import pytest
from app.core.config import Settings, get_settings
from app.core.errors import ConfigurationError


# Verify that the app fails clearly when DATABASE_URL is missing.
# The error should be user-friendly and should not expose raw Pydantic details.
def test_missing_database_url_fails_with_sanitized_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()

    with pytest.raises(ConfigurationError) as exc_info:
        get_settings()

    assert str(exc_info.value) == (
        "DATABASE_URL is required. Set it in the environment or .env file."
    )


# Verify that the app fails clearly when DATABASE_URL has an invalid format.
# The error should be sanitized and should not leak the invalid value.
def test_malformed_database_url_fails_with_sanitized_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "not-a-database-url")
    get_settings.cache_clear()

    with pytest.raises(ConfigurationError) as exc_info:
        get_settings()

    assert str(exc_info.value) == (
        "DATABASE_URL is invalid. Use a PostgreSQL connection URL."
    )
    assert "not-a-database-url" not in str(exc_info.value)


# Verify that the Settings model accepts the async PostgreSQL URL format.
def test_settings_accept_postgresql_asyncpg_url() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/buguard"
    )

    assert str(settings.database_url).startswith("postgresql+asyncpg://")
