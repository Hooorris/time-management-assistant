from app.api.health import router as health_router
from app.api.reminders import router as reminders_router
from app.api.summary import router as summary_router
from app.api.tasks import router as tasks_router

__all__ = [
    "health_router",
    "reminders_router",
    "summary_router",
    "tasks_router",
]
