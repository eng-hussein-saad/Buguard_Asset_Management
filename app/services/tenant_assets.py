from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.asset import Asset, AssetRelationship
from app.models.user import User
from app.repositories import assets as asset_repository
from app.repositories import relationships as relationship_repository
from app.services.rbac import Permission, require_permission


async def get_owned_asset(
    session: AsyncSession, current_user: User, asset_id: UUID
) -> Asset:
    require_permission(current_user.role, Permission.READ_ASSETS)
    asset = await asset_repository.get_for_organization(
        session, current_user.organization_id, asset_id
    )
    if asset is None:
        raise NotFoundError("Asset")
    return asset


async def create_owned_relationship(
    session: AsyncSession,
    current_user: User,
    source_asset_id: UUID,
    target_asset_id: UUID,
    relationship_type: str,
) -> AssetRelationship:
    require_permission(current_user.role, Permission.CREATE_RELATIONSHIP)
    source_asset = await asset_repository.get_for_organization(
        session, current_user.organization_id, source_asset_id
    )
    target_asset = await asset_repository.get_for_organization(
        session, current_user.organization_id, target_asset_id
    )
    if source_asset is None or target_asset is None:
        raise NotFoundError("Asset")

    return await relationship_repository.create_relationship(
        session,
        current_user.organization_id,
        source_asset_id,
        target_asset_id,
        relationship_type,
    )
