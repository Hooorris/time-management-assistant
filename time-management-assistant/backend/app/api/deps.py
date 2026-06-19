from typing import Optional

from sqlalchemy.orm import Session

from app.config import get_settings
from app.services import TaskService


def get_task_service(db: Session, *, timezone_name: Optional[str] = None) -> TaskService:
    settings = get_settings()
    return TaskService(db, timezone_name=timezone_name or settings.app_timezone)
