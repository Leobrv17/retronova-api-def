from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
from typing import List
import secrets

from app.models import Arcade, ArcadeGame, Game, Reservation, ReservationStatus
from app.schemas.admin.arcade import CreateArcadeRequest, ArcadeGameAssignmentRequest
from app.utils.exceptions import AdminException
from app.utils.admin_utils import validate_slot_number


class ArcadeService:
    def __init__(self, db: Session):
        self.db = db

    async def create_arcade(self, arcade_data: CreateArcadeRequest) -> dict:
        """Crée une nouvelle borne d'arcade."""
        api_key = self._generate_unique_api_key()

        arcade = Arcade(
            nom=arcade_data.nom,
            description=arcade_data.description,
            api_key=api_key,
            localisation=arcade_data.localisation,
            latitude=arcade_data.latitude,
            longitude=arcade_data.longitude
        )

        self.db.add(arcade)
        self.db.commit()
        self.db.refresh(arcade)

        return {
            "message": "Borne créée avec succès",
            "arcade_id": arcade.id,
            "api_key": api_key
        }

    async def assign_game_to_arcade(
            self,
            arcade_id: int,
            assignment: ArcadeGameAssignmentRequest
    ) -> dict:
        """Assigne un jeu à une borne."""
        arcade = self._get_arcade_by_id(arcade_id)
        game = self._get_game_by_id(assignment.game_id)

        validate_slot_number(assignment.slot_number)
        self._remove_existing_game_from_slot(arcade_id, assignment.slot_number)

        arcade_game = ArcadeGame(
            arcade_id=arcade_id,
            game_id=assignment.game_id,
            slot_number=assignment.slot_number
        )

        self.db.add(arcade_game)
        self.db.commit()

        return {
            "message": f"Jeu {game.nom} assigné au slot {assignment.slot_number} "
                       f"de la borne {arcade.nom}"
        }

    async def soft_delete_arcade(self, arcade_id: int) -> dict:
        """Supprime une borne (soft delete)."""
        arcade = self._get_arcade_by_id(arcade_id)
        self._check_no_active_reservations(arcade_id)

        arcade.is_deleted = True
        arcade.deleted_at = datetime.now(timezone.utc)

        deleted_associations = self._soft_delete_arcade_games(arcade_id)
        self.db.commit()

        return {
            "message": f"Borne '{arcade.nom}' supprimée avec succès",
            "arcade_id": arcade.id,
            "deleted_associations": deleted_associations
        }

    async def list_deleted_arcades(self) -> List[Arcade]:
        """Liste les bornes supprimées."""
        return self.db.query(Arcade).filter(
            Arcade.is_deleted == True
        ).order_by(Arcade.deleted_at.desc()).all()

    async def restore_arcade(self, arcade_id: int) -> dict:
        """Restaure une borne supprimée."""
        arcade = self._get_arcade_by_id_including_deleted(arcade_id)
        self._validate_arcade_for_restoration(arcade)

        arcade.is_deleted = False
        arcade.deleted_at = None

        restored_associations = self._restore_arcade_games(arcade_id)
        self.db.commit()

        return {
            "message": f"Borne '{arcade.nom}' restaurée avec succès",
            "arcade_id": arcade.id,
            "restored_associations": restored_associations
        }

    async def regenerate_api_key(self, arcade_id: int) -> dict:
        """Régénère la clé API d'une borne."""
        arcade = self._get_arcade_by_id_including_deleted(arcade_id)

        old_api_key = arcade.api_key
        new_api_key = self._generate_unique_api_key()

        arcade.api_key = new_api_key
        self.db.commit()

        return {
            "message": f"Clé API de la borne '{arcade.nom}' régénérée",
            "arcade_id": arcade.id,
            "old_api_key": old_api_key[:20] + "...",
            "new_api_key": new_api_key
        }

    # Méthodes privées
    def _generate_unique_api_key(self) -> str:
        """Génère une clé API unique."""
        while True:
            api_key = f"arcade_key_{secrets.token_urlsafe(16)}"
            if not self._api_key_exists(api_key):
                return api_key

    def _api_key_exists(self, api_key: str) -> bool:
        """Vérifie si une clé API existe déjà."""
        return self.db.query(Arcade).filter(
            Arcade.api_key == api_key
        ).first() is not None

    def _get_arcade_by_id(self, arcade_id: int) -> Arcade:
        """Récupère une borne active par ID."""
        arcade = self.db.query(Arcade).filter(
            Arcade.id == arcade_id,
            Arcade.is_deleted == False
        ).first()

        if not arcade:
            raise AdminException("Borne d'arcade non trouvée", 404)
        return arcade

    def _get_arcade_by_id_including_deleted(self, arcade_id: int) -> Arcade:
        """Récupère une borne par ID (incluant supprimées)."""
        arcade = self.db.query(Arcade).filter(Arcade.id == arcade_id).first()
        if not arcade:
            raise AdminException("Borne d'arcade non trouvée", 404)
        return arcade

    def _get_game_by_id(self, game_id: int) -> Game:
        """Récupère un jeu par ID."""
        game = self.db.query(Game).filter(
            Game.id == game_id,
            Game.is_deleted == False
        ).first()

        if not game:
            raise AdminException("Jeu non trouvé", 404)
        return game

    def _remove_existing_game_from_slot(self, arcade_id: int, slot_number: int):
        """Supprime le jeu existant d'un slot."""
        existing = self.db.query(ArcadeGame).filter(
            ArcadeGame.arcade_id == arcade_id,
            ArcadeGame.slot_number == slot_number
        ).first()

        if existing:
            self.db.delete(existing)

    def _check_no_active_reservations(self, arcade_id: int):
        """Vérifie qu'il n'y a pas de réservations actives."""
        active_count = self.db.query(Reservation).filter(
            Reservation.arcade_id == arcade_id,
            Reservation.status.in_([ReservationStatus.WAITING, ReservationStatus.PLAYING]),
            Reservation.is_deleted == False
        ).count()

        if active_count > 0:
            raise AdminException(
                f"Impossible de supprimer la borne : {active_count} réservation(s) active(s)",
                400
            )

    def _soft_delete_arcade_games(self, arcade_id: int) -> int:
        """Supprime les associations arcade-jeux."""
        arcade_games = self.db.query(ArcadeGame).filter(
            ArcadeGame.arcade_id == arcade_id,
            ArcadeGame.is_deleted == False
        ).all()

        for ag in arcade_games:
            ag.is_deleted = True
            ag.deleted_at = datetime.now(timezone.utc)

        return len(arcade_games)

    def _validate_arcade_for_restoration(self, arcade: Arcade):
        """Valide qu'une borne peut être restaurée."""
        if not arcade.is_deleted:
            raise AdminException("Cette borne n'est pas supprimée", 400)

        # Vérifier l'unicité de la clé API
        existing_api_key = self.db.query(Arcade).filter(
            Arcade.api_key == arcade.api_key,
            Arcade.is_deleted == False,
            Arcade.id != arcade.id
        ).first()

        if existing_api_key:
            raise AdminException(
                "La clé API de cette borne est maintenant utilisée par une autre borne. "
                "Veuillez générer une nouvelle clé API.",
                400
            )

    def _restore_arcade_games(self, arcade_id: int) -> int:
        """Restaure les associations arcade-jeux."""
        arcade_games = self.db.query(ArcadeGame).filter(
            ArcadeGame.arcade_id == arcade_id,
            ArcadeGame.is_deleted == True
        ).all()

        restored_count = 0
        for ag in arcade_games:
            if self._can_restore_arcade_game(ag):
                ag.is_deleted = False
                ag.deleted_at = None
                restored_count += 1

        return restored_count

    def _can_restore_arcade_game(self, arcade_game: ArcadeGame) -> bool:
        """Vérifie si une association peut être restaurée."""
        # Vérifier que le jeu existe toujours
        game_exists = self.db.query(Game).filter(
            Game.id == arcade_game.game_id,
            Game.is_deleted == False
        ).first()

        if not game_exists:
            return False

        # Vérifier qu'il n'y a pas de conflit de slot
        slot_conflict = self.db.query(ArcadeGame).filter(
            ArcadeGame.arcade_id == arcade_game.arcade_id,
            ArcadeGame.slot_number == arcade_game.slot_number,
            ArcadeGame.is_deleted == False,
            ArcadeGame.id != arcade_game.id
        ).first()

        return slot_conflict is None