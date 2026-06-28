import pytest
from app.core.config import Settings
from app.core.errors import RateLimitExceededError
from app.services.rate_limits import (
    AI_ANALYSIS,
    BULK_IMPORT,
    LOGIN,
    REFRESH,
    RateLimitService,
    authenticated_effective_caller,
    login_effective_caller,
)


def _settings() -> Settings:
    """Build test settings with short deterministic rate-limit thresholds."""
    return Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost/test",
        RATE_LIMIT_WINDOW_SECONDS=60,
        RATE_LIMIT_LOGIN_ATTEMPTS=2,
        RATE_LIMIT_REFRESH_ATTEMPTS=3,
        RATE_LIMIT_BULK_IMPORT_ATTEMPTS=3,
        RATE_LIMIT_AI_ANALYSIS_ATTEMPTS=2,
    )


@pytest.mark.asyncio
async def test_rate_limit_thresholds_and_retry_metadata() -> None:
    """Verify fixed-window counters reject the first request over threshold."""
    service = RateLimitService(_settings())

    await service.check(LOGIN, "rate-limit-unit")
    await service.check(LOGIN, "rate-limit-unit")

    with pytest.raises(RateLimitExceededError) as exc:
        await service.check(LOGIN, "rate-limit-unit")

    error = exc.value.detail["error"]
    assert error["code"] == "rate_limited"
    assert error["details"]["operation"] == LOGIN
    assert error["details"]["retry_after_seconds"] > 0


def test_rate_limit_rules_and_trusted_callers() -> None:
    """Verify configured operation policies and caller key construction."""
    service = RateLimitService(_settings())

    assert service.rule_for(LOGIN).limit == 2
    assert service.rule_for(REFRESH).limit == 3
    assert service.rule_for(BULK_IMPORT).limit == 3
    assert service.rule_for(AI_ANALYSIS).limit == 2
    assert login_effective_caller(" Admin@Example.COM ", "127.0.0.1") == (
        "admin@example.com:127.0.0.1"
    )
    assert authenticated_effective_caller("user-id", "org-id") == "user-id:org-id"
