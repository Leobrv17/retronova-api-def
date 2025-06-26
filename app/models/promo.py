from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel


class PromoCode(BaseModel):
    __tablename__ = "promo_codes"

    code = Column(String, unique=True, nullable=False)
    tickets_reward = Column(Integer, nullable=False)
    is_single_use_global = Column(Boolean, default=False)
    is_single_use_per_user = Column(Boolean, default=True)
    usage_limit = Column(Integer, nullable=True)  # Limite globale optionnelle
    current_uses = Column(Integer, default=0)

    # Relations
    promo_uses = relationship("PromoUse", back_populates="promo_code")


class PromoUse(BaseModel):
    __tablename__ = "promo_uses"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    promo_code_id = Column(Integer, ForeignKey("promo_codes.id"), nullable=False)
    tickets_received = Column(Integer, nullable=False)

    # Relations
    user = relationship("User", back_populates="promo_uses")
    promo_code = relationship("PromoCode", back_populates="promo_uses")