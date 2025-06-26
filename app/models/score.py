from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel


class Score(BaseModel):
    __tablename__ = "scores"

    player1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    arcade_id = Column(Integer, ForeignKey("arcades.id"), nullable=False)
    score_j1 = Column(Integer, nullable=False)
    score_j2 = Column(Integer, nullable=False)

    # Relations
    player1 = relationship("User", foreign_keys=[player1_id], back_populates="scores_player1")
    player2 = relationship("User", foreign_keys=[player2_id], back_populates="scores_player2")
    game = relationship("Game", back_populates="scores")
    arcade = relationship("Arcade", back_populates="scores")
