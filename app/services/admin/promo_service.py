from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List

from app.models import PromoCode
from app.schemas.admin.promo import CreatePromoCodeRequest, UpdatePromoCodeRequest
from app.utils.exceptions import AdminException
from app.utils.admin_utils import validate_promo_dates


class PromoService:
    def __init__(self, db: Session):
        self.db = db

    async def create_promo_code(self, promo_data: CreatePromoCodeRequest) -> dict:
        """Crée un nouveau code promo."""
        validate_promo_dates(promo_data.valid_from, promo_data.valid_until)
        self._check_code_uniqueness(promo_data.code)

        promo_code = PromoCode(
            code=promo_data.code.upper().strip(),
            tickets_reward=promo_data.tickets_reward,
            is_single_use_global=promo_data.is_single_use_global,
            is_single_use_per_user=promo_data.is_single_use_per_user,
            usage_limit=promo_data.usage_limit,
            valid_from=promo_data.valid_from,
            valid_until=promo_data.valid_until,
            is_active=promo_data.is_active
        )

        self.db.add(promo_code)
        self.db.commit()
        self.db.refresh(promo_code)

        return {
            "message": "Code promo créé avec succès",
            "promo_code_id": promo_code.id,
            "is_valid_now": promo_code.is_valid_now(),
            "days_until_expiry": promo_code.days_until_expiry()
        }

    async def list_promo_codes(self, include_expired: bool = False) -> List[dict]:
        """Liste tous les codes promo."""
        query = self.db.query(PromoCode).filter(PromoCode.is_deleted == False)

        if not include_expired:
            query = self._filter_non_expired(query)

        promo_codes = query.order_by(PromoCode.created_at.desc()).all()
        return [self._format_promo_code_response(promo) for promo in promo_codes]

    async def update_promo_code(
            self,
            promo_code_id: int,
            update_data: UpdatePromoCodeRequest
    ) -> dict:
        """Met à jour un code promo."""
        promo_code = self._get_promo_code_by_id(promo_code_id)

        # Validation des dates si elles sont modifiées
        valid_from = update_data.valid_from or promo_code.valid_from
        valid_until = update_data.valid_until or promo_code.valid_until
        validate_promo_dates(valid_from, valid_until)

        # Appliquer les modifications
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(promo_code, field, value)

        self.db.commit()
        self.db.refresh(promo_code)

        return {
            "message": "Code promo mis à jour avec succès",
            "promo_code_id": promo_code.id,
            "is_valid_now": promo_code.is_valid_now(),
            "days_until_expiry": promo_code.days_until_expiry()
        }

    async def toggle_promo_code_active(self, promo_code_id: int) -> dict:
        """Active/désactive un code promo."""
        promo_code = self._get_promo_code_by_id(promo_code_id)

        promo_code.is_active = not promo_code.is_active
        self.db.commit()

        status = "activé" if promo_code.is_active else "désactivé"
        return {
            "message": f"Code promo {status} avec succès",
            "promo_code_id": promo_code.id,
            "is_active": promo_code.is_active,
            "is_valid_now": promo_code.is_valid_now()
        }

    async def get_expiring_promo_codes(self, days_ahead: int) -> dict:
        """Récupère les codes promo expirant bientôt."""
        now = datetime.now(timezone.utc)
        future_date = now + timedelta(days=days_ahead)

        expiring_codes = self.db.query(PromoCode).filter(
            PromoCode.is_deleted == False,
            PromoCode.is_active == True,
            PromoCode.valid_until.isnot(None),
            PromoCode.valid_until <= future_date,
            PromoCode.valid_until > now
        ).order_by(PromoCode.valid_until).all()

        formatted_codes = [
            self._format_expiring_code(promo) for promo in expiring_codes
        ]

        return {
            "expiring_codes": formatted_codes,
            "total_count": len(formatted_codes),
            "days_ahead": days_ahead
        }

    # Méthodes privées
    def _check_code_uniqueness(self, code: str):
        """Vérifie l'unicité d'un code promo."""
        existing = self.db.query(PromoCode).filter(
            PromoCode.code == code.upper().strip()
        ).first()

        if existing:
            raise AdminException("Ce code promo existe déjà", 400)

    def _get_promo_code_by_id(self, promo_code_id: int) -> PromoCode:
        """Récupère un code promo par ID."""
        promo_code = self.db.query(PromoCode).filter(
            PromoCode.id == promo_code_id,
            PromoCode.is_deleted == False
        ).first()

        if not promo_code:
            raise AdminException("Code promo non trouvé", 404)
        return promo_code

    def _filter_non_expired(self, query):
        """Filtre les codes non expirés."""
        now = datetime.now(timezone.utc)
        return query.filter(
            (PromoCode.valid_until.is_(None) | (PromoCode.valid_until > now))
        )

    def _format_promo_code_response(self, promo: PromoCode) -> dict:
        """Formate une réponse de code promo."""
        return {
            "id": promo.id,
            "code": promo.code,
            "tickets_reward": promo.tickets_reward,
            "usage_limit": promo.usage_limit,
            "current_uses": promo.current_uses,
            "is_single_use_global": promo.is_single_use_global,
            "is_single_use_per_user": promo.is_single_use_per_user,
            "valid_from": promo.valid_from.isoformat() if promo.valid_from else None,
            "valid_until": promo.valid_until.isoformat() if promo.valid_until else None,
            "is_active": promo.is_active,
            "is_valid_now": promo.is_valid_now(),
            "is_expired": promo.is_expired(),
            "days_until_expiry": promo.days_until_expiry(),
            "created_at": promo.created_at.isoformat()
        }

    def _format_expiring_code(self, promo: PromoCode) -> dict:
        """Formate un code promo expirant."""
        return {
            "id": promo.id,
            "code": promo.code,
            "tickets_reward": promo.tickets_reward,
            "valid_until": promo.valid_until.isoformat(),
            "days_until_expiry": promo.days_until_expiry(),
            "current_uses": promo.current_uses,
            "usage_limit": promo.usage_limit
        }