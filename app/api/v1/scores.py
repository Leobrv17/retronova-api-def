from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from app.core.database import get_db
from app.models.user import User
from app.models.score import Score
from app.models.game import Game
from app.models.arcade import Arcade
from app.models.friend import Friendship, FriendshipStatus
from app.api.deps import get_current_user, verify_arcade_key
from pydantic import BaseModel
from sqlalchemy.orm import aliased

router = APIRouter()


class CreateScoreRequest(BaseModel):
    player1_id: int
    player2_id: Optional[int] = None  # Maintenant optionnel
    game_id: int
    arcade_id: int
    score_j1: int
    score_j2: Optional[int] = None  # Optionnel pour jeu solo


class ScoreResponse(BaseModel):
    id: int
    player1_pseudo: str
    player2_pseudo: Optional[str] = None  # Peut être None
    game_name: str
    arcade_name: str
    score_j1: int
    score_j2: Optional[int] = None
    winner_pseudo: Optional[str] = None  # Peut être None pour jeu solo
    created_at: str
    is_single_player: bool  # Nouveau champ

    class Config:
        from_attributes = True


@router.post("/", response_model=ScoreResponse)
async def create_score(
        score_data: CreateScoreRequest,
        db: Session = Depends(get_db),
        _: bool = Depends(verify_arcade_key)
):
    """Enregistre un nouveau score (authentification par clé API borne)."""

    # Vérifier que le joueur 1 existe
    player1 = db.query(User).filter(
        User.id == score_data.player1_id,
        User.is_deleted == False
    ).first()

    if not player1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Joueur 1 non trouvé"
        )

    # Si c'est un jeu à 2 joueurs, vérifier le joueur 2
    player2 = None
    if score_data.player2_id:
        if score_data.player1_id == score_data.player2_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Les deux joueurs ne peuvent pas être identiques"
            )

        player2 = db.query(User).filter(
            User.id == score_data.player2_id,
            User.is_deleted == False
        ).first()

        if not player2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Joueur 2 non trouvé"
            )

    # Vérifier que le jeu existe
    game = db.query(Game).filter(
        Game.id == score_data.game_id,
        Game.is_deleted == False
    ).first()

    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jeu non trouvé"
        )

    # Vérifier que la borne existe
    arcade = db.query(Arcade).filter(
        Arcade.id == score_data.arcade_id,
        Arcade.is_deleted == False
    ).first()

    if not arcade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Borne d'arcade non trouvée"
        )

    # Validation cohérence jeu solo/multi
    is_single_player = score_data.player2_id is None

    if is_single_player:
        # Jeu solo : vérifier que le jeu accepte 1 joueur
        if game.min_players > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ce jeu nécessite au minimum {game.min_players} joueurs"
            )
    else:
        # Jeu multi : vérifier que le jeu accepte 2 joueurs
        if game.max_players < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ce jeu ne supporte pas 2 joueurs"
            )

    # Créer le score
    score = Score(
        player1_id=score_data.player1_id,
        player2_id=score_data.player2_id,
        game_id=score_data.game_id,
        arcade_id=score_data.arcade_id,
        score_j1=score_data.score_j1,
        score_j2=score_data.score_j2
    )

    db.add(score)
    db.commit()
    db.refresh(score)

    # Déterminer le gagnant
    winner_pseudo = None
    if not is_single_player:
        if score_data.score_j1 > score_data.score_j2:
            winner_pseudo = player1.pseudo
        elif score_data.score_j2 > score_data.score_j1:
            winner_pseudo = player2.pseudo
        else:
            winner_pseudo = "Égalité"

    return ScoreResponse(
        id=score.id,
        player1_pseudo=player1.pseudo,
        player2_pseudo=player2.pseudo if player2 else None,
        game_name=game.nom,
        arcade_name=arcade.nom,
        score_j1=score_data.score_j1,
        score_j2=score_data.score_j2,
        winner_pseudo=winner_pseudo,
        is_single_player=is_single_player,
        created_at=score.created_at.isoformat()
    )


