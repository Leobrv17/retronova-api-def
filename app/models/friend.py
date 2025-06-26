from sqlalchemy import Column, Integer, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum


class FriendshipStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Friendship(BaseModel):
    __tablename__ = "friendships"

    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    requested_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(FriendshipStatus), default=FriendshipStatus.PENDING)

    # Relations
    requester = relationship("User", foreign_keys=[requester_id], back_populates="sent_friend_requests")
    requested = relationship("User", foreign_keys=[requested_id], back_populates="received_friend_requests")

