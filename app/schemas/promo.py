from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional


class PromoCodeCreate(BaseModel):
    """Schéma pour la création d'un code promo."""
    code: str
    tickets_reward: int
    is_single_use_global: bool = False
    is_single_use_per_user: bool = True
    usage_limit: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool = True

    @validator('valid_until')
    def validate_expiry_after_start(cls, v, values):
        """Valide que la date d'expiration est après la date de début."""
        if v and 'valid_from' in values and values['valid_from']:
            if v <= values['valid_from']:
                raise ValueError('La date d\'expiration doit être après la date de début')
        return v

    @validator('valid_from')
    def validate_start_date_not_past(cls, v):
        """Valide que la date de début n'est pas dans le passé (optionnel)."""
        if v and v < datetime.now():
            # Avertissement mais on accepte (pour les codes rétroactifs)
            pass
        return v

    @validator('tickets_reward')
    def validate_positive_reward(cls, v):
        """Valide que la récompense est positive."""
        if v <= 0:
            raise ValueError('La récompense doit être positive')
        return v


class PromoCodeResponse(BaseModel):
    """Schéma de réponse pour un code promo."""
    id: int
    code: str
    tickets_reward: int
    is_single_use_global: bool
    is_single_use_per_user: bool
    usage_limit: Optional[int]
    current_uses: int
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    is_active: bool
    is_expired: bool
    days_until_expiry: int
    created_at: datetime

    class Config:
        from_attributes = True

    @validator('is_expired', pre=False, always=True)
    def set_is_expired(cls, v, values):
        """Calcule si le code est expiré."""
        if 'valid_until' in values and values['valid_until']:
            return datetime.now() > values['valid_until']
        return False

    @validator('days_until_expiry', pre=False, always=True)
    def set_days_until_expiry(cls, v, values):
        """Calcule les jours avant expiration."""
        if 'valid_until' in values and values['valid_until']:
            now = datetime.now()
            if now > values['valid_until']:
                return 0
            delta = values['valid_until'] - now
            return delta.days
        return -1


class PromoCodeUpdate(BaseModel):
    """Schéma pour la mise à jour d'un code promo."""
    tickets_reward: Optional[int] = None
    is_single_use_global: Optional[bool] = None
    is_single_use_per_user: Optional[bool] = None
    usage_limit: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None

    @validator('valid_until')
    def validate_expiry_after_start(cls, v, values):
        """Valide que la date d'expiration est après la date de début."""
        if v and 'valid_from' in values and values['valid_from']:
            if v <= values['valid_from']:
                raise ValueError('La date d\'expiration doit être après la date de début')
        return v