from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.models.user import User
from app.models.arcade import Arcade, ArcadeGame
from app.models.game import Game
from app.models.promo import PromoCode
from app.models.ticket import TicketOffer
from app.api.deps import get_current_admin
from pydantic import BaseModel
from datetime import datetime, timezone

router = APIRouter()


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

    # Générer une clé API unique pour la borne
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
        assignment: ArcadeGameAssignmentRequest,
        db: Session = Depends(get_db),
        _: dict = Depends(get_current_admin)
):
    """Assigne un jeu à une borne sur un slot spécifique."""

    # Vérifier que la borne existe
    arcade = db.query(Arcade).filter(Arcade.id == assignment.arcade_id).first()
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
        ArcadeGame.arcade_id == assignment.arcade_id,
        ArcadeGame.slot_number == assignment.slot_number
    ).first()

    if existing:
        db.delete(existing)

    # Créer la nouvelle assignation
    arcade_game = ArcadeGame(
        arcade_id=assignment.arcade_id,
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
        usage_limit=promo_data.usage_limit
    )

    db.add(promo_code)
    db.commit()
    db.refresh(promo_code)

    return {"message": "Code promo créé", "promo_code_id": promo_code.id}


@router.get("/promo-codes/")
async def list_promo_codes(
        db: Session = Depends(get_db),
        _: dict = Depends(get_current_admin)
):
    """Liste tous les codes promo."""

    promo_codes = db.query(PromoCode).filter(
        PromoCode.is_deleted == False
    ).all()

    return promo_codes


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


@router.get("/users/deleted")
async def list_deleted_users(
        db: Session = Depends(get_db),
        _: dict = Depends(get_current_admin)
):
    """Liste les utilisateurs supprimés (soft delete)."""

    deleted_users = db.query(User).filter(
        User.is_deleted == True
    ).all()

    return deleted_users


@router.put("/users/{user_id}/restore")
async def restore_user(
        user_id: int,
        db: Session = Depends(get_db),
        _: dict = Depends(get_current_admin)
):
    """Restaure un utilisateur supprimé."""

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    if not user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet utilisateur n'est pas supprimé"
        )

    user.is_deleted = False
    user.deleted_at = None
    db.commit()

    return {"message": f"Utilisateur {user.pseudo} restauré"}


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


@router.delete("/arcades/{arcade_id}")
async def soft_delete_arcade(
        arcade_id: int,
        db: Session = Depends(get_db),
        _: dict = Depends(get_current_admin)
):
    """Supprime une borne d'arcade (soft delete)."""

    arcade = db.query(Arcade).filter(
        Arcade.id == arcade_id,
        Arcade.is_deleted == False
    ).first()

    if not arcade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Borne d'arcade non trouvée"
        )

    # Vérifier s'il y a des réservations en cours sur cette borne
    from app.models.reservation import Reservation, ReservationStatus
    active_reservations = db.query(Reservation).filter(
        Reservation.arcade_id == arcade_id,
        Reservation.status.in_([ReservationStatus.WAITING, ReservationStatus.PLAYING]),
        Reservation.is_deleted == False
    ).count()

    if active_reservations > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible de supprimer la borne : {active_reservations} réservation(s) active(s)"
        )

    # Soft delete
    arcade.is_deleted = True
    arcade.deleted_at = datetime.now(timezone.utc)

    # Soft delete des associations arcade-jeux
    arcade_games = db.query(ArcadeGame).filter(
        ArcadeGame.arcade_id == arcade_id,
        ArcadeGame.is_deleted == False
    ).all()

    for ag in arcade_games:
        ag.is_deleted = True
        ag.deleted_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "message": f"Borne '{arcade.nom}' supprimée avec succès",
        "arcade_id": arcade.id,
        "deleted_associations": len(arcade_games)
    }


@router.get("/arcades/deleted")
async def list_deleted_arcades(
        db: Session = Depends(get_db),
        _: dict = Depends(get_current_admin)
):
    """Liste les bornes d'arcade supprimées (soft delete)."""

    deleted_arcades = db.query(Arcade).filter(
        Arcade.is_deleted == True
    ).order_by(Arcade.deleted_at.desc()).all()

    return deleted_arcades


@router.put("/arcades/{arcade_id}/restore")
async def restore_arcade(
        arcade_id: int,
        db: Session = Depends(get_db),
        _: dict = Depends(get_current_admin)
):
    """Restaure une borne d'arcade supprimée."""

    arcade = db.query(Arcade).filter(Arcade.id == arcade_id).first()

    if not arcade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Borne d'arcade non trouvée"
        )

    if not arcade.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette borne n'est pas supprimée"
        )

    # Vérifier l'unicité de la clé API (au cas où elle aurait été réassignée)
    existing_api_key = db.query(Arcade).filter(
        Arcade.api_key == arcade.api_key,
        Arcade.is_deleted == False,
        Arcade.id != arcade_id
    ).first()

    if existing_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La clé API de cette borne est maintenant utilisée par une autre borne. "
                   "Veuillez générer une nouvelle clé API."
        )

    # Restaurer la borne
    arcade.is_deleted = False
    arcade.deleted_at = None

    # Restaurer les associations arcade-jeux
    arcade_games = db.query(ArcadeGame).filter(
        ArcadeGame.arcade_id == arcade_id,
        ArcadeGame.is_deleted == True
    ).all()

    restored_associations = 0
    for ag in arcade_games:
        # Vérifier que le jeu existe toujours
        game_exists = db.query(Game).filter(
            Game.id == ag.game_id,
            Game.is_deleted == False
        ).first()

        if game_exists:
            # Vérifier qu'il n'y a pas de conflit de slot
            slot_conflict = db.query(ArcadeGame).filter(
                ArcadeGame.arcade_id == arcade_id,
                ArcadeGame.slot_number == ag.slot_number,
                ArcadeGame.is_deleted == False,
                ArcadeGame.id != ag.id
            ).first()

            if not slot_conflict:
                ag.is_deleted = False
                ag.deleted_at = None
                restored_associations += 1

    db.commit()

    return {
        "message": f"Borne '{arcade.nom}' restaurée avec succès",
        "arcade_id": arcade.id,
        "restored_associations": restored_associations,
        "note": f"{len(arcade_games) - restored_associations} association(s) non restaurée(s) en raison de conflits" if restored_associations < len(
            arcade_games) else None
    }


@router.put("/arcades/{arcade_id}/regenerate-api-key")
async def regenerate_arcade_api_key(
        arcade_id: int,
        db: Session = Depends(get_db),
        _: dict = Depends(get_current_admin)
):
    """Régénère la clé API d'une borne d'arcade."""

    arcade = db.query(Arcade).filter(
        Arcade.id == arcade_id
    ).first()

    if not arcade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Borne d'arcade non trouvée"
        )

    # Générer une nouvelle clé API unique
    import secrets
    new_api_key = f"arcade_key_{secrets.token_urlsafe(16)}"

    # Vérifier l'unicité (au cas où)
    while db.query(Arcade).filter(Arcade.api_key == new_api_key).first():
        new_api_key = f"arcade_key_{secrets.token_urlsafe(16)}"

    old_api_key = arcade.api_key
    arcade.api_key = new_api_key
    db.commit()

    return {
        "message": f"Clé API de la borne '{arcade.nom}' régénérée",
        "arcade_id": arcade.id,
        "old_api_key": old_api_key[:20] + "...",  # Masquer partiellement
        "new_api_key": new_api_key
    }