from sqlalchemy import Column, Integer, ForeignKey, String, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum


class ReservationStatus(str, enum.Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Reservation(BaseModel):
    __tablename__ = "reservations"

    player_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player2_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    arcade_id = Column(Integer, ForeignKey("arcades.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    unlock_code = Column(String(1), nullable=False)  # 1-8
    status = Column(Enum(ReservationStatus), default=ReservationStatus.WAITING)
    tickets_used = Column(Integer, nullable=False)

    # Relations avec foreign_keys explicites pour éviter l'ambiguïté
    player = relationship(
        "User",
        foreign_keys=[player_id],
        back_populates="reservations"
    )
    player2 = relationship(
        "User",
        foreign_keys=[player2_id]
        # Pas de back_populates pour player2 car c'est optionnel
    )

    # Relations simples (pas d'ambiguïté)
    arcade = relationship("Arcade", back_populates="reservations")
    game = relationship("Game", back_populates="reservations")