from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import AuthenticationError
from app.core.security import (
    create_access_token,
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories import auth as auth_repository


def _make_raw_refresh_token() -> str:
    """Create an opaque refresh token safe for client storage."""
    return secrets.token_urlsafe(48)


async def issue_token_pair(
    session: AsyncSession, user: User, settings: Settings | None = None
) -> tuple[str, str]:
    """Persist a refresh token and return a matching access token pair."""
    active_settings = settings or get_settings()
    raw_refresh_token = _make_raw_refresh_token()
    expires_at = datetime.now(UTC) + timedelta(
        days=active_settings.refresh_token_expire_days
    )
    await auth_repository.create_refresh_token_record(
        session,
        user.id,
        hash_refresh_token(raw_refresh_token, active_settings),
        expires_at,
    )
    access_token = create_access_token(
        user.id,
        user.organization_id,
        user.role,
        active_settings,
    )
    return access_token, raw_refresh_token


async def authenticate(
    session: AsyncSession, email: str, password: str
) -> tuple[User, str, str]:
    """Authenticate credentials and issue a committed token pair."""
    user = await auth_repository.get_active_user_by_email(session, email)
    if user is None or not verify_password(password, user.password_hash):
        raise AuthenticationError()

    access_token, refresh_token = await issue_token_pair(session, user)
    await session.commit()
    return user, access_token, refresh_token


async def _find_refresh_record(
    session: AsyncSession, raw_refresh_token: str
) -> RefreshToken | None:
    """Find an unrevoked refresh-token record by its keyed digest."""
    token_hash = hash_refresh_token(raw_refresh_token)
    return await auth_repository.get_unrevoked_refresh_token_by_hash(
        session, token_hash
    )


async def refresh_token_user(session: AsyncSession, raw_refresh_token: str) -> User:
    """Return the active user for a usable refresh token without rotating it."""
    token = await _find_refresh_record(session, raw_refresh_token)
    now = datetime.now(UTC)
    if token is None or token.expires_at <= now or not token.user.is_active:
        raise AuthenticationError()
    return token.user


async def refresh_session(
    session: AsyncSession, raw_refresh_token: str
) -> tuple[User, str, str]:
    """Rotate one refresh token and issue a committed replacement pair."""
    token = await _find_refresh_record(session, raw_refresh_token)
    now = datetime.now(UTC)
    if token is None or token.expires_at <= now:
        raise AuthenticationError()

    user = token.user
    if not user.is_active:
        raise AuthenticationError()

    await auth_repository.revoke_refresh_token(session, token)
    access_token, replacement_refresh_token = await issue_token_pair(session, user)
    await session.commit()
    return user, access_token, replacement_refresh_token


async def logout(session: AsyncSession, raw_refresh_token: str) -> None:
    """Revoke a refresh token if it is currently known."""
    token = await _find_refresh_record(session, raw_refresh_token)
    if token is None:
        raise AuthenticationError()

    await auth_repository.revoke_refresh_token(session, token)
    await session.commit()
