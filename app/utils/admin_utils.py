from datetime import datetime
from typing import Optional
from .exceptions import AdminException


def validate_slot_number(slot_number: int):
    """Valide qu'un numéro de slot est valide."""
    if slot_number not in [1, 2]:
        raise AdminException("Le slot doit être 1 ou 2", 400)


def validate_promo_dates(valid_from: Optional[datetime], valid_until: Optional[datetime]):
    """Valide les dates d'un code promo."""
    if valid_from and valid_until and valid_until <= valid_from:
        raise AdminException(
            "La date d'expiration doit être après la date de début",
            400
        )


def generate_success_message(action: str, entity: str, name: str) -> str:
    """Génère un message de succès standardisé."""
    return f"{entity} '{name}' {action} avec succès"


def format_api_key_for_display(api_key: str, show_chars: int = 20) -> str:
    """Formate une clé API pour l'affichage (masque partiellement)."""
    if len(api_key) <= show_chars:
        return api_key
    return api_key[:show_chars] + "..."


def calculate_success_rate(successes: int, total: int) -> float:
    """Calcule un taux de succès en pourcentage."""
    if total == 0:
        return 0.0
    return round((successes / total) * 100, 2)