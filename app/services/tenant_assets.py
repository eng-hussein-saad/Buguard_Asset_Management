from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AssetNotFoundError, DuplicateAssetError, NotFoundError
from app.models.asset import Asset, AssetRelationship
from app.models.user import User
from app.repositories import assets as asset_repository
from app.repositories import relationships as relationship_repository
from app.schemas.assets import (
    AssetCreate,
    AssetListParams,
    AssetRead,
    AssetUpdate,
    PaginatedAssets,
)
from app.services.rbac import Permission, require_permission


def normalize_asset_value(asset_type: str, value: str) -> str:
    """Trim every asset value and lowercase domain-like values."""
    normalized = value.strip()
    if asset_type in {"domain", "subdomain"}:
        return normalized.lower()
    return normalized


def _normalized_update(existing: Asset, payload: AssetUpdate) -> dict[str, object]:
    """Prepare update fields with type-aware value normalization."""
    updates = payload.model_dump(exclude_unset=True)
    next_type = str(updates.get("type", existing.type))
    if "type" in updates:
        updates["type"] = updates["type"].value
    if "status" in updates:
        updates["status"] = updates["status"].value
    if "value" in updates:
        updates["value"] = normalize_asset_value(next_type, str(updates["value"]))
    elif "type" in updates:
        updates["value"] = normalize_asset_value(next_type, existing.value)
    return updates


def _page(total: int, params: AssetListParams) -> tuple[int, bool, bool]:
    """Calculate total pages and adjacent page availability."""
    total_pages = (total + params.page_size - 1) // params.page_size if total else 0
    return total_pages, params.page < total_pages, params.page > 1


async def get_owned_asset(
    session: AsyncSession, current_user: User, asset_id: UUID
) -> Asset:
    """Return an organization-scoped asset model for internal service callers."""
    require_permission(current_user.role, Permission.READ_ASSETS)
    asset = await asset_repository.get_for_organization(
        session, current_user.organization_id, asset_id
    )
    if asset is None:
        raise NotFoundError("Asset")
    return asset


async def create_asset(
    session: AsyncSession, current_user: User, payload: AssetCreate
) -> AssetRead:
    """Create an asset for the current user's organization after RBAC checks."""
    require_permission(current_user.role, Permission.CREATE_ASSET)
    normalized_value = normalize_asset_value(payload.type.value, payload.value)
    duplicate = await asset_repository.get_duplicate_for_organization(
        session, current_user.organization_id, payload.type.value, normalized_value
    )
    if duplicate is not None:
        raise DuplicateAssetError()
    try:
        asset = await asset_repository.create_asset(
            session,
            current_user.organization_id,
            payload.type.value,
            normalized_value,
            payload.status.value,
            payload.first_seen,
            payload.last_seen,
            payload.source,
            payload.tags,
            payload.metadata,
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateAssetError() from exc
    return AssetRead.from_model(asset)


async def read_asset(
    session: AsyncSession, current_user: User, asset_id: UUID
) -> AssetRead:
    """Read one asset from the authenticated user's organization."""
    require_permission(current_user.role, Permission.READ_ASSETS)
    asset = await asset_repository.get_for_organization(
        session, current_user.organization_id, asset_id
    )
    if asset is None:
        raise AssetNotFoundError()
    return AssetRead.from_model(asset)


async def update_asset(
    session: AsyncSession, current_user: User, asset_id: UUID, payload: AssetUpdate
) -> AssetRead:
    """Update an organization-scoped asset with duplicate protection."""
    require_permission(current_user.role, Permission.UPDATE_ASSET)
    asset = await asset_repository.get_for_organization(
        session, current_user.organization_id, asset_id
    )
    if asset is None:
        raise AssetNotFoundError()
    updates = _normalized_update(asset, payload)
    next_type = str(updates.get("type", asset.type))
    next_value = str(updates.get("value", asset.value))
    duplicate = await asset_repository.get_duplicate_for_organization(
        session, current_user.organization_id, next_type, next_value, asset_id
    )
    if duplicate is not None:
        raise DuplicateAssetError()
    try:
        updated = await asset_repository.update_asset(session, asset, updates)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateAssetError() from exc
    return AssetRead.from_model(updated)


async def delete_asset(
    session: AsyncSession, current_user: User, asset_id: UUID
) -> None:
    """Hard delete an organization-scoped asset when the user is an admin."""
    require_permission(current_user.role, Permission.DELETE_OR_ARCHIVE)
    deleted = await asset_repository.delete_for_organization(
        session, current_user.organization_id, asset_id
    )
    if not deleted:
        raise AssetNotFoundError()
    await session.commit()


async def list_assets(
    session: AsyncSession, current_user: User, params: AssetListParams
) -> PaginatedAssets:
    """List filtered assets for the current user's organization with pagination."""
    require_permission(current_user.role, Permission.READ_ASSETS)
    if params.value_contains is not None and params.type is not None:
        params.value_contains = normalize_asset_value(
            params.type.value, params.value_contains
        )
    total = await asset_repository.count_for_organization(
        session, current_user.organization_id, params
    )
    assets = await asset_repository.list_for_organization(
        session, current_user.organization_id, params
    )
    total_pages, has_next, has_previous = _page(total, params)
    return PaginatedAssets(
        items=[AssetRead.from_model(asset) for asset in assets],
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous,
    )


async def create_owned_relationship(
    session: AsyncSession,
    current_user: User,
    source_asset_id: UUID,
    target_asset_id: UUID,
    relationship_type: str,
) -> AssetRelationship:
    """Create a relationship only when both assets belong to the current tenant."""
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
