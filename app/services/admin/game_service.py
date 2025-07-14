# app/services/admin/game_service.py

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from app.models import Game, ArcadeGame, Arcade, Reservation, Score, ReservationStatus
from app.schemas.admin.game import CreateGameRequest, UpdateGameRequest
from app.utils.exceptions import AdminException
from app.utils.admin_utils import generate_success_message, validate_game_players


class GameService:
    def __init__(self, db: Session):
        self.db = db

    async def create_game(self, game_data: CreateGameRequest) -> dict:
        """Crée un nouveau jeu."""
        self._validate_game_data(game_data)
        self._check_game_name_uniqueness(game_data.nom)

        game = Game(
            nom=game_data.nom,
            description=game_data.description,
            min_players=game_data.min_players,
            max_players=game_data.max_players,
            ticket_cost=game_data.ticket_cost
        )

        self.db.add(game)
        self.db.commit()
        self.db.refresh(game)

        return {
            "message": generate_success_message("créé", "Jeu", game.nom),
            "game_id": game.id,
            "game_details": self._format_game_response(game)
        }

    async def list_games(self, include_deleted: bool = False) -> List[dict]:
        """Liste tous les jeux."""
        query = self.db.query(Game)

        if not include_deleted:
            query = query.filter(Game.is_deleted == False)

        games = query.order_by(Game.created_at.desc()).all()
        return [self._format_game_response(game) for game in games]

    async def get_game_by_id(self, game_id: int) -> dict:
        """Récupère un jeu par ID."""
        game = self._get_game_by_id(game_id)
        return self._format_game_response(game)

    async def update_game(self, game_id: int, update_data: UpdateGameRequest) -> dict:
        """Met à jour un jeu."""
        game = self._get_game_by_id(game_id)

        # Valider les nouvelles données
        if update_data.min_players and update_data.max_players:
            validate_game_players(update_data.min_players, update_data.max_players)

        # Vérifier l'unicité du nom si modifié
        if update_data.nom and update_data.nom != game.nom:
            self._check_game_name_uniqueness(update_data.nom, exclude_id=game_id)

        # Appliquer les modifications
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(game, field, value)

        self.db.commit()
        self.db.refresh(game)

        return {
            "message": generate_success_message("mis à jour", "Jeu", game.nom),
            "game_id": game.id,
            "updated_fields": list(update_dict.keys()),
            "game_details": self._format_game_response(game)
        }

    async def soft_delete_game(self, game_id: int) -> dict:
        """Supprime un jeu (soft delete)."""
        game = self._get_game_by_id(game_id)
        self._check_game_can_be_deleted(game_id)

        game.is_deleted = True
        game.deleted_at = datetime.now(timezone.utc)

        # Supprimer les associations avec les bornes
        deleted_associations = self._soft_delete_game_associations(game_id)

        self.db.commit()

        return {
            "message": generate_success_message("supprimé", "Jeu", game.nom),
            "game_id": game.id,
            "deleted_arcade_associations": deleted_associations,
            "note": "Les scores et réservations historiques sont préservés"
        }

    async def list_deleted_games(self) -> List[dict]:
        """Liste les jeux supprimés."""
        deleted_games = self.db.query(Game).filter(
            Game.is_deleted == True
        ).order_by(Game.deleted_at.desc()).all()

        return [self._format_game_response(game) for game in deleted_games]

    async def restore_game(self, game_id: int) -> dict:
        """Restaure un jeu supprimé."""
        game = self._get_game_by_id_including_deleted(game_id)
        self._validate_game_for_restoration(game)

        game.is_deleted = False
        game.deleted_at = None

        # Note: Les associations arcade-jeu ne sont pas automatiquement restaurées
        # pour éviter les conflits. L'admin devra les reconfigurer manuellement.

        self.db.commit()

        return {
            "message": generate_success_message("restauré", "Jeu", game.nom),
            "game_id": game.id,
            "note": "Les associations avec les bornes doivent être reconfigurées manuellement"
        }

    async def get_game_stats(self, game_id: int, days: int = 30) -> dict:
        """Récupère les statistiques d'un jeu."""
        game = self._get_game_by_id(game_id)
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Statistiques des réservations
        reservation_stats = self._calculate_reservation_stats(game_id, start_date)

        # Statistiques des scores
        score_stats = self._calculate_score_stats(game_id, start_date)

        # Revenus générés
        revenue_stats = self._calculate_revenue_stats(game_id, start_date)

        # Popularité par borne
        arcade_popularity = self._calculate_arcade_popularity(game_id, start_date)

        return {
            "game_id": game.id,
            "game_name": game.nom,
            "period_days": days,
            "reservation_stats": reservation_stats,
            "score_stats": score_stats,
            "revenue_stats": revenue_stats,
            "arcade_popularity": arcade_popularity,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    async def get_game_arcades(self, game_id: int) -> List[dict]:
        """Liste les bornes où ce jeu est disponible."""
        game = self._get_game_by_id(game_id)

        arcade_games = self.db.query(ArcadeGame, Arcade).join(
            Arcade, ArcadeGame.arcade_id == Arcade.id
        ).filter(
            ArcadeGame.game_id == game_id,
            ArcadeGame.is_deleted == False,
            Arcade.is_deleted == False
        ).all()

        result = []
        for arcade_game, arcade in arcade_games:
            result.append({
                "arcade_id": arcade.id,
                "arcade_name": arcade.nom,
                "arcade_location": arcade.localisation,
                "slot_number": arcade_game.slot_number,
                "assigned_at": arcade_game.created_at.isoformat()
            })

        return result

    async def toggle_game_active(self, game_id: int) -> dict:
        """Active/désactive un jeu."""
        game = self._get_game_by_id(game_id)

        # Pour cette demo, on utilise un champ virtuel "is_active"
        # En réalité, on pourrait ajouter ce champ au modèle
        # Pour l'instant, on simule avec is_deleted

        if game.is_deleted:
            raise AdminException("Impossible d'activer un jeu supprimé", 400)

        # Simuler l'activation/désactivation
        # Dans un vrai cas, on aurait un champ is_active
        message = f"Jeu '{game.nom}' est maintenant actif"

        return {
            "message": message,
            "game_id": game.id,
            "is_active": True,  # Simulé
            "note": "Fonctionnalité d'activation/désactivation à implémenter"
        }

    # Méthodes privées
    def _validate_game_data(self, game_data: CreateGameRequest):
        """Valide les données d'un jeu."""
        validate_game_players(game_data.min_players, game_data.max_players)

        if game_data.ticket_cost < 0:
            raise AdminException("Le coût en tickets ne peut pas être négatif", 400)

        if len(game_data.nom.strip()) < 2:
            raise AdminException("Le nom du jeu doit contenir au moins 2 caractères", 400)

    def _check_game_name_uniqueness(self, nom: str, exclude_id: int = None):
        """Vérifie l'unicité du nom d'un jeu."""
        query = self.db.query(Game).filter(
            Game.nom.ilike(nom.strip()),
            Game.is_deleted == False
        )

        if exclude_id:
            query = query.filter(Game.id != exclude_id)

        existing = query.first()
        if existing:
            raise AdminException(f"Un jeu avec le nom '{nom}' existe déjà", 400)

    def _get_game_by_id(self, game_id: int) -> Game:
        """Récupère un jeu actif par ID."""
        game = self.db.query(Game).filter(
            Game.id == game_id,
            Game.is_deleted == False
        ).first()

        if not game:
            raise AdminException("Jeu non trouvé", 404)
        return game

    def _get_game_by_id_including_deleted(self, game_id: int) -> Game:
        """Récupère un jeu par ID (incluant supprimés)."""
        game = self.db.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise AdminException("Jeu non trouvé", 404)
        return game

    def _check_game_can_be_deleted(self, game_id: int):
        """Vérifie qu'un jeu peut être supprimé."""
        # Vérifier s'il y a des réservations actives
        active_reservations = self.db.query(Reservation).filter(
            Reservation.game_id == game_id,
            Reservation.status.in_([ReservationStatus.WAITING, ReservationStatus.PLAYING]),
            Reservation.is_deleted == False
        ).count()

        if active_reservations > 0:
            raise AdminException(
                f"Impossible de supprimer le jeu : {active_reservations} réservation(s) active(s)",
                400
            )

    def _soft_delete_game_associations(self, game_id: int) -> int:
        """Supprime les associations jeu-arcade."""
        arcade_games = self.db.query(ArcadeGame).filter(
            ArcadeGame.game_id == game_id,
            ArcadeGame.is_deleted == False
        ).all()

        for ag in arcade_games:
            ag.is_deleted = True
            ag.deleted_at = datetime.now(timezone.utc)

        return len(arcade_games)

    def _validate_game_for_restoration(self, game: Game):
        """Valide qu'un jeu peut être restauré."""
        if not game.is_deleted:
            raise AdminException("Ce jeu n'est pas supprimé", 400)

    def _format_game_response(self, game: Game) -> dict:
        """Formate une réponse de jeu."""
        return {
            "id": game.id,
            "nom": game.nom,
            "description": game.description,
            "min_players": game.min_players,
            "max_players": game.max_players,
            "ticket_cost": game.ticket_cost,
            "is_deleted": game.is_deleted,
            "created_at": game.created_at.isoformat(),
            "updated_at": game.updated_at.isoformat(),
            "deleted_at": game.deleted_at.isoformat() if game.deleted_at else None
        }

    def _calculate_reservation_stats(self, game_id: int, start_date: datetime) -> dict:
        """Calcule les statistiques de réservation."""
        total_reservations = self.db.query(Reservation).filter(
            Reservation.game_id == game_id,
            Reservation.created_at >= start_date,
            Reservation.is_deleted == False
        ).count()

        completed_reservations = self.db.query(Reservation).filter(
            Reservation.game_id == game_id,
            Reservation.status == ReservationStatus.COMPLETED,
            Reservation.created_at >= start_date,
            Reservation.is_deleted == False
        ).count()

        return {
            "total_reservations": total_reservations,
            "completed_reservations": completed_reservations,
            "completion_rate": round((completed_reservations / max(total_reservations, 1)) * 100, 2)
        }

    def _calculate_score_stats(self, game_id: int, start_date: datetime) -> dict:
        """Calcule les statistiques de scores."""
        total_games_played = self.db.query(Score).filter(
            Score.game_id == game_id,
            Score.created_at >= start_date,
            Score.is_deleted == False
        ).count()

        avg_score_j1 = self.db.query(func.avg(Score.score_j1)).filter(
            Score.game_id == game_id,
            Score.created_at >= start_date,
            Score.is_deleted == False
        ).scalar() or 0

        avg_score_j2 = self.db.query(func.avg(Score.score_j2)).filter(
            Score.game_id == game_id,
            Score.score_j2.isnot(None),
            Score.created_at >= start_date,
            Score.is_deleted == False
        ).scalar() or 0

        return {
            "total_games_played": total_games_played,
            "average_score_player1": round(avg_score_j1, 2),
            "average_score_player2": round(avg_score_j2, 2)
        }

    def _calculate_revenue_stats(self, game_id: int, start_date: datetime) -> dict:
        """Calcule les statistiques de revenus."""
        game = self._get_game_by_id_including_deleted(game_id)

        total_tickets_spent = self.db.query(func.sum(Reservation.tickets_used)).filter(
            Reservation.game_id == game_id,
            Reservation.created_at >= start_date,
            Reservation.is_deleted == False
        ).scalar() or 0

        total_reservations = self.db.query(Reservation).filter(
            Reservation.game_id == game_id,
            Reservation.created_at >= start_date,
            Reservation.is_deleted == False
        ).count()

        return {
            "total_tickets_spent": total_tickets_spent,
            "total_reservations": total_reservations,
            "tickets_per_game": game.ticket_cost,
            "estimated_revenue_euros": total_tickets_spent * 1.0  # Approximation 1 ticket = 1€
        }

    def _calculate_arcade_popularity(self, game_id: int, start_date: datetime) -> List[dict]:
        """Calcule la popularité par borne."""
        popularity = self.db.query(
            Arcade.id,
            Arcade.nom,
            func.count(Reservation.id).label('total_reservations')
        ).join(
            Reservation, Arcade.id == Reservation.arcade_id
        ).filter(
            Reservation.game_id == game_id,
            Reservation.created_at >= start_date,
            Reservation.is_deleted == False,
            Arcade.is_deleted == False
        ).group_by(
            Arcade.id, Arcade.nom
        ).order_by(
            func.count(Reservation.id).desc()
        ).all()

        return [
            {
                "arcade_id": arcade_id,
                "arcade_name": arcade_name,
                "total_reservations": total_reservations
            }
            for arcade_id, arcade_name, total_reservations in popularity
        ]