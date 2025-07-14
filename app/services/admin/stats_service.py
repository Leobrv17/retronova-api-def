from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.models import User, Arcade, Game, PromoCode


class StatsService:
    def __init__(self, db: Session):
        self.db = db

    async def get_global_stats(self) -> dict:
        """Récupère les statistiques globales de la plateforme."""
        return {
            "active_users": self._count_active_users(),
            "total_arcades": self._count_active_arcades(),
            "total_games": self._count_active_games(),
            "active_promo_codes": self._count_active_promo_codes(),
            "total_tickets_in_circulation": self._count_total_tickets(),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _count_active_users(self) -> int:
        """Compte les utilisateurs actifs."""
        return self.db.query(User).filter(User.is_deleted == False).count()

    def _count_active_arcades(self) -> int:
        """Compte les bornes actives."""
        return self.db.query(Arcade).filter(Arcade.is_deleted == False).count()

    def _count_active_games(self) -> int:
        """Compte les jeux actifs."""
        return self.db.query(Game).filter(Game.is_deleted == False).count()

    def _count_active_promo_codes(self) -> int:
        """Compte les codes promo actifs."""
        return self.db.query(PromoCode).filter(PromoCode.is_deleted == False).count()

    def _count_total_tickets(self) -> int:
        """Compte le total de tickets en circulation."""
        result = self.db.query(func.sum(User.tickets_balance)).filter(
            User.is_deleted == False
        ).scalar()
        return result or 0