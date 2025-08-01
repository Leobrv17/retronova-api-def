from sqlalchemy import Column, String, Date, Integer
from sqlalchemy.orm import relationship
from .base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    firebase_uid = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    pseudo = Column(String, unique=True, index=True, nullable=False)
    date_naissance = Column(Date, nullable=False)
    numero_telephone = Column(String, unique=True, nullable=False)
    tickets_balance = Column(Integer, default=0, nullable=False)

    # Relations avec spécification explicite des foreign_keys
    sent_friend_requests = relationship(
        "Friendship",
        foreign_keys="Friendship.requester_id",
        back_populates="requester"
    )
    received_friend_requests = relationship(
        "Friendship",
        foreign_keys="Friendship.requested_id",
        back_populates="requested"
    )

    # CORRECTION: Spécifier explicitement foreign_keys pour éviter l'ambiguïté
    reservations = relationship(
        "Reservation",
        foreign_keys="Reservation.player_id",
        back_populates="player"
    )

    # Relations pour les scores avec foreign_keys explicites
    scores_player1 = relationship(
        "Score",
        foreign_keys="Score.player1_id",
        back_populates="player1"
    )
    scores_player2 = relationship(
        "Score",
        foreign_keys="Score.player2_id",
        back_populates="player2"
    )

    # Relations simples (pas d'ambiguïté)
    ticket_purchases = relationship("TicketPurchase", back_populates="user")
    promo_uses = relationship("PromoUse", back_populates="user")