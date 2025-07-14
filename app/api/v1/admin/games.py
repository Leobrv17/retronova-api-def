# app/api/v1/admin/games.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.api.deps import get_current_admin
from app.services.admin.game_service import GameService
from app.schemas.admin.game import (
    CreateGameRequest,
    UpdateGameRequest,
    GameResponse,
    GameStatsResponse
)

router = APIRouter()


@router.post("/", response_model=dict)
async def create_game(
    game_data: CreateGameRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Crée un nouveau jeu."""
    service = GameService(db)
    return await service.create_game(game_data)


@router.get("/", response_model=List[GameResponse])
async def list_games(
    include_deleted: bool = Query(False, description="Inclure les jeux supprimés"),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Liste tous les jeux (admin)."""
    service = GameService(db)
    return await service.list_games(include_deleted=include_deleted)


@router.get("/{game_id}", response_model=GameResponse)
async def get_game(
    game_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Récupère un jeu par ID."""
    service = GameService(db)
    return await service.get_game_by_id(game_id)


@router.put("/{game_id}", response_model=dict)
async def update_game(
    game_id: int,
    update_data: UpdateGameRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Met à jour un jeu."""
    service = GameService(db)
    return await service.update_game(game_id, update_data)


@router.delete("/{game_id}")
async def delete_game(
    game_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Supprime un jeu (soft delete)."""
    service = GameService(db)
    return await service.soft_delete_game(game_id)


@router.get("/deleted", response_model=List[GameResponse])
async def list_deleted_games(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Liste les jeux supprimés."""
    service = GameService(db)
    return await service.list_deleted_games()


@router.put("/{game_id}/restore")
async def restore_game(
    game_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Restaure un jeu supprimé."""
    service = GameService(db)
    return await service.restore_game(game_id)


@router.get("/{game_id}/stats", response_model=GameStatsResponse)
async def get_game_stats(
    game_id: int,
    days: int = Query(30, ge=1, le=365, description="Nombre de jours pour les statistiques"),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Récupère les statistiques d'un jeu."""
    service = GameService(db)
    return await service.get_game_stats(game_id, days)


@router.get("/{game_id}/arcades", response_model=List[dict])
async def get_game_arcades(
    game_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Liste les bornes où ce jeu est disponible."""
    service = GameService(db)
    return await service.get_game_arcades(game_id)


@router.put("/{game_id}/toggle-active")
async def toggle_game_active(
    game_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Active/désactive un jeu."""
    service = GameService(db)
    return await service.toggle_game_active(game_id)