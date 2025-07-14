from pydantic import BaseModel, validator
from typing import Optional


class CreateArcadeRequest(BaseModel):
    nom: str
    description: Optional[str] = None
    localisation: str
    latitude: float
    longitude: float

    @validator('nom')
    def validate_nom(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Le nom doit contenir au moins 2 caractères')
        return v.strip()

    @validator('latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('La latitude doit être entre -90 et 90')
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('La longitude doit être entre -180 et 180')
        return v


class ArcadeGameAssignmentRequest(BaseModel):
    arcade_id: int
    game_id: int
    slot_number: int

    @validator('slot_number')
    def validate_slot_number(cls, v):
        if v not in [1, 2]:
            raise ValueError('Le slot doit être 1 ou 2')
        return v


class ArcadeResponse(BaseModel):
    id: int
    nom: str
    description: Optional[str]
    localisation: str
    latitude: float
    longitude: float
    api_key: Optional[str] = None  # Masqué par défaut
    is_deleted: bool = False

    class Config:
        from_attributes = True