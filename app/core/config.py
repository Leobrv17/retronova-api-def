from pydantic_settings import BaseSettings
from typing import Optional
import json
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Arcade API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str

    # Firebase
    FIREBASE_USER_PROJECT_ID: str
    FIREBASE_ADMIN_PROJECT_ID: str
    FIREBASE_USER_CREDENTIALS: str  # JSON string
    FIREBASE_ADMIN_CREDENTIALS: str  # JSON string

    # Arcade API Key
    ARCADE_API_KEY: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def firebase_user_credentials_dict(self) -> dict:
        return json.loads(self.FIREBASE_USER_CREDENTIALS)

    @property
    def firebase_admin_credentials_dict(self) -> dict:
        return json.loads(self.FIREBASE_ADMIN_CREDENTIALS)


settings = Settings()