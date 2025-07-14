from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_admin
from app.services.admin.user_service import UserService
from app.schemas.admin.user import (
    UpdateUserTicketsRequest,
    UserDeletionResponse,
    UserDeletionImpactResponse
)

router = APIRouter()


@router.put("/tickets", response_model=dict)
async def update_user_tickets(
    update_data: UpdateUserTicketsRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Ajoute ou retire des tickets à un utilisateur."""
    service = UserService(db)
    return await service.update_user_tickets(update_data)


@router.get("/deleted", response_model=List[dict])
async def list_deleted_users(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Liste les utilisateurs supprimés."""
    service = UserService(db)
    return await service.list_deleted_users()


@router.put("/{user_id}/restore", response_model=dict)
async def restore_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Restaure un utilisateur supprimé."""
    service = UserService(db)
    return await service.restore_user(user_id)


@router.delete("/{user_id}", response_model=UserDeletionResponse)
async def soft_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Supprime un utilisateur (soft delete)."""
    service = UserService(db)
    return await service.soft_delete_user(user_id)


@router.get("/{user_id}/deletion-impact", response_model=UserDeletionImpactResponse)
async def get_user_deletion_impact(
    user_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Analyse l'impact de la suppression d'un utilisateur."""
    service = UserService(db)
    return await service.get_user_deletion_impact(user_id)


@router.put("/{user_id}/force-cancel-reservations", response_model=dict)
async def force_cancel_user_reservations(
    user_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Force l'annulation des réservations d'un utilisateur."""
    service = UserService(db)
    return await service.force_cancel_user_reservations(user_id)