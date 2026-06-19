from fastapi import FastAPI

from app.api import health_router, reminders_router, summary_router, tasks_router
from app.api.errors import register_error_handlers
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Backend service for the Time Management Assistant.",
    )
    register_error_handlers(app)
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(tasks_router, prefix=settings.api_prefix)
    app.include_router(summary_router, prefix=settings.api_prefix)
    app.include_router(reminders_router, prefix=settings.api_prefix)
    return app


app = create_app()
