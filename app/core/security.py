import firebase_admin
from firebase_admin import credentials, auth
from .config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Firebase Apps
firebase_user_app = None
firebase_admin_app = None


def init_firebase():
    """Initialise les applications Firebase."""
    global firebase_user_app, firebase_admin_app

    try:
        # App pour les utilisateurs finaux
        user_cred = credentials.Certificate(settings.firebase_user_credentials_dict)
        firebase_user_app = firebase_admin.initialize_app(
            user_cred,
            name="user_app"
        )

        # App pour les administrateurs
        admin_cred = credentials.Certificate(settings.firebase_admin_credentials_dict)
        firebase_admin_app = firebase_admin.initialize_app(
            admin_cred,
            name="admin_app"
        )

        logger.info("Firebase applications initialized successfully")
    except Exception as e:
        logger.error(f"Firebase initialization failed: {e}")
        raise


def verify_firebase_token(token: str, app_type: str = "user") -> Optional[dict]:
    """
    Vérifie un token Firebase et retourne les informations utilisateur.

    Args:
        token: Token Firebase
        app_type: "user" ou "admin"

    Returns:
        Dict contenant les infos utilisateur ou None si invalide
    """
    try:
        app = firebase_user_app if app_type == "user" else firebase_admin_app
        decoded_token = auth.verify_id_token(token, app=app)
        return {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email"),
            "email_verified": decoded_token.get("email_verified", False)
        }
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        return None


def verify_arcade_api_key(api_key: str) -> bool:
    """Vérifie la clé API des bornes d'arcade."""
    return api_key == settings.ARCADE_API_KEY