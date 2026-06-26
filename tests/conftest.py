import os
from collections.abc import Iterator

import pytest
from fastapi import FastAPI

# Force tests to use the test database and reset cached settings.
@pytest.fixture(autouse=True)
def database_url_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/buguard_test",
    )

    from app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# Provide a reusable FastAPI app instance for API tests.
@pytest.fixture
def app_instance() -> FastAPI:
    from app.main import create_app

    return create_app()


# Prevent tests from loading settings from an unexpected env file.
@pytest.fixture(autouse=True)
def avoid_env_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYDANTIC_SETTINGS_ENV_FILE", raising=False)
    os.environ.pop("PYDANTIC_SETTINGS_ENV_FILE", None)

