from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


def normalize_email(email: str) -> str:
    return email.strip().lower()


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    return cast(
        User | None,
        await session.scalar(
        select(User).where(User.email == normalize_email(email))
        ),
    )


async def get_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    return await session.get(User, user_id)


async def get_or_create(
    session: AsyncSession,
    organization_id: UUID,
    email: str,
    password_hash: str,
    role: str,
) -> User:
    user = await get_by_email(session, email)
    if user is not None:
        return user

    user = User(
        organization_id=organization_id,
        email=normalize_email(email),
        password_hash=password_hash,
        role=role,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return user
