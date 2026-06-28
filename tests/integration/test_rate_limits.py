from uuid import uuid4

import pytest
from app.api.deps import get_current_user, get_db, get_rate_limiter
from app.core.config import Settings
from app.models.user import User
from app.schemas.analysis import AnalysisReportResponse
from app.schemas.assets import AssetImportSummary
from app.services import analysis, tenant_assets
from app.services import auth as auth_service
from app.services.rate_limits import RateLimitService
from httpx import ASGITransport, AsyncClient


class DummySession:
    """Minimal route-test session for rate-limit integration checks."""


def _settings() -> Settings:
    """Build low-threshold settings for integration rate-limit tests."""
    return Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost/test",
        RATE_LIMIT_LOGIN_ATTEMPTS=2,
        RATE_LIMIT_REFRESH_ATTEMPTS=2,
        RATE_LIMIT_BULK_IMPORT_ATTEMPTS=2,
        RATE_LIMIT_AI_ANALYSIS_ATTEMPTS=2,
    )


async def _client(app_instance, user: User | None = None):
    """Create an ASGI client with deterministic dependencies overridden."""
    limiter = RateLimitService(_settings())
    app_instance.dependency_overrides[get_db] = lambda: DummySession()
    app_instance.dependency_overrides[get_rate_limiter] = lambda: limiter
    if user is not None:
        app_instance.dependency_overrides[get_current_user] = lambda: user
    return AsyncClient(
        transport=ASGITransport(app=app_instance), base_url="http://testserver"
    )


@pytest.mark.asyncio
async def test_login_attempt_over_threshold_returns_structured_429(
    app_instance, demo_user, monkeypatch
) -> None:
    """Verify the third same-caller login attempt is rate limited."""

    async def fake_authenticate(session, email, password):
        return demo_user, "access-token", "refresh-token"

    monkeypatch.setattr(auth_service, "authenticate", fake_authenticate)

    async with await _client(app_instance) as client:
        for _ in range(2):
            response = await client.post(
                "/auth/login",
                json={"email": "admin@example.com", "password": "password123"},
            )
            assert response.status_code == 200
        limited = await client.post(
            "/auth/login",
            json={"email": "admin@example.com", "password": "password123"},
        )

    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "rate_limited"
    assert limited.json()["error"]["details"]["operation"] == "login"


@pytest.mark.asyncio
async def test_refresh_attempt_over_threshold_returns_structured_429(
    app_instance, demo_user, monkeypatch
) -> None:
    """Verify refresh limits use the refresh-token user and organization."""

    async def fake_refresh_user(session, raw_refresh_token):
        return demo_user

    async def fake_refresh_session(session, raw_refresh_token):
        return demo_user, f"access-{uuid4()}", f"refresh-{uuid4()}"

    monkeypatch.setattr(auth_service, "refresh_token_user", fake_refresh_user)
    monkeypatch.setattr(auth_service, "refresh_session", fake_refresh_session)

    async with await _client(app_instance) as client:
        for _ in range(2):
            response = await client.post(
                "/auth/refresh", json={"refresh_token": "valid-refresh"}
            )
            assert response.status_code == 200
        limited = await client.post(
            "/auth/refresh", json={"refresh_token": "valid-refresh"}
        )

    assert limited.status_code == 429
    assert limited.json()["error"]["details"]["operation"] == "refresh"


@pytest.mark.asyncio
async def test_bulk_import_rate_limit_runs_after_rbac(
    app_instance, demo_user, viewer_user, import_payload_factory, monkeypatch
) -> None:
    """Verify imports are limited for writers while viewers remain forbidden."""
    calls = 0

    async def fake_import(session, current_user, payload, cache_service=None):
        nonlocal calls
        calls += 1
        return AssetImportSummary(created=1, updated=0, failed=0, errors=[])

    monkeypatch.setattr(tenant_assets, "import_assets", fake_import)

    async with await _client(app_instance, demo_user) as client:
        for _ in range(2):
            response = await client.post(
                "/assets/import", json=import_payload_factory()
            )
            assert response.status_code == 200
        limited = await client.post("/assets/import", json=import_payload_factory())

    assert limited.status_code == 429
    assert calls == 2

    async with await _client(app_instance, viewer_user) as client:
        forbidden = await client.post("/assets/import", json=import_payload_factory())

    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_analysis_report_rate_limit_returns_structured_429(
    app_instance, demo_user, monkeypatch
) -> None:
    """Verify analysis reports use the documented AI analysis limit."""
    calls = 0

    async def fake_generate_report(session, current_user, payload, provider):
        nonlocal calls
        calls += 1
        return AnalysisReportResponse(
            summary="ok",
            risks=[],
            evidence=[],
            status="completed",
        )

    monkeypatch.setattr(analysis, "generate_report", fake_generate_report)

    async with await _client(app_instance, demo_user) as client:
        for _ in range(2):
            response = await client.post("/analysis/report", json={"limit": 1})
            assert response.status_code == 200
        limited = await client.post("/analysis/report", json={"limit": 1})

    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "rate_limited"
    assert limited.json()["error"]["details"]["operation"] == "ai_analysis"
    assert calls == 2