@router.get("/", response_model=List[ScoreResponse])
async def get_scores(
        game_id: Optional[int] = Query(None, description="Filtrer par jeu"),
        arcade_id: Optional[int] = Query(None, description="Filtrer par borne"),
        friends_only: bool = Query(False, description="Afficher seulement les scores avec mes amis"),
        single_player_only: bool = Query(False, description="Afficher seulement les scores solo"),
        limit: int = Query(50, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Récupère les scores avec filtres optionnels."""

    Player1 = aliased(User, name="p1")
    Player2 = aliased(User, name="p2")

    query = db.query(Score).join(
        Player1, Score.player1_id == Player1.id
    ).outerjoin(  # LEFT JOIN pour player2 (peut être NULL)
        Player2, Score.player2_id == Player2.id
    ).join(
        Game, Score.game_id == Game.id
    ).join(
        Arcade, Score.arcade_id == Arcade.id
    ).filter(
        Score.is_deleted == False
    )

    # Filtrer par jeu si spécifié
    if game_id:
        query = query.filter(Score.game_id == game_id)

    # Filtrer par borne si spécifié
    if arcade_id:
        query = query.filter(Score.arcade_id == arcade_id)

    # Filtrer solo uniquement
    if single_player_only:
        query = query.filter(Score.player2_id.is_(None))

    # Filtrer par amis si demandé
    if friends_only:
        friend_ids = []
        friendships = db.query(Friendship).filter(
            and_(
                or_(
                    Friendship.requester_id == current_user.id,
                    Friendship.requested_id == current_user.id
                ),
                Friendship.status == FriendshipStatus.ACCEPTED,
                Friendship.is_deleted == False
            )
        ).all()

        for friendship in friendships:
            friend_id = friendship.requested_id if friendship.requester_id == current_user.id else friendship.requester_id
            friend_ids.append(friend_id)

        if not friend_ids:
            return []

        # Filtrer les scores où l'utilisateur actuel joue (solo ou contre un ami)
        query = query.filter(
            or_(
                # Scores solo de l'utilisateur
                and_(Score.player1_id == current_user.id, Score.player2_id.is_(None)),
                # Scores multi avec amis
                and_(Score.player1_id == current_user.id, Score.player2_id.in_(friend_ids)),
                and_(Score.player2_id == current_user.id, Score.player1_id.in_(friend_ids))
            )
        )

    scores = query.order_by(Score.created_at.desc()).limit(limit).all()

    result = []
    for score in scores:
        # Récupérer les infos des joueurs
        player1 = db.query(User).filter(User.id == score.player1_id).first()
        player2 = None
        if score.player2_id:
            player2 = db.query(User).filter(User.id == score.player2_id).first()

        game = db.query(Game).filter(Game.id == score.game_id).first()
        arcade = db.query(Arcade).filter(Arcade.id == score.arcade_id).first()

        # Déterminer le gagnant
        winner_pseudo = None
        is_single_player = score.player2_id is None

        if not is_single_player:
            if score.score_j1 > score.score_j2:
                winner_pseudo = player1.pseudo
            elif score.score_j2 > score.score_j1:
                winner_pseudo = player2.pseudo
            else:
                winner_pseudo = "Égalité"

        result.append(ScoreResponse(
            id=score.id,
            player1_pseudo=player1.pseudo,
            player2_pseudo=player2.pseudo if player2 else None,
            game_name=game.nom,
            arcade_name=arcade.nom,
            score_j1=score.score_j1,
            score_j2=score.score_j2,
            winner_pseudo=winner_pseudo,
            is_single_player=is_single_player,
            created_at=score.created_at.isoformat()
        ))

    return result


@router.get("/my-stats")
async def get_my_stats(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Récupère les statistiques personnelles de l'utilisateur."""

    # Compter les parties jouées (solo + multi)
    total_games = db.query(Score).filter(
        or_(
            Score.player1_id == current_user.id,
            Score.player2_id == current_user.id
        ),
        Score.is_deleted == False
    ).count()

    # Compter les parties solo
    solo_games = db.query(Score).filter(
        Score.player1_id == current_user.id,
        Score.player2_id.is_(None),
        Score.is_deleted == False
    ).count()

    # Compter les victoires (seulement pour jeux multi)
    wins = db.query(Score).filter(
        or_(
            and_(Score.player1_id == current_user.id, Score.score_j1 > Score.score_j2),
            and_(Score.player2_id == current_user.id, Score.score_j2 > Score.score_j1)
        ),
        Score.player2_id.isnot(None),  # Seulement jeux multi
        Score.is_deleted == False
    ).count()

    # Compter les défaites (seulement pour jeux multi)
    losses = db.query(Score).filter(
        or_(
            and_(Score.player1_id == current_user.id, Score.score_j1 < Score.score_j2),
            and_(Score.player2_id == current_user.id, Score.score_j2 < Score.score_j1)
        ),
        Score.player2_id.isnot(None),  # Seulement jeux multi
        Score.is_deleted == False
    ).count()

    # Compter les égalités (seulement pour jeux multi)
    multi_games = total_games - solo_games
    draws = multi_games - wins - losses

    win_rate = (wins / multi_games * 100) if multi_games > 0 else 0

    return {
        "total_games": total_games,
        "solo_games": solo_games,
        "multiplayer_games": multi_games,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "win_rate": round(win_rate, 2)
    }