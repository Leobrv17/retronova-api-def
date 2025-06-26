from pydantic import BaseModel, EmailStr, validator
from datetime import date, datetime
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    nom: str
    prenom: str
    pseudo: str
    date_naissance: date
    numero_telephone: str


class UserCreate(UserBase):
    firebase_uid: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    nom: Optional[str] = None
    prenom: Optional[str] = None
    pseudo: Optional[str] = None
    date_naissance: Optional[date] = None
    numero_telephone: Optional[str] = None


class UserResponse(UserBase):
    id: int
    tickets_balance: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserSearchResponse(BaseModel):
    id: int
    pseudo: str
    nom: str
    prenom: str

    class Config:
        from_attributes = True