from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_admin
from app.services.admin.stats_service import StatsService

router = APIRouter()


@router.get("/")
async def get_admin_stats(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Récupère les statistiques globales de la plateforme."""
    service = StatsService(db)
    return await service.get_global_stats()