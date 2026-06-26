from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset


async def get_for_organization(
    session: AsyncSession, organization_id: UUID, asset_id: UUID
) -> Asset | None:
    return cast(
        Asset | None,
        await session.scalar(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.organization_id == organization_id,
        )
        ),
    )


async def create_asset(
    session: AsyncSession,
    organization_id: UUID,
    asset_type: str,
    value: str,
    status: str = "active",
) -> Asset:
    asset = Asset(
        organization_id=organization_id,
        type=asset_type,
        value=value,
        status=status,
    )
    session.add(asset)
    await session.flush()
    return asset
