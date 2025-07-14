from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Dict, Any

from app.models import (
    User, Reservation, ReservationStatus, Friendship,
    PromoUse, TicketPurchase, Score
)
from app.schemas.admin.user import UpdateUserTicketsRequest
from app.utils.exceptions import AdminException
from app.utils.admin_utils import generate_success_message


class UserService:
    def __init__(self, db: Session):
        self.db = db

    async def update_user_tickets(self, update_data: UpdateUserTicketsRequest) -> dict:
        """Met à jour le solde de tickets d'un utilisateur."""
        user = self._get_user_by_id(update_data.user_id)

        old_balance = user.tickets_balance
        new_balance = max(0, old_balance + update_data.tickets_to_add)
        user.tickets_balance = new_balance

        self.db.commit()

        return {
            "message": generate_success_message("mis à jour", "Solde", user.pseudo),
            "old_balance": old_balance,
            "new_balance": new_balance,
            "tickets_added": update_data.tickets_to_add
        }

    async def list_deleted_users(self) -> List[User]:
        """Liste les utilisateurs supprimés."""
        return self.db.query(User).filter(User.is_deleted == True).all()

    async def restore_user(self, user_id: int) -> dict:
        """Restaure un utilisateur supprimé."""
        user = self._get_user_by_id_including_deleted(user_id)
        self._validate_user_for_restoration(user)

        user.is_deleted = False
        user.deleted_at = None
        self.db.commit()

        return {
            "message": generate_success_message("restauré", "Utilisateur", user.pseudo)
        }

    async def soft_delete_user(self, user_id: int) -> dict:
        """Supprime un utilisateur (soft delete)."""
        user = self._get_user_by_id(user_id)
        self._check_no_active_reservations_for_user(user_id)

        deletion_stats = self._perform_user_soft_delete(user)
        self.db.commit()

        return {
            "message": generate_success_message("supprimé", "Utilisateur", user.pseudo),
            "user_id": user.id,
            **deletion_stats,
            "note": "Les scores sont conservés de manière anonymisée pour l'intégrité des données de jeu"
        }

    async def get_user_deletion_impact(self, user_id: int) -> dict:
        """Analyse l'impact de la suppression d'un utilisateur."""
        user = self._get_user_by_id(user_id)

        # Facteurs bloquants
        active_reservations = self._count_active_reservations(user_id)
        can_delete = active_reservations == 0

        # Impact de suppression
        deletion_impact = self._calculate_deletion_impact(user_id)

        # Recommandations
        recommendations = self._generate_recommendations(can_delete)

        result = {
            "user": self._format_user_summary(user),
            "can_delete": can_delete,
            "deletion_impact": deletion_impact,
            "recommendations": recommendations
        }

        if not can_delete:
            result["blocking_factors"] = {"active_reservations": active_reservations}

        return result

    async def force_cancel_user_reservations(self, user_id: int) -> dict:
        """Force l'annulation des réservations actives d'un utilisateur."""
        user = self._get_user_by_id(user_id)

        active_reservations = self._get_active_reservations(user_id)
        cancelled_count = 0
        refunded_tickets = 0

        for reservation in active_reservations:
            if self._should_refund_tickets(reservation, user_id):
                user.tickets_balance += reservation.tickets_used
                refunded_tickets += reservation.tickets_used

            reservation.status = ReservationStatus.CANCELLED
            cancelled_count += 1

        self.db.commit()

        return {
            "message": f"Réservations de l'utilisateur '{user.pseudo}' annulées",
            "user_id": user.id,
            "cancelled_reservations": cancelled_count,
            "refunded_tickets": refunded_tickets,
            "new_tickets_balance": user.tickets_balance
        }

    # Méthodes privées
    def _get_user_by_id(self, user_id: int) -> User:
        """Récupère un utilisateur actif par ID."""
        user = self.db.query(User).filter(
            User.id == user_id,
            User.is_deleted == False
        ).first()

        if not user:
            raise AdminException("Utilisateur non trouvé", 404)
        return user

    def _get_user_by_id_including_deleted(self, user_id: int) -> User:
        """Récupère un utilisateur par ID (incluant supprimés)."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise AdminException("Utilisateur non trouvé", 404)
        return user

    def _validate_user_for_restoration(self, user: User):
        """Valide qu'un utilisateur peut être restauré."""
        if not user.is_deleted:
            raise AdminException("Cet utilisateur n'est pas supprimé", 400)

    def _check_no_active_reservations_for_user(self, user_id: int):
        """Vérifie qu'il n'y a pas de réservations actives."""
        active_count = self._count_active_reservations(user_id)

        if active_count > 0:
            raise AdminException(
                f"Impossible de supprimer l'utilisateur : {active_count} réservation(s) active(s). "
                "Veuillez d'abord gérer les réservations en cours.",
                400
            )

    def _count_active_reservations(self, user_id: int) -> int:
        """Compte les réservations actives d'un utilisateur."""
        return self.db.query(Reservation).filter(
            (Reservation.player_id == user_id) | (Reservation.player2_id == user_id),
            Reservation.status.in_([ReservationStatus.WAITING, ReservationStatus.PLAYING]),
            Reservation.is_deleted == False
        ).count()

    def _perform_user_soft_delete(self, user: User) -> dict:
        """Effectue la suppression soft de l'utilisateur et ses données."""
        now = datetime.now(timezone.utc)

        # Marquer l'utilisateur comme supprimé
        user.is_deleted = True
        user.deleted_at = now

        # Supprimer les relations d'amitié
        deleted_friendships = self._soft_delete_user_friendships(user.id, now)

        # Supprimer les codes promo utilisés
        deleted_promo_uses = self._soft_delete_user_promo_uses(user.id, now)

        # Supprimer les achats de tickets
        deleted_purchases = self._soft_delete_user_purchases(user.id, now)

        return {
            "deleted_friendships": deleted_friendships,
            "deleted_promo_uses": deleted_promo_uses,
            "deleted_purchases": deleted_purchases
        }

    def _soft_delete_user_friendships(self, user_id: int, timestamp: datetime) -> int:
        """Supprime les amitiés d'un utilisateur."""
        friendships = self.db.query(Friendship).filter(
            (Friendship.requester_id == user_id) | (Friendship.requested_id == user_id),
            Friendship.is_deleted == False
        ).all()

        for friendship in friendships:
            friendship.is_deleted = True
            friendship.deleted_at = timestamp

        return len(friendships)

    def _soft_delete_user_promo_uses(self, user_id: int, timestamp: datetime) -> int:
        """Supprime les utilisations de codes promo."""
        promo_uses = self.db.query(PromoUse).filter(
            PromoUse.user_id == user_id,
            PromoUse.is_deleted == False
        ).all()

        for promo_use in promo_uses:
            promo_use.is_deleted = True
            promo_use.deleted_at = timestamp

        return len(promo_uses)

    def _soft_delete_user_purchases(self, user_id: int, timestamp: datetime) -> int:
        """Supprime les achats de tickets."""
        purchases = self.db.query(TicketPurchase).filter(
            TicketPurchase.user_id == user_id,
            TicketPurchase.is_deleted == False
        ).all()

        for purchase in purchases:
            purchase.is_deleted = True
            purchase.deleted_at = timestamp

        return len(purchases)

    def _calculate_deletion_impact(self, user_id: int) -> dict:
        """Calcule l'impact de la suppression."""
        friendships_count = self.db.query(Friendship).filter(
            (Friendship.requester_id == user_id) | (Friendship.requested_id == user_id),
            Friendship.is_deleted == False
        ).count()

        promo_uses_count = self.db.query(PromoUse).filter(
            PromoUse.user_id == user_id,
            PromoUse.is_deleted == False
        ).count()

        purchases_count = self.db.query(TicketPurchase).filter(
            TicketPurchase.user_id == user_id,
            TicketPurchase.is_deleted == False
        ).count()

        completed_reservations = self.db.query(Reservation).filter(
            (Reservation.player_id == user_id) | (Reservation.player2_id == user_id),
            Reservation.status.in_([ReservationStatus.COMPLETED, ReservationStatus.CANCELLED]),
            Reservation.is_deleted == False
        ).count()

        scores_count = self._count_user_scores(user_id)

        return {
            "friendships_to_delete": friendships_count,
            "promo_uses_to_delete": promo_uses_count,
            "purchases_to_delete": purchases_count,
            "completed_reservations_preserved": completed_reservations,
            "scores_anonymized": scores_count
        }

    def _count_user_scores(self, user_id: int) -> int:
        """Compte les scores d'un utilisateur."""
        scores_as_player1 = self.db.query(Score).filter(
            Score.player1_id == user_id,
            Score.is_deleted == False
        ).count()

        scores_as_player2 = self.db.query(Score).filter(
            Score.player2_id == user_id,
            Score.is_deleted == False
        ).count()

        return scores_as_player1 + scores_as_player2

    def _generate_recommendations(self, can_delete: bool) -> List[str]:
        """Génère des recommandations pour la suppression."""
        base_recommendations = [
            "Les scores seront conservés de manière anonymisée pour préserver l'intégrité des classements",
            "Les réservations terminées seront préservées pour l'historique",
            "Les données personnelles seront marquées comme supprimées conformément au RGPD"
        ]

        if not can_delete:
            base_recommendations.append(
                "⚠️ Annulez d'abord les réservations actives avant la suppression"
            )

        return base_recommendations

    def _format_user_summary(self, user: User) -> dict:
        """Formate un résumé utilisateur."""
        return {
            "id": user.id,
            "pseudo": user.pseudo,
            "email": user.email,
            "tickets_balance": user.tickets_balance,
            "created_at": user.created_at.isoformat()
        }

    def _get_active_reservations(self, user_id: int) -> List[Reservation]:
        """Récupère les réservations actives d'un utilisateur."""
        return self.db.query(Reservation).filter(
            (Reservation.player_id == user_id) | (Reservation.player2_id == user_id),
            Reservation.status.in_([ReservationStatus.WAITING, ReservationStatus.PLAYING]),
            Reservation.is_deleted == False
        ).all()

    def _should_refund_tickets(self, reservation: Reservation, user_id: int) -> bool:
        """Détermine si les tickets doivent être remboursés."""
        return reservation.player_id == user_id