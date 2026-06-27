import os
from collections.abc import Iterator
from datetime import UTC, datetime
from uuid import uuid4

import app.db.base  # noqa: F401
import pytest
from app.models.asset import Asset
from app.models.user import User
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


@pytest.fixture
def demo_user() -> User:
    """Return an active analyst in the default test organization."""
    return User(
        id=uuid4(),
        organization_id=uuid4(),
        email="analyst@example.com",
        password_hash="hash",
        role="analyst",
        is_active=True,
    )


@pytest.fixture
def viewer_user(demo_user: User) -> User:
    """Return an active viewer in the default test organization."""
    return User(
        id=uuid4(),
        organization_id=demo_user.organization_id,
        email="viewer@example.com",
        password_hash="hash",
        role="viewer",
        is_active=True,
    )


@pytest.fixture
def admin_user(demo_user: User) -> User:
    """Return an active admin in the default test organization."""
    return User(
        id=uuid4(),
        organization_id=demo_user.organization_id,
        email="admin@example.com",
        password_hash="hash",
        role="admin",
        is_active=True,
    )


def build_asset(
    organization_id,
    asset_type: str = "domain",
    value: str = "example.com",
    status: str = "active",
    tags: list[str] | None = None,
    source: str | None = "manual",
) -> Asset:
    """Build an Asset model with timestamps for service and API tests."""
    now = datetime(2026, 6, 27, tzinfo=UTC)
    return Asset(
        id=uuid4(),
        organization_id=organization_id,
        type=asset_type,
        value=value,
        status=status,
        first_seen=now,
        last_seen=now,
        source=source,
        tags=tags or [],
        asset_metadata={},
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def asset_factory():
    """Return a small factory for tenant-scoped asset model instances."""
    return build_asset

