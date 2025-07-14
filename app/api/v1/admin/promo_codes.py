from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_admin
from app.services.admin.promo_service import PromoService
from app.schemas.admin.promo import (
    CreatePromoCodeRequest,
    UpdatePromoCodeRequest,
    PromoCodeResponse
)

router = APIRouter()


@router.post("/", response_model=dict)
async def create_promo_code(
    promo_data: CreatePromoCodeRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Crée un nouveau code promo."""
    service = PromoService(db)
    return await service.create_promo_code(promo_data)


@router.get("/", response_model=List[PromoCodeResponse])
async def list_promo_codes(
    include_expired: bool = Query(False),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Liste tous les codes promo."""
    service = PromoService(db)
    return await service.list_promo_codes(include_expired)


@router.put("/{promo_code_id}", response_model=dict)
async def update_promo_code(
    promo_code_id: int,
    update_data: UpdatePromoCodeRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Met à jour un code promo."""
    service = PromoService(db)
    return await service.update_promo_code(promo_code_id, update_data)


@router.post("/{promo_code_id}/toggle-active", response_model=dict)
async def toggle_promo_code_active(
    promo_code_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Active/désactive un code promo."""
    service = PromoService(db)
    return await service.toggle_promo_code_active(promo_code_id)


@router.get("/expiring-soon", response_model=dict)
async def get_expiring_promo_codes(
    days_ahead: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Récupère les codes promo expirant bientôt."""
    service = PromoService(db)
    return await service.get_expiring_promo_codes(days_ahead)