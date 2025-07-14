from fastapi import APIRouter
from .admin import arcades, games, promo_codes, users, stats

router = APIRouter()

# Inclusion des sous-modules
router.include_router(arcades.router, prefix="/arcades", tags=["admin-arcades"])
router.include_router(games.router, prefix="/games", tags=["admin-games"])
router.include_router(promo_codes.router, prefix="/promo-codes", tags=["admin-promos"])
router.include_router(users.router, prefix="/users", tags=["admin-users"])
router.include_router(stats.router, prefix="/stats", tags=["admin-stats"])