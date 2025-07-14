# app/schemas/admin/game.py

from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class CreateGameRequest(BaseModel):
    nom: str
    description: Optional[str] = None
    min_players: int = 1
    max_players: int = 2
    ticket_cost: int = 1

    @validator('nom')
    def validate_nom(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Le nom doit contenir au moins 2 caractères')
        if len(v.strip()) > 100:
            raise ValueError('Le nom ne peut pas dépasser 100 caractères')
        return v.strip()

    @validator('description')
    def validate_description(cls, v):
        if v and len(v.strip()) > 500:
            raise ValueError('La description ne peut pas dépasser 500 caractères')
        return v.strip() if v else None

    @validator('min_players')
    def validate_min_players(cls, v):
        if v < 1 or v > 8:
            raise ValueError('Le nombre minimum de joueurs doit être entre 1 et 8')
        return v

    @validator('max_players')
    def validate_max_players(cls, v, values):
        if v < 1 or v > 8:
            raise ValueError('Le nombre maximum de joueurs doit être entre 1 et 8')
        if 'min_players' in values and v < values['min_players']:
            raise ValueError('Le nombre maximum de joueurs doit être >= au minimum')
        return v

    @validator('ticket_cost')
    def validate_ticket_cost(cls, v):
        if v < 0:
            raise ValueError('Le coût en tickets ne peut pas être négatif')
        if v > 100:
            raise ValueError('Le coût en tickets ne peut pas dépasser 100')
        return v


class UpdateGameRequest(BaseModel):
    nom: Optional[str] = None
    description: Optional[str] = None
    min_players: Optional[int] = None
    max_players: Optional[int] = None
    ticket_cost: Optional[int] = None

    @validator('nom')
    def validate_nom(cls, v):
        if v is not None:
            if not v or len(v.strip()) < 2:
                raise ValueError('Le nom doit contenir au moins 2 caractères')
            if len(v.strip()) > 100:
                raise ValueError('Le nom ne peut pas dépasser 100 caractères')
            return v.strip()
        return v

    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            if len(v.strip()) > 500:
                raise ValueError('La description ne peut pas dépasser 500 caractères')
            return v.strip()
        return v

    @validator('min_players')
    def validate_min_players(cls, v):
        if v is not None and (v < 1 or v > 8):
            raise ValueError('Le nombre minimum de joueurs doit être entre 1 et 8')
        return v

    @validator('max_players')
    def validate_max_players(cls, v, values):
        if v is not None:
            if v < 1 or v > 8:
                raise ValueError('Le nombre maximum de joueurs doit être entre 1 et 8')
            if 'min_players' in values and values['min_players'] and v < values['min_players']:
                raise ValueError('Le nombre maximum de joueurs doit être >= au minimum')
        return v

    @validator('ticket_cost')
    def validate_ticket_cost(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError('Le coût en tickets ne peut pas être négatif')
            if v > 100:
                raise ValueError('Le coût en tickets ne peut pas dépasser 100')
        return v


class GameResponse(BaseModel):
    id: int
    nom: str
    description: Optional[str]
    min_players: int
    max_players: int
    ticket_cost: int
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GameStatsResponse(BaseModel):
    game_id: int
    game_name: str
    period_days: int
    reservation_stats: Dict[str, Any]
    score_stats: Dict[str, Any]
    revenue_stats: Dict[str, Any]
    arcade_popularity: List[Dict[str, Any]]
    generated_at: str

    class Config:
        from_attributes = True


class GameArcadeAssociation(BaseModel):
    arcade_id: int
    arcade_name: str
    arcade_location: str
    slot_number: int
    assigned_at: str

    class Config:
        from_attributes = True


class GameListResponse(BaseModel):
    games: List[GameResponse]
    total_count: int
    active_count: int
    deleted_count: int

    class Config:
        from_attributes = True


class GameDeletionImpactResponse(BaseModel):
    """Schéma pour l'analyse d'impact de suppression d'un jeu."""

    class GameSummary(BaseModel):
        id: int
        nom: str
        description: Optional[str]
        ticket_cost: int
        created_at: str

    class BlockingFactors(BaseModel):
        active_reservations: int

    class DeletionImpact(BaseModel):
        arcade_associations_to_delete: int
        historical_reservations_preserved: int
        historical_scores_preserved: int
        estimated_revenue_lost: float

    game: GameSummary
    can_delete: bool
    blocking_factors: Optional[BlockingFactors] = None
    deletion_impact: DeletionImpact
    recommendations: List[str]


class BulkGameActionRequest(BaseModel):
    """Schéma pour les actions en masse sur les jeux."""
    game_ids: List[int]
    action: str  # "delete", "restore", "update_cost"
    parameters: Optional[Dict[str, Any]] = None

    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ["delete", "restore", "update_cost", "toggle_active"]
        if v not in allowed_actions:
            raise ValueError(f'Action must be one of: {", ".join(allowed_actions)}')
        return v

    @validator('game_ids')
    def validate_game_ids(cls, v):
        if not v:
            raise ValueError('At least one game ID is required')
        if len(v) > 50:
            raise ValueError('Maximum 50 games can be processed at once')
        return v


class BulkGameActionResponse(BaseModel):
    """Schéma de réponse pour les actions en masse."""
    action: str
    requested_games: int
    successful_actions: int
    failed_actions: int
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


class GameUsageAnalyticsRequest(BaseModel):
    """Schéma pour les demandes d'analytics d'usage."""
    game_ids: Optional[List[int]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    group_by: str = "day"  # "hour", "day", "week", "month"
    include_revenue: bool = True

    @validator('group_by')
    def validate_group_by(cls, v):
        allowed_values = ["hour", "day", "week", "month"]
        if v not in allowed_values:
            raise ValueError(f'group_by must be one of: {", ".join(allowed_values)}')
        return v

    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v <= values['start_date']:
                raise ValueError('end_date must be after start_date')
        return v


class GameUsageAnalyticsResponse(BaseModel):
    """Schéma de réponse pour les analytics d'usage."""
    period_start: datetime
    period_end: datetime
    group_by: str
    games_analyzed: List[int]
    data_points: List[Dict[str, Any]]
    summary: Dict[str, Any]
    generated_at: datetime

    class Config:
        from_attributes = True