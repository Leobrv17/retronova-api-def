# app/api/v1/admin/__init__.py (version mise à jour)

"""
Module admin pour les endpoints d'administration de l'API Arcade.

Ce module contient tous les endpoints réservés aux administrateurs,
organisés par domaine fonctionnel.
"""

__version__ = "1.0.0"
__author__ = "Retronova Team"

# Imports des sous-modules (à utiliser quand l'architecture modulaire sera complètement implémentée)
try:
    from . import arcades
    ARCADES_MODULE_AVAILABLE = True
except ImportError:
    ARCADES_MODULE_AVAILABLE = False

try:
    from . import games
    GAMES_MODULE_AVAILABLE = True
except ImportError:
    GAMES_MODULE_AVAILABLE = False

try:
    from . import promo_codes
    PROMO_CODES_MODULE_AVAILABLE = True
except ImportError:
    PROMO_CODES_MODULE_AVAILABLE = False

try:
    from . import users
    USERS_MODULE_AVAILABLE = True
except ImportError:
    USERS_MODULE_AVAILABLE = False

try:
    from . import stats
    STATS_MODULE_AVAILABLE = True
except ImportError:
    STATS_MODULE_AVAILABLE = False

# Export conditionnel basé sur la disponibilité des modules
__all__ = []

if ARCADES_MODULE_AVAILABLE:
    __all__.append("arcades")

if GAMES_MODULE_AVAILABLE:
    __all__.append("games")

if PROMO_CODES_MODULE_AVAILABLE:
    __all__.append("promo_codes")

if USERS_MODULE_AVAILABLE:
    __all__.append("users")

if STATS_MODULE_AVAILABLE:
    __all__.append("stats")

# Informations de disponibilité des modules
MODULE_STATUS = {
    "arcades": ARCADES_MODULE_AVAILABLE,
    "games": GAMES_MODULE_AVAILABLE,
    "promo_codes": PROMO_CODES_MODULE_AVAILABLE,
    "users": USERS_MODULE_AVAILABLE,
    "stats": STATS_MODULE_AVAILABLE
}

def get_available_modules():
    """Retourne la liste des modules admin disponibles."""
    return [module for module, available in MODULE_STATUS.items() if available]

def is_module_available(module_name: str) -> bool:
    """Vérifie si un module admin spécifique est disponible."""
    return MODULE_STATUS.get(module_name, False)