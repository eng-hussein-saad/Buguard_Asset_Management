from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization


async def get_by_slug(session: AsyncSession, slug: str) -> Organization | None:
    return cast(
        Organization | None,
        await session.scalar(select(Organization).where(Organization.slug == slug)),
    )


async def get_or_create(
    session: AsyncSession, slug: str, name: str
) -> Organization:
    organization = await get_by_slug(session, slug)
    if organization is not None:
        return organization

    organization = Organization(slug=slug, name=name)
    session.add(organization)
    await session.flush()
    return organization
