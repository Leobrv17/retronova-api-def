from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.promo import PromoCode, PromoUse
from app.api.deps import get_current_user
from pydantic import BaseModel

router = APIRouter()


class UsePromoCodeRequest(BaseModel):
    code: str


class PromoCodeResponse(BaseModel):
    tickets_received: int
    new_balance: int
    message: str


@router.post("/use", response_model=PromoCodeResponse)
async def use_promo_code(
        promo_data: UsePromoCodeRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Utilise un code promo pour obtenir des tickets."""

    # Rechercher le code promo
    promo_code = db.query(PromoCode).filter(
        PromoCode.code == promo_data.code.upper().strip(),
        PromoCode.is_deleted == False
    ).first()

    if not promo_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Code promo invalide"
        )

    # Vérifier si l'utilisateur a déjà utilisé ce code
    if promo_code.is_single_use_per_user:
        existing_use = db.query(PromoUse).filter(
            PromoUse.user_id == current_user.id,
            PromoUse.promo_code_id == promo_code.id,
            PromoUse.is_deleted == False
        ).first()

        if existing_use:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vous avez déjà utilisé ce code promo"
            )

    # Vérifier la limite globale d'utilisation
    if promo_code.usage_limit and promo_code.current_uses >= promo_code.usage_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce code promo a atteint sa limite d'utilisation"
        )

    # Vérifier si c'est un code à usage unique global
    if promo_code.is_single_use_global and promo_code.current_uses > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce code promo a déjà été utilisé"
        )

    # Utiliser le code promo
    promo_use = PromoUse(
        user_id=current_user.id,
        promo_code_id=promo_code.id,
        tickets_received=promo_code.tickets_reward
    )

    # Créditer les tickets à l'utilisateur
    current_user.tickets_balance += promo_code.tickets_reward

    # Incrémenter le compteur d'utilisations
    promo_code.current_uses += 1

    db.add(promo_use)
    db.commit()

    return PromoCodeResponse(
        tickets_received=promo_code.tickets_reward,
        new_balance=current_user.tickets_balance,
        message=f"Code promo utilisé avec succès ! Vous avez reçu {promo_code.tickets_reward} tickets."
    )


@router.get("/history")
async def get_promo_history(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Récupère l'historique des codes promo utilisés par l'utilisateur."""

    promo_uses = db.query(PromoUse).join(
        PromoCode, PromoUse.promo_code_id == PromoCode.id
    ).filter(
        PromoUse.user_id == current_user.id,
        PromoUse.is_deleted == False
    ).order_by(PromoUse.created_at.desc()).all()

    history = []
    for promo_use in promo_uses:
        history.append({
            "id": promo_use.id,
            "code": promo_use.promo_code.code,
            "tickets_received": promo_use.tickets_received,
            "used_at": promo_use.created_at.isoformat()
        })

    return history