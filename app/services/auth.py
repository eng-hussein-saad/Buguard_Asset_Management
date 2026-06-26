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
    verify_refresh_token,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories import auth as auth_repository


def _make_raw_refresh_token() -> str:
    return secrets.token_urlsafe(48)


async def issue_token_pair(
    session: AsyncSession, user: User, settings: Settings | None = None
) -> tuple[str, str]:
    active_settings = settings or get_settings()
    raw_refresh_token = _make_raw_refresh_token()
    expires_at = datetime.now(UTC) + timedelta(
        days=active_settings.refresh_token_expire_days
    )
    await auth_repository.create_refresh_token_record(
        session,
        user.id,
        hash_refresh_token(raw_refresh_token),
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
    user = await auth_repository.get_active_user_by_email(session, email)
    if user is None or not verify_password(password, user.password_hash):
        raise AuthenticationError()

    access_token, refresh_token = await issue_token_pair(session, user)
    await session.commit()
    return user, access_token, refresh_token


async def _find_refresh_record(
    session: AsyncSession, raw_refresh_token: str
) -> RefreshToken | None:
    for candidate in await auth_repository.list_unrevoked_refresh_tokens(session):
        if verify_refresh_token(raw_refresh_token, candidate.token_hash):
            return candidate
    return None


async def refresh_session(
    session: AsyncSession, raw_refresh_token: str
) -> tuple[User, str, str]:
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
    token = await _find_refresh_record(session, raw_refresh_token)
    if token is None:
        raise AuthenticationError()

    await auth_repository.revoke_refresh_token(session, token)
    await session.commit()
