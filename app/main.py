from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.core.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or get_settings()
    application = FastAPI(
        title=active_settings.app_name,
        version="0.1.0",
        description="Buguard Asset Management API.",
    )
    application.include_router(auth_router)
    application.include_router(health_router)
    return application


app = create_app()

