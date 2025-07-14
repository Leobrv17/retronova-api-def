from fastapi import APIRouter

# Import des sous-modules admin (qui n'existent pas encore, donc on les commente pour l'instant)
# from .admin import arcades, games, promo_codes, users, stats

# Pour l'instant, on garde l'ancien code simplifié en attendant la migration complète
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.core.database import get_db
from app.models.user import User
from app.models.arcade import Arcade, ArcadeGame
from app.models.game import Game
from app.models.promo import PromoCode
from app.models.ticket import TicketOffer
from app.api.deps import get_current_admin
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta

router = APIRouter()

# Modèles Pydantic pour les requêtes
class CreateArcadeRequest(BaseModel):
    nom: str
    description: str
    localisation: str
    latitude: float
    longitude: float

class CreateGameRequest(BaseModel):
    nom: str
    description: str
    min_players: int = 1
    max_players: int = 2
    ticket_cost: int = 1

class CreatePromoCodeRequest(BaseModel):
    code: str
    tickets_reward: int
    is_single_use_global: bool = False
    is_single_use_per_user: bool = True
    usage_limit: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool = True

class UpdateUserTicketsRequest(BaseModel):
    user_id: int
    tickets_to_add: int

class ArcadeGameAssignmentRequest(BaseModel):
    arcade_id: int
    game_id: int
    slot_number: int

# === GESTION DES BORNES ===
@router.post("/arcades/")
async def create_arcade(
    arcade_data: CreateArcadeRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Crée une nouvelle borne d'arcade."""
    import secrets
    api_key = f"arcade_key_{secrets.token_urlsafe(16)}"

    arcade = Arcade(
        nom=arcade_data.nom,
        description=arcade_data.description,
        api_key=api_key,
        localisation=arcade_data.localisation,
        latitude=arcade_data.latitude,
        longitude=arcade_data.longitude
    )

    db.add(arcade)
    db.commit()
    db.refresh(arcade)

    return {"message": "Borne créée", "arcade_id": arcade.id, "api_key": api_key}

@router.put("/arcades/{arcade_id}/games")
async def assign_game_to_arcade(
    arcade_id: int,
    assignment: ArcadeGameAssignmentRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Assigne un jeu à une borne sur un slot spécifique."""
    # Vérifier que la borne existe
    arcade = db.query(Arcade).filter(Arcade.id == arcade_id).first()
    if not arcade:
        raise HTTPException(status_code=404, detail="Borne non trouvée")

    # Vérifier que le jeu existe
    game = db.query(Game).filter(Game.id == assignment.game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Jeu non trouvé")

    # Vérifier que le slot est valide (1 ou 2)
    if assignment.slot_number not in [1, 2]:
        raise HTTPException(status_code=400, detail="Le slot doit être 1 ou 2")

    # Supprimer l'ancien jeu sur ce slot s'il existe
    existing = db.query(ArcadeGame).filter(
        ArcadeGame.arcade_id == arcade_id,
        ArcadeGame.slot_number == assignment.slot_number
    ).first()

    if existing:
        db.delete(existing)

    # Créer la nouvelle assignation
    arcade_game = ArcadeGame(
        arcade_id=arcade_id,
        game_id=assignment.game_id,
        slot_number=assignment.slot_number
    )

    db.add(arcade_game)
    db.commit()

    return {"message": f"Jeu {game.nom} assigné au slot {assignment.slot_number} de la borne {arcade.nom}"}

# === GESTION DES JEUX ===
@router.post("/games/")
async def create_game(
    game_data: CreateGameRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Crée un nouveau jeu."""
    game = Game(
        nom=game_data.nom,
        description=game_data.description,
        min_players=game_data.min_players,
        max_players=game_data.max_players,
        ticket_cost=game_data.ticket_cost
    )

    db.add(game)
    db.commit()
    db.refresh(game)

    return {"message": "Jeu créé", "game_id": game.id}

# === GESTION DES CODES PROMO ===
@router.post("/promo-codes/")
async def create_promo_code(
    promo_data: CreatePromoCodeRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Crée un nouveau code promo."""
    # Validation des dates
    if promo_data.valid_from and promo_data.valid_until:
        if promo_data.valid_until <= promo_data.valid_from:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La date d'expiration doit être après la date de début"
            )

    # Vérifier que le code n'existe pas déjà
    existing = db.query(PromoCode).filter(
        PromoCode.code == promo_data.code.upper().strip()
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce code promo existe déjà"
        )

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

    db.add(promo_code)
    db.commit()
    db.refresh(promo_code)

    return {
        "message": "Code promo créé",
        "promo_code_id": promo_code.id,
        "is_valid_now": promo_code.is_valid_now(),
        "days_until_expiry": promo_code.days_until_expiry()
    }

@router.get("/promo-codes/")
async def list_promo_codes(
    include_expired: bool = False,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Liste tous les codes promo."""
    query = db.query(PromoCode).filter(PromoCode.is_deleted == False)

    if not include_expired:
        now = datetime.now(timezone.utc)
        query = query.filter(
            (PromoCode.valid_until.is_(None) | (PromoCode.valid_until > now))
        )

    promo_codes = query.order_by(PromoCode.created_at.desc()).all()

    result = []
    for promo in promo_codes:
        result.append({
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
        })

    return result

# === GESTION DES UTILISATEURS ===
@router.put("/users/tickets")
async def update_user_tickets(
    update_data: UpdateUserTicketsRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Ajoute ou retire des tickets à un utilisateur."""
    user = db.query(User).filter(
        User.id == update_data.user_id,
        User.is_deleted == False
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    old_balance = user.tickets_balance
    user.tickets_balance += update_data.tickets_to_add

    # Empêcher un solde négatif
    if user.tickets_balance < 0:
        user.tickets_balance = 0

    db.commit()

    return {
        "message": f"Solde mis à jour pour {user.pseudo}",
        "old_balance": old_balance,
        "new_balance": user.tickets_balance,
        "tickets_added": update_data.tickets_to_add
    }

# === STATISTIQUES ===
@router.get("/stats")
async def get_admin_stats(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Récupère les statistiques globales de la plateforme."""
    # Compter les utilisateurs actifs
    active_users = db.query(User).filter(User.is_deleted == False).count()

    # Compter les bornes
    total_arcades = db.query(Arcade).filter(Arcade.is_deleted == False).count()

    # Compter les jeux
    total_games = db.query(Game).filter(Game.is_deleted == False).count()

    # Compter les codes promo actifs
    active_promo_codes = db.query(PromoCode).filter(
        PromoCode.is_deleted == False
    ).count()

    # Total de tickets en circulation
    total_tickets = db.query(func.sum(User.tickets_balance)).filter(
        User.is_deleted == False
    ).scalar() or 0

    return {
        "active_users": active_users,
        "total_arcades": total_arcades,
        "total_games": total_games,
        "active_promo_codes": active_promo_codes,
        "total_tickets_in_circulation": total_tickets,
        "timestamp": datetime.utcnow().isoformat()
    }