from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.users import get_by_email


async def get_active_user_by_email(session: AsyncSession, email: str) -> User | None:
    user = await get_by_email(session, email)
    if user is None or not user.is_active:
        return None
    return user


async def create_refresh_token_record(
    session: AsyncSession, user_id: UUID, token_hash: str, expires_at: datetime
) -> RefreshToken:
    token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        revoked_at=None,
    )
    session.add(token)
    await session.flush()
    return token


async def get_unrevoked_refresh_token_by_hash(
    session: AsyncSession, token_hash: str
) -> RefreshToken | None:
    """Return one unrevoked refresh token by its indexed digest."""
    return cast(
        RefreshToken | None,
        await session.scalar(
            select(RefreshToken)
            .options(selectinload(RefreshToken.user))
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
        ),
    )


async def revoke_refresh_token(session: AsyncSession, token: RefreshToken) -> None:
    token.revoked_at = datetime.now(UTC)
    session.add(token)
    await session.flush()
