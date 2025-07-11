from pydantic import BaseModel, EmailStr, validator
from datetime import date, datetime
from typing import Optional, List, Dict, Any


class UserBase(BaseModel):
    email: EmailStr
    nom: str
    prenom: str
    pseudo: str
    date_naissance: date
    numero_telephone: str


class UserCreate(UserBase):
    firebase_uid: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    nom: Optional[str] = None
    prenom: Optional[str] = None
    pseudo: Optional[str] = None
    date_naissance: Optional[date] = None
    numero_telephone: Optional[str] = None


class UserResponse(UserBase):
    id: int
    tickets_balance: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserSearchResponse(BaseModel):
    id: int
    pseudo: str
    nom: str
    prenom: str

    class Config:
        from_attributes = True


class UserDeletionResponse(BaseModel):
    """Schéma de réponse pour la suppression d'utilisateur."""
    message: str
    user_id: int
    deleted_friendships: int
    deleted_promo_uses: Optional[int] = None
    deleted_purchases: Optional[int] = None
    note: str


class UserDeletionImpactResponse(BaseModel):
    """Schéma de réponse pour l'analyse d'impact de suppression."""

    class UserSummary(BaseModel):
        id: int
        pseudo: str
        email: str
        tickets_balance: int
        created_at: str

    class BlockingFactors(BaseModel):
        active_reservations: int

    class DeletionImpact(BaseModel):
        friendships_to_delete: int
        promo_uses_to_delete: int
        purchases_to_delete: int
        completed_reservations_preserved: int
        scores_anonymized: int

    user: UserSummary
    can_delete: bool
    blocking_factors: Optional[BlockingFactors] = None
    deletion_impact: DeletionImpact
    recommendations: List[str]


class ForceCancelReservationsResponse(BaseModel):
    """Schéma de réponse pour l'annulation forcée de réservations."""
    message: str
    user_id: int
    cancelled_reservations: int
    refunded_tickets: int
    new_tickets_balance: int


class UserAdminListResponse(BaseModel):
    """Schéma de réponse pour la liste admin des utilisateurs."""
    id: int
    pseudo: str
    email: str
    nom: str
    prenom: str
    tickets_balance: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    deleted_at: Optional[datetime] = None

    # Statistiques rapides
    active_reservations: Optional[int] = None
    total_scores: Optional[int] = None
    friendships_count: Optional[int] = None

    class Config:
        from_attributes = True


class BulkUserActionRequest(BaseModel):
    """Schéma pour les actions en masse sur les utilisateurs."""
    user_ids: List[int]
    action: str  # "delete", "restore", "force_cancel_reservations"
    reason: Optional[str] = None

    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ["delete", "restore", "force_cancel_reservations"]
        if v not in allowed_actions:
            raise ValueError(f'Action must be one of: {", ".join(allowed_actions)}')
        return v

    @validator('user_ids')
    def validate_user_ids(cls, v):
        if not v:
            raise ValueError('At least one user ID is required')
        if len(v) > 100:
            raise ValueError('Maximum 100 users can be processed at once')
        return v


class BulkUserActionResponse(BaseModel):
    """Schéma de réponse pour les actions en masse."""
    action: str
    requested_users: int
    successful_actions: int
    failed_actions: int
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


class UserDeletionStatsResponse(BaseModel):
    """Schéma pour les statistiques de suppression."""
    total_users: int
    active_users: int
    deleted_users: int
    deletion_rate_percentage: float
    recent_deletions_7d: int
    recent_deletions_30d: int
    top_deletion_reasons: List[Dict[str, Any]]
    avg_user_lifetime_days: float