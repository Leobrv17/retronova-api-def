from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_admin
from app.services.admin.arcade_service import ArcadeService
from app.schemas.admin.arcade import (
    CreateArcadeRequest,
    ArcadeGameAssignmentRequest,
    ArcadeResponse
)

router = APIRouter()


@router.post("/", response_model=dict)
async def create_arcade(
    arcade_data: CreateArcadeRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Crée une nouvelle borne d'arcade."""
    service = ArcadeService(db)
    return await service.create_arcade(arcade_data)


@router.put("/{arcade_id}/games", response_model=dict)
async def assign_game_to_arcade(
    arcade_id: int,
    assignment: ArcadeGameAssignmentRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Assigne un jeu à une borne sur un slot spécifique."""
    service = ArcadeService(db)
    return await service.assign_game_to_arcade(arcade_id, assignment)


@router.delete("/{arcade_id}")
async def delete_arcade(
    arcade_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Supprime une borne d'arcade (soft delete)."""
    service = ArcadeService(db)
    return await service.soft_delete_arcade(arcade_id)


@router.get("/deleted", response_model=List[ArcadeResponse])
async def list_deleted_arcades(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Liste les bornes supprimées."""
    service = ArcadeService(db)
    return await service.list_deleted_arcades()


@router.put("/{arcade_id}/restore")
async def restore_arcade(
    arcade_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Restaure une borne supprimée."""
    service = ArcadeService(db)
    return await service.restore_arcade(arcade_id)


@router.put("/{arcade_id}/regenerate-api-key")
async def regenerate_api_key(
    arcade_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Régénère la clé API d'une borne."""
    service = ArcadeService(db)
    return await service.regenerate_api_key(arcade_id)