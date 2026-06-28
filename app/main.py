from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes.assets import relationships_router
from app.api.routes.assets import router as assets_router
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.core.config import Settings, get_settings
from app.core.errors import AppError


async def app_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Render AppError details as the top-level structured error envelope."""
    assert isinstance(exc, AppError)
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


async def validation_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Render request validation errors in the project error envelope."""
    assert isinstance(exc, RequestValidationError)
    details = {
        "errors": [
            {
                "loc": list(error["loc"]),
                "msg": str(error["msg"]),
                "type": str(error["type"]),
            }
            for error in exc.errors()
        ]
    }
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request validation failed.",
                "details": details,
            }
        },
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application instance."""
    active_settings = settings or get_settings()
    application = FastAPI(
        title=active_settings.app_name,
        version="0.1.0",
        description="Buguard Asset Management API.",
    )
    application.add_exception_handler(AppError, app_error_handler)
    application.add_exception_handler(RequestValidationError, validation_error_handler)
    application.include_router(auth_router)
    application.include_router(assets_router)
    application.include_router(relationships_router)
    application.include_router(health_router)
    return application


app = create_app()

