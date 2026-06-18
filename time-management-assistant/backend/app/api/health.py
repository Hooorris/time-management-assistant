from fastapi import APIRouter

from app.config import get_settings
from app.database import check_database_connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "timezone": settings.app_timezone,
    }


@router.get("/health/db")
def database_health_check() -> dict[str, str]:
    return check_database_connection()
