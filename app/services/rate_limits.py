from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Final

from app.core.config import Settings
from app.core.errors import RateLimitExceededError

LOGIN: Final = "login"
REFRESH: Final = "refresh"
BULK_IMPORT: Final = "bulk_import"
AI_ANALYSIS: Final = "ai_analysis"

_MEMORY_COUNTERS: dict[str, tuple[int, int]] = {}


@dataclass(frozen=True)
class RateLimitRule:
    """Defines a fixed-window threshold for one protected operation."""

    operation: str
    limit: int
    window_seconds: int


class RateLimitService:
    """Checks fixed-window operation limits against cache or memory state."""

    def __init__(self, settings: Settings, store: Any | None = None) -> None:
        """Create a rate limiter using an optional Redis-compatible store."""
        self.settings = settings
        self.store = store

    def rule_for(self, operation: str) -> RateLimitRule:
        """Return the configured rule for a supported operation."""
        limits = {
            LOGIN: self.settings.rate_limit_login_attempts,
            REFRESH: self.settings.rate_limit_refresh_attempts,
            BULK_IMPORT: self.settings.rate_limit_bulk_import_attempts,
            AI_ANALYSIS: self.settings.rate_limit_ai_analysis_attempts,
        }
        return RateLimitRule(
            operation=operation,
            limit=limits[operation],
            window_seconds=self.settings.rate_limit_window_seconds,
        )

    def key_for(self, operation: str, effective_caller: str) -> str:
        """Build a storage key from trusted route-provided caller identity."""
        return f"rate-limit:{operation}:{effective_caller}"

    async def check(self, operation: str, effective_caller: str) -> None:
        """Record one attempt and raise a structured error when over limit."""
        rule = self.rule_for(operation)
        key = self.key_for(operation, effective_caller)
        count, retry_after = await self._increment(key, rule.window_seconds)
        if count > rule.limit:
            raise RateLimitExceededError(operation, retry_after)

    async def _increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        """Increment a counter using Redis when available, otherwise memory."""
        if self.store is not None:
            try:
                count = await self.store.incr(key)
                if count == 1:
                    await self.store.expire(key, window_seconds)
                ttl = await self.store.ttl(key)
                retry_after = (
                    ttl if isinstance(ttl, int) and ttl > 0 else window_seconds
                )
                return int(count), retry_after
            except Exception:
                pass

        now = int(time.time())
        count, reset_at = _MEMORY_COUNTERS.get(key, (0, now + window_seconds))
        if reset_at <= now:
            count = 0
            reset_at = now + window_seconds
        count += 1
        _MEMORY_COUNTERS[key] = (count, reset_at)
        return count, max(reset_at - now, 1)


def login_effective_caller(username: str, client_host: str | None) -> str:
    """Build the login caller key from attempted username and client network."""
    return f"{username.strip().lower()}:{client_host or 'unknown'}"


def authenticated_effective_caller(user_id: object, organization_id: object) -> str:
    """Build the trusted authenticated caller key for tenant-owned operations."""
    return f"{user_id}:{organization_id}"
