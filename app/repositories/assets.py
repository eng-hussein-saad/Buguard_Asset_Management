from collections.abc import Sequence
from typing import Any, cast
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.schemas.assets import AssetListParams

SORT_COLUMNS = {
    "value": Asset.value,
    "type": Asset.type,
    "status": Asset.status,
    "first_seen": Asset.first_seen,
    "last_seen": Asset.last_seen,
    "created_at": Asset.created_at,
}


async def get_for_organization(
    session: AsyncSession, organization_id: UUID, asset_id: UUID
) -> Asset | None:
    """Return one asset by id inside the requested organization scope."""
    return cast(
        Asset | None,
        await session.scalar(
            select(Asset).where(
                Asset.id == asset_id,
                Asset.organization_id == organization_id,
            )
        ),
    )


async def get_duplicate_for_organization(
    session: AsyncSession,
    organization_id: UUID,
    asset_type: str,
    value: str,
    exclude_asset_id: UUID | None = None,
) -> Asset | None:
    """Find an asset with the same organization, type, and canonical value."""
    query = select(Asset).where(
        Asset.organization_id == organization_id,
        Asset.type == asset_type,
        Asset.value == value,
    )
    if exclude_asset_id is not None:
        query = query.where(Asset.id != exclude_asset_id)
    return cast(Asset | None, await session.scalar(query))


async def get_by_org_type_value(
    session: AsyncSession,
    organization_id: UUID,
    asset_type: str,
    value: str,
) -> Asset | None:
    """Look up one asset by organization, type, and canonical import value."""
    return await get_duplicate_for_organization(
        session, organization_id, asset_type, value
    )


async def create_asset(
    session: AsyncSession,
    organization_id: UUID,
    asset_type: str,
    value: str,
    status: str = "active",
    first_seen: Any | None = None,
    last_seen: Any | None = None,
    source: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Asset:
    """Persist a new asset under an explicit organization scope."""
    asset = Asset(
        organization_id=organization_id,
        type=asset_type,
        value=value,
        status=status,
        source=source,
        tags=tags or [],
        asset_metadata=metadata or {},
    )
    if first_seen is not None:
        asset.first_seen = first_seen
    if last_seen is not None:
        asset.last_seen = last_seen
    session.add(asset)
    await session.flush()
    return asset


async def update_asset(
    session: AsyncSession, asset: Asset, updates: dict[str, Any]
) -> Asset:
    """Apply editable asset fields to an existing scoped model instance."""
    for field_name, value in updates.items():
        if field_name == "metadata":
            asset.asset_metadata = value
        else:
            setattr(asset, field_name, value)
    await session.flush()
    return asset


async def update_imported_asset(
    session: AsyncSession,
    asset: Asset,
    *,
    status: str,
    last_seen: Any,
    source: str | None,
    tags: list[str],
    metadata: dict[str, Any],
) -> Asset:
    """Apply import-safe lifecycle and observation fields to an existing asset."""
    asset.status = status
    asset.last_seen = last_seen
    asset.source = source
    asset.tags = tags
    asset.asset_metadata = metadata
    await session.flush()
    return asset


async def delete_for_organization(
    session: AsyncSession, organization_id: UUID, asset_id: UUID
) -> bool:
    """Hard delete one asset inside an organization and report whether it existed."""
    asset = await get_for_organization(session, organization_id, asset_id)
    if asset is None:
        return False
    await session.delete(asset)
    await session.flush()
    return True


def _filtered_query(
    organization_id: UUID, params: AssetListParams
) -> Select[tuple[Asset]]:
    """Build the organization-scoped asset filter query shared by count and list."""
    query = select(Asset).where(Asset.organization_id == organization_id)
    if params.type is not None:
        query = query.where(Asset.type == params.type.value)
    if params.status is not None:
        query = query.where(Asset.status == params.status.value)
    if params.tag is not None:
        query = query.where(Asset.tags.contains([params.tag]))
    if params.source is not None:
        query = query.where(Asset.source == params.source)
    if params.value_contains is not None:
        query = query.where(Asset.value.ilike(f"%{params.value_contains}%"))
    if params.certificate_lifecycle_status is not None:
        query = query.where(Asset.type == "certificate")
        today = func.current_date()
        expires_text = Asset.asset_metadata["expires"].astext
        has_valid_date = expires_text.op("~")(r"^\d{4}-\d{2}-\d{2}")
        expires = func.to_date(expires_text, "YYYY-MM-DD")
        status = params.certificate_lifecycle_status.value
        if status == "expired":
            query = query.where(has_valid_date, expires < today)
        elif status == "expiring_soon":
            query = query.where(has_valid_date, expires >= today, expires <= today + 30)
        elif status == "valid":
            query = query.where(has_valid_date, expires > today + 30)
        else:
            query = query.where(
                or_(
                    ~Asset.asset_metadata.has_key("expires"),  # noqa: W601
                    ~has_valid_date,
                )
            )
    return query


async def select_analysis_evidence(
    session: AsyncSession, organization_id: UUID, params: AssetListParams, limit: int
) -> Sequence[Asset]:
    """Return bounded organization-scoped evidence for analysis reports."""
    result = await session.scalars(
        _filtered_query(organization_id, params)
        .order_by(Asset.updated_at.desc(), Asset.id.asc())
        .limit(limit)
    )
    return result.all()


async def count_for_organization(
    session: AsyncSession, organization_id: UUID, params: AssetListParams
) -> int:
    """Count filtered assets without dropping organization scoping."""
    filtered = _filtered_query(organization_id, params).subquery()
    return cast(int, await session.scalar(select(func.count()).select_from(filtered)))


async def list_for_organization(
    session: AsyncSession, organization_id: UUID, params: AssetListParams
) -> Sequence[Asset]:
    """Return one bounded page of filtered, sorted assets for an organization."""
    sort_column = SORT_COLUMNS[params.sort_by]
    order_by = sort_column.asc() if params.sort_order == "asc" else sort_column.desc()
    offset = (params.page - 1) * params.page_size
    result = await session.scalars(
        _filtered_query(organization_id, params)
        .order_by(order_by, Asset.id.asc())
        .offset(offset)
        .limit(params.page_size)
    )
    return result.all()
