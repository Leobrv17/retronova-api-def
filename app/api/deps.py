from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Annotated
from app.core.database import get_db
from app.core.security import verify_firebase_token, verify_arcade_api_key
from app.models.user import User

security = HTTPBearer()


def get_current_user(
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Dependency pour obtenir l'utilisateur actuel via Firebase."""
    print(credentials.credentials)
    token_data = verify_firebase_token(credentials.credentials, "user")
    print(">>>",token_data)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Firebase invalide"
        )

    # Recherche l'utilisateur en base
    user = db.query(User).filter(
        User.firebase_uid == token_data["uid"],
        User.is_deleted == False
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    return user


def get_current_admin(
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Dependency pour obtenir l'admin actuel via Firebase Admin."""
    token_data = verify_firebase_token(credentials.credentials, "admin")
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Firebase admin invalide"
        )

    return token_data


def verify_arcade_key(
        x_api_key: Annotated[str, Header()] = None
) -> bool:
    """Dependency pour vérifier la clé API des bornes."""
    if not x_api_key or not verify_arcade_api_key(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API borne invalide"
        )
    return True


def get_optional_user(
        db: Session = Depends(get_db),
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Dependency pour obtenir l'utilisateur actuel optionnel."""
    if not credentials:
        return None

    token_data = verify_firebase_token(credentials.credentials, "user")
    if not token_data:
        return None

    return db.query(User).filter(
        User.firebase_uid == token_data["uid"],
        User.is_deleted == False
    ).first()