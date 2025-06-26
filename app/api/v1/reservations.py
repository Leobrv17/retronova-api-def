from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import random
from app.core.database import get_db
from app.models.user import User
from app.models.arcade import Arcade, ArcadeGame
from app.models.game import Game
from app.models.reservation import Reservation, ReservationStatus
from app.api.deps import get_current_user
from pydantic import BaseModel

router = APIRouter()


class CreateReservationRequest(BaseModel):
    arcade_id: int
    game_id: int
    player2_id: Optional[int] = None


class ReservationResponse(BaseModel):
    id: int
    unlock_code: str
    status: ReservationStatus
    arcade_name: str
    game_name: str
    player_pseudo: str
    player2_pseudo: Optional[str]
    tickets_used: int
    position_in_queue: Optional[int]

    class Config:
        from_attributes = True


@router.post("/", response_model=ReservationResponse)
async def create_reservation(
        reservation_data: CreateReservationRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Crée une nouvelle réservation de partie."""

    # Vérifier que la borne existe
    arcade = db.query(Arcade).filter(
        Arcade.id == reservation_data.arcade_id,
        Arcade.is_deleted == False
    ).first()

    if not arcade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Borne d'arcade non trouvée"
        )

    # Vérifier que le jeu existe et est disponible sur cette borne
    arcade_game = db.query(ArcadeGame).join(Game).filter(
        ArcadeGame.arcade_id == reservation_data.arcade_id,
        ArcadeGame.game_id == reservation_data.game_id,
        ArcadeGame.is_deleted == False,
        Game.is_deleted == False
    ).first()

    if not arcade_game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jeu non disponible sur cette borne"
        )

    game = arcade_game.game

    # Vérifier le nombre de joueurs
    player_count = 2 if reservation_data.player2_id else 1

    if player_count < game.min_players or player_count > game.max_players:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ce jeu nécessite entre {game.min_players} et {game.max_players} joueurs"
        )

    # Vérifier le joueur 2 s'il est spécifié
    player2 = None
    if reservation_data.player2_id:
        if reservation_data.player2_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vous ne pouvez pas jouer contre vous-même"
            )

        player2 = db.query(User).filter(
            User.id == reservation_data.player2_id,
            User.is_deleted == False
        ).first()

        if not player2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Joueur 2 non trouvé"
            )

    # Vérifier que l'utilisateur a assez de tickets
    if current_user.tickets_balance < game.ticket_cost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tickets insuffisants"
        )

    # Générer un code de déverrouillage (1-8)
    unlock_code = str(random.randint(1, 8))

    # Créer la réservation
    reservation = Reservation(
        player_id=current_user.id,
        player2_id=reservation_data.player2_id,
        arcade_id=reservation_data.arcade_id,
        game_id=reservation_data.game_id,
        unlock_code=unlock_code,
        tickets_used=game.ticket_cost
    )

    # Déduire les tickets
    current_user.tickets_balance -= game.ticket_cost

    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    # Calculer la position dans la file d'attente
    queue_position = db.query(Reservation).filter(
        Reservation.arcade_id == reservation_data.arcade_id,
        Reservation.status == ReservationStatus.WAITING,
        Reservation.created_at <= reservation.created_at,
        Reservation.is_deleted == False
    ).count()

    return ReservationResponse(
        id=reservation.id,
        unlock_code=unlock_code,
        status=reservation.status,
        arcade_name=arcade.nom,
        game_name=game.nom,
        player_pseudo=current_user.pseudo,
        player2_pseudo=player2.pseudo if player2 else None,
        tickets_used=game.ticket_cost,
        position_in_queue=queue_position
    )


@router.get("/", response_model=List[ReservationResponse])
async def get_my_reservations(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Récupère les réservations de l'utilisateur actuel."""

    reservations = db.query(Reservation).join(
        Arcade, Reservation.arcade_id == Arcade.id
    ).join(
        Game, Reservation.game_id == Game.id
    ).filter(
        (Reservation.player_id == current_user.id) | (Reservation.player2_id == current_user.id),
        Reservation.is_deleted == False
    ).order_by(Reservation.created_at.desc()).all()

    result = []
    for reservation in reservations:
        # Récupérer le joueur 2 si nécessaire
        player2_pseudo = None
        if reservation.player2_id:
            player2 = db.query(User).filter(User.id == reservation.player2_id).first()
            if player2:
                player2_pseudo = player2.pseudo

        # Calculer la position dans la file si en attente
        position_in_queue = None
        if reservation.status == ReservationStatus.WAITING:
            position_in_queue = db.query(Reservation).filter(
                Reservation.arcade_id == reservation.arcade_id,
                Reservation.status == ReservationStatus.WAITING,
                Reservation.created_at <= reservation.created_at,
                Reservation.is_deleted == False
            ).count()

        result.append(ReservationResponse(
            id=reservation.id,
            unlock_code=reservation.unlock_code,
            status=reservation.status,
            arcade_name=reservation.arcade.nom,
            game_name=reservation.game.nom,
            player_pseudo=reservation.player.pseudo,
            player2_pseudo=player2_pseudo,
            tickets_used=reservation.tickets_used,
            position_in_queue=position_in_queue
        ))

    return result


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(
        reservation_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Récupère les détails d'une réservation spécifique."""

    reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id,
        (Reservation.player_id == current_user.id) | (Reservation.player2_id == current_user.id),
        Reservation.is_deleted == False
    ).first()

    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Réservation non trouvée"
        )

    # Récupérer le joueur 2 si nécessaire
    player2_pseudo = None
    if reservation.player2_id:
        player2 = db.query(User).filter(User.id == reservation.player2_id).first()
        if player2:
            player2_pseudo = player2.pseudo

    # Calculer la position dans la file si en attente
    position_in_queue = None
    if reservation.status == ReservationStatus.WAITING:
        position_in_queue = db.query(Reservation).filter(
            Reservation.arcade_id == reservation.arcade_id,
            Reservation.status == ReservationStatus.WAITING,
            Reservation.created_at <= reservation.created_at,
            Reservation.is_deleted == False
        ).count()

    return ReservationResponse(
        id=reservation.id,
        unlock_code=reservation.unlock_code,
        status=reservation.status,
        arcade_name=reservation.arcade.nom,
        game_name=reservation.game.nom,
        player_pseudo=reservation.player.pseudo,
        player2_pseudo=player2_pseudo,
        tickets_used=reservation.tickets_used,
        position_in_queue=position_in_queue
    )


@router.delete("/{reservation_id}")
async def cancel_reservation(
        reservation_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Annule une réservation (seulement si en attente)."""

    reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id,
        Reservation.player_id == current_user.id,  # Seul le joueur principal peut annuler
        Reservation.is_deleted == False
    ).first()

    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Réservation non trouvée"
        )

    if reservation.status != ReservationStatus.WAITING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seules les réservations en attente peuvent être annulées"
        )

    # Annuler la réservation et rembourser les tickets
    reservation.status = ReservationStatus.CANCELLED
    current_user.tickets_balance += reservation.tickets_used

    db.commit()

    return {"message": "Réservation annulée, tickets remboursés"}