from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import AssetRelationship


async def create_relationship(
    session: AsyncSession,
    organization_id: UUID,
    source_asset_id: UUID,
    target_asset_id: UUID,
    relationship_type: str,
) -> AssetRelationship:
    relationship = AssetRelationship(
        organization_id=organization_id,
        source_asset_id=source_asset_id,
        target_asset_id=target_asset_id,
        relationship_type=relationship_type,
    )
    session.add(relationship)
    await session.flush()
    return relationship
