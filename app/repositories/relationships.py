from collections.abc import Mapping
from typing import cast
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.asset import AssetRelationship


async def get_duplicate_for_organization(
    session: AsyncSession,
    organization_id: UUID,
    source_asset_id: UUID,
    target_asset_id: UUID,
    relationship_type: str,
) -> AssetRelationship | None:
    """Find an existing relationship by its organization-scoped unique key."""
    return cast(
        AssetRelationship | None,
        await session.scalar(
            select(AssetRelationship).where(
                AssetRelationship.organization_id == organization_id,
                AssetRelationship.source_asset_id == source_asset_id,
                AssetRelationship.target_asset_id == target_asset_id,
                AssetRelationship.relationship_type == relationship_type,
            )
        ),
    )


async def create_relationship(
    session: AsyncSession,
    organization_id: UUID,
    source_asset_id: UUID,
    target_asset_id: UUID,
    relationship_type: str,
    metadata: Mapping[str, object] | None = None,
) -> AssetRelationship:
    """Persist a relationship under an explicit organization scope."""
    relationship = AssetRelationship(
        organization_id=organization_id,
        source_asset_id=source_asset_id,
        target_asset_id=target_asset_id,
        relationship_type=relationship_type,
        relationship_metadata=dict(metadata or {}),
    )
    session.add(relationship)
    await session.flush()
    return relationship


async def list_for_organization(
    session: AsyncSession, organization_id: UUID
) -> list[AssetRelationship]:
    """Return all relationships owned by one organization."""
    result = await session.scalars(
        select(AssetRelationship)
        .where(AssetRelationship.organization_id == organization_id)
        .order_by(AssetRelationship.created_at.desc(), AssetRelationship.id.asc())
    )
    return list(result.all())


async def list_one_hop_for_asset(
    session: AsyncSession, organization_id: UUID, center_asset_id: UUID
) -> list[AssetRelationship]:
    """Load organization-scoped relationships directly connected to one asset."""
    result = await session.scalars(
        select(AssetRelationship)
        .options(
            selectinload(AssetRelationship.source_asset),
            selectinload(AssetRelationship.target_asset),
        )
        .where(
            AssetRelationship.organization_id == organization_id,
            or_(
                AssetRelationship.source_asset_id == center_asset_id,
                AssetRelationship.target_asset_id == center_asset_id,
            ),
        )
        .order_by(AssetRelationship.created_at.desc(), AssetRelationship.id.asc())
    )
    return list(result.all())
