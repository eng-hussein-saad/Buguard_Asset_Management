from functools import lru_cache

from pydantic import Field, PostgresDsn, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.errors import ConfigurationError


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Buguard Asset Management API"
    database_url: PostgresDsn = Field(alias="DATABASE_URL")
    jwt_secret_key: str = Field(
        default="change-me-in-local-dev", alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES", ge=1
    )
    refresh_token_expire_days: int = Field(
        default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS", ge=1
    )
    cache_url: str | None = Field(default=None, alias="CACHE_URL")
    cache_ttl_seconds: int = Field(default=300, alias="CACHE_TTL_SECONDS", ge=1)
    rate_limit_window_seconds: int = Field(
        default=60, alias="RATE_LIMIT_WINDOW_SECONDS", ge=1
    )
    rate_limit_login_attempts: int = Field(
        default=5, alias="RATE_LIMIT_LOGIN_ATTEMPTS", ge=1
    )
    rate_limit_refresh_attempts: int = Field(
        default=10, alias="RATE_LIMIT_REFRESH_ATTEMPTS", ge=1
    )
    rate_limit_bulk_import_attempts: int = Field(
        default=10, alias="RATE_LIMIT_BULK_IMPORT_ATTEMPTS", ge=1
    )
    rate_limit_ai_analysis_attempts: int = Field(
        default=5, alias="RATE_LIMIT_AI_ANALYSIS_ATTEMPTS", ge=1
    )


def _sanitize_settings_error(error: ValidationError) -> str:
    """Return a configuration error that does not expose secret values."""
    missing_database_url = any(
        tuple(detail.get("loc", ())) == ("DATABASE_URL",)
        and detail.get("type") == "missing"
        for detail in error.errors()
    )
    if missing_database_url:
        return "DATABASE_URL is required. Set it in the environment or .env file."

    return "DATABASE_URL is invalid. Use a PostgreSQL connection URL."


@lru_cache
def get_settings() -> Settings:
    """Load and cache validated application settings."""
    try:
        return Settings()
    except ValidationError as exc:
        raise ConfigurationError(_sanitize_settings_error(exc)) from None
