from functools import lru_cache

from pydantic import Field, PostgresDsn, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.errors import ConfigurationError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Buguard Asset Management API"
    database_url: PostgresDsn = Field(alias="DATABASE_URL")


def _sanitize_settings_error(error: ValidationError) -> str:
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
    try:
        return Settings()
    except ValidationError as exc:
        raise ConfigurationError(_sanitize_settings_error(exc)) from None

