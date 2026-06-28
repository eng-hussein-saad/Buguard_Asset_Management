from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import AuthenticationError
from app.core.security import decode_access_token
from app.db.session import get_async_session
from app.models.user import User
from app.repositories.users import get_by_id
from app.services.cache import CacheService
from app.services.rate_limits import RateLimitService
from app.services.rbac import Permission, require_permission

bearer_scheme = HTTPBearer(auto_error=False)
_cache_client: Any | None = None


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield one async database session for request-scoped work."""
    async for session in get_async_session():
        yield session


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Resolve the active user from a bearer access token."""
    if credentials is None:
        raise AuthenticationError()

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise AuthenticationError()

    try:
        user_id = UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise AuthenticationError() from exc

    user = await get_by_id(session, user_id)
    if user is None or not user.is_active:
        raise AuthenticationError()

    if (
        str(user.organization_id) != payload["organization_id"]
        or user.role != payload["role"]
    ):
        raise AuthenticationError()
    return user


def require_role_permission(
    permission: Permission,
) -> Callable[[User], Coroutine[Any, Any, User]]:
    """Build a dependency that enforces one RBAC permission."""
    async def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        """Return the current user after permission validation."""
        require_permission(current_user.role, permission)
        return current_user

    return dependency


async def get_cache_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Any | None:
    """Return an optional Redis-compatible client without requiring startup."""
    global _cache_client
    if settings.cache_url is None:
        return None
    if _cache_client is None:
        try:
            from redis.asyncio import from_url

            _cache_client = from_url(settings.cache_url, decode_responses=True)
        except Exception:
            return None
    return _cache_client


async def get_cache_service(
    settings: Annotated[Settings, Depends(get_settings)],
    cache_client: Annotated[Any | None, Depends(get_cache_client)],
) -> CacheService:
    """Create the request cache helper with optional external storage."""
    return CacheService(settings, cache_client)


async def get_rate_limiter(
    settings: Annotated[Settings, Depends(get_settings)],
    cache_client: Annotated[Any | None, Depends(get_cache_client)],
) -> RateLimitService:
    """Create the request rate-limit helper with optional external storage."""
    return RateLimitService(settings, cache_client)
