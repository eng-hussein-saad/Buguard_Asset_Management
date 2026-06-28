from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import (
    AssetNotFoundError,
    DuplicateAssetError,
    DuplicateRelationshipError,
    NotFoundError,
)
from app.models.asset import (
    Asset,
    AssetRelationship,
    AssetStatus,
    AssetType,
    RelationshipType,
)
from app.models.user import User
from app.repositories import assets as asset_repository
from app.repositories import relationships as relationship_repository
from app.schemas.assets import (
    AssetCreate,
    AssetGraph,
    AssetImportBatch,
    AssetImportError,
    AssetImportSummary,
    AssetListParams,
    AssetRead,
    AssetUpdate,
    GraphAsset,
    GraphEdge,
    PaginatedAssets,
    RelationshipCreate,
    RelationshipList,
    RelationshipRead,
)
from app.services.cache import CacheService
from app.services.certificate_lifecycle import parse_certificate_expiry
from app.services.rbac import Permission, require_permission


def normalize_asset_value(asset_type: str, value: str) -> str:
    """Trim every asset value and lowercase domain-like values."""
    normalized = value.strip()
    if asset_type in {"domain", "subdomain"}:
        return normalized.lower()
    return normalized


def merge_import_tags(
    existing: list[str] | None, incoming: list[str] | None
) -> list[str]:
    """Merge tags in stable order while dropping duplicate values."""
    merged: list[str] = []
    for tag in [*(existing or []), *(incoming or [])]:
        if tag not in merged:
            merged.append(tag)
    return merged


def merge_import_metadata(
    existing: dict[str, Any] | None, incoming: dict[str, Any] | None
) -> dict[str, Any]:
    """Shallow-merge metadata with newest import keys winning conflicts."""
    return {**(existing or {}), **(incoming or {})}


def resolve_import_status(
    existing_status: str | None, explicit_status: str | None
) -> str:
    """Choose the lifecycle status for new imports and accepted re-sightings."""
    if existing_status is None:
        return explicit_status or AssetStatus.ACTIVE.value
    if existing_status == AssetStatus.STALE.value:
        return AssetStatus.ACTIVE.value
    if existing_status == AssetStatus.ARCHIVED.value:
        return (
            AssetStatus.ACTIVE.value
            if explicit_status == AssetStatus.ACTIVE.value
            else AssetStatus.ARCHIVED.value
        )
    return explicit_status or existing_status


def import_status_code(summary: AssetImportSummary) -> int:
    """Map import summary counts to the required HTTP response status."""
    accepted = summary.created + summary.updated
    if accepted and summary.failed:
        return 207
    if not accepted and summary.failed:
        return 422
    return 200


def _reject_record(index: int, reason: str) -> AssetImportError:
    """Build a stable per-record validation error."""
    return AssetImportError(index=index, reason=reason)


def validate_import_record(
    index: int, raw: dict[str, Any]
) -> tuple[dict[str, Any] | None, AssetImportError | None]:
    """Validate one raw import record without trusting ownership or timestamps."""
    allowed_fields = {
        "type",
        "id",
        "value",
        "status",
        "source",
        "tags",
        "metadata",
        "parent",
        "covers",
        "first_seen",
        "last_seen",
    }
    ignored_fields = {"first_seen", "last_seen"}
    extra_fields = set(raw) - allowed_fields
    if "organization_id" in raw:
        return None, _reject_record(index, "organization_id is not accepted.")
    if extra_fields:
        return None, _reject_record(
            index, f"Unsupported import field: {sorted(extra_fields)[0]}."
        )
    for field_name in ignored_fields:
        raw.pop(field_name, None)

    try:
        asset_type = AssetType(str(raw.get("type"))).value
    except ValueError:
        return None, _reject_record(index, "Unsupported asset type.")

    value = raw.get("value")
    if not isinstance(value, str) or not value.strip():
        return None, _reject_record(index, "Asset value must not be blank.")

    status_value: str | None = None
    if raw.get("status") is not None:
        try:
            status_value = AssetStatus(str(raw["status"])).value
        except ValueError:
            return None, _reject_record(index, "Unsupported asset status.")

    source = raw.get("source")
    if source is not None and not isinstance(source, str):
        return None, _reject_record(index, "Asset source must be a string or null.")

    tags = raw.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        return None, _reject_record(index, "Asset tags must be a list of strings.")

    metadata = raw.get("metadata", {})
    if not isinstance(metadata, dict):
        return None, _reject_record(index, "Asset metadata must be an object.")
    import_id = raw.get("id")
    if import_id is not None and (
        not isinstance(import_id, str) or not import_id.strip()
    ):
        return None, _reject_record(index, "Import-local id must be a string.")
    parent = raw.get("parent")
    if parent is not None and (not isinstance(parent, str) or not parent.strip()):
        return None, _reject_record(index, "Parent reference must be a string.")
    covers = raw.get("covers")
    if covers is not None and (not isinstance(covers, str) or not covers.strip()):
        return None, _reject_record(index, "Covers reference must be a string.")

    return (
        {
            "import_id": import_id.strip() if isinstance(import_id, str) else None,
            "type": asset_type,
            "value": normalize_asset_value(asset_type, value),
            "status": status_value,
            "source": source,
            "tags": tags,
            "metadata": metadata,
            "parent": parent.strip() if isinstance(parent, str) else None,
            "covers": covers.strip() if isinstance(covers, str) else None,
        },
        None,
    )


def _certificate_expiry_error(
    index: int, record: dict[str, Any]
) -> AssetImportError | None:
    """Report malformed certificate expiry metadata without rejecting the record."""
    if record["type"] != AssetType.CERTIFICATE.value:
        return None
    metadata = record["metadata"]
    if "expires" in metadata and parse_certificate_expiry(metadata["expires"]) is None:
        return _reject_record(index, "Certificate metadata.expires is malformed.")
    return None


async def _create_import_relationship(
    session: AsyncSession,
    organization_id: UUID,
    *,
    source: Asset,
    target: Asset,
    relationship_type: RelationshipType,
) -> bool:
    """Create an import relationship idempotently inside one organization."""
    duplicate = await relationship_repository.get_duplicate_for_organization(
        session, organization_id, source.id, target.id, relationship_type.value
    )
    if duplicate is not None:
        return False
    await relationship_repository.create_relationship(
        session,
        organization_id,
        source.id,
        target.id,
        relationship_type.value,
        {"source": "import"},
    )
    return True


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


async def observe_asset(
    session: AsyncSession,
    organization_id: UUID,
    *,
    asset_type: str,
    value: str,
    explicit_status: str | None,
    source: str | None,
    tags: list[str] | None,
    metadata: dict[str, Any] | None,
) -> tuple[Asset, bool]:
    """Create or refresh one observed asset using import lifecycle semantics."""
    observed_at = datetime.now(UTC)
    normalized_value = normalize_asset_value(asset_type, value)
    existing = await asset_repository.get_by_org_type_value(
        session,
        organization_id,
        asset_type,
        normalized_value,
    )
    if existing is None:
        asset = await asset_repository.create_asset(
            session,
            organization_id,
            asset_type,
            normalized_value,
            resolve_import_status(None, explicit_status),
            observed_at,
            observed_at,
            source,
            merge_import_tags([], tags),
            dict(metadata or {}),
        )
        return asset, True

    asset = await asset_repository.update_imported_asset(
        session,
        existing,
        status=resolve_import_status(existing.status, explicit_status),
        last_seen=observed_at,
        source=source if source is not None else existing.source,
        tags=merge_import_tags(existing.tags, tags),
        metadata=merge_import_metadata(existing.asset_metadata, metadata),
    )
    return asset, False


async def create_asset(
    session: AsyncSession,
    current_user: User,
    payload: AssetCreate,
    cache_service: CacheService | None = None,
) -> tuple[AssetRead, bool]:
    """Create or refresh one asset observation for the current organization."""
    require_permission(current_user.role, Permission.CREATE_ASSET)
    try:
        asset, created = await observe_asset(
            session,
            current_user.organization_id,
            asset_type=payload.type.value,
            value=payload.value,
            explicit_status=(
                payload.status.value if "status" in payload.model_fields_set else None
            ),
            source=payload.source,
            tags=payload.tags,
            metadata=payload.metadata,
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateAssetError() from exc
    await _invalidate_asset_cache(
        cache_service, current_user.organization_id, "asset_create_refresh"
    )
    return AssetRead.from_model(asset), created


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
    session: AsyncSession,
    current_user: User,
    asset_id: UUID,
    payload: AssetUpdate,
    cache_service: CacheService | None = None,
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
    await _invalidate_asset_cache(
        cache_service,
        current_user.organization_id,
        "mark_stale" if updated.status == AssetStatus.STALE.value else "asset_update",
    )
    return AssetRead.from_model(updated)


async def import_assets(
    session: AsyncSession,
    current_user: User,
    payload: AssetImportBatch,
    cache_service: CacheService | None = None,
) -> AssetImportSummary:
    """Import observations idempotently under the authenticated organization."""
    require_permission(current_user.role, Permission.BULK_IMPORT)
    summary = AssetImportSummary(created=0, updated=0, failed=0, errors=[])

    processed_by_import_id: dict[str, Asset] = {}
    duplicate_import_ids: set[str] = set()
    relationship_requests: list[tuple[int, str, str, RelationshipType]] = []

    try:
        for index, raw_record in enumerate(payload.items):
            record, error = validate_import_record(index, dict(raw_record))
            if error is not None or record is None:
                summary.failed += 1
                summary.errors.append(error or _reject_record(index, "Invalid record."))
                continue
            expiry_error = _certificate_expiry_error(index, record)
            if expiry_error is not None:
                summary.failed += 1
                summary.errors.append(expiry_error)
            import_id = record["import_id"]
            if import_id is not None and import_id in processed_by_import_id:
                duplicate_import_ids.add(str(import_id))
                summary.failed += 1
                summary.errors.append(
                    _reject_record(index, "Duplicate import-local id.")
                )
                continue

            asset, created = await observe_asset(
                session,
                current_user.organization_id,
                asset_type=str(record["type"]),
                value=str(record["value"]),
                explicit_status=record["status"],
                source=record["source"],
                tags=record["tags"],
                metadata=record["metadata"],
            )
            if created:
                summary.created += 1
            else:
                summary.updated += 1
            if import_id is not None:
                processed_by_import_id[str(import_id)] = asset
                if record["parent"] is not None:
                    relationship_requests.append(
                        (
                            index,
                            str(import_id),
                            str(record["parent"]),
                            RelationshipType.PARENT,
                        )
                    )
                if record["covers"] is not None:
                    relationship_requests.append(
                        (
                            index,
                            str(import_id),
                            str(record["covers"]),
                            RelationshipType.COVERS,
                        )
                    )
        for index, source_ref, target_ref, relationship_type in relationship_requests:
            source = processed_by_import_id.get(source_ref)
            target = processed_by_import_id.get(target_ref)
            if (
                source is None
                or target is None
                or source_ref in duplicate_import_ids
                or target_ref in duplicate_import_ids
            ):
                summary.failed += 1
                summary.errors.append(
                    _reject_record(
                        index,
                        f"Unresolved {relationship_type.value} reference.",
                    )
                )
                continue
            if relationship_type == RelationshipType.PARENT and not (
                source.type == AssetType.SUBDOMAIN.value
                and target.type == AssetType.DOMAIN.value
            ):
                summary.failed += 1
                summary.errors.append(_reject_record(index, "Unsafe parent reference."))
                continue
            if relationship_type == RelationshipType.COVERS and not (
                source.type == AssetType.CERTIFICATE.value
                and target.type == AssetType.SUBDOMAIN.value
            ):
                summary.failed += 1
                summary.errors.append(_reject_record(index, "Unsafe covers reference."))
                continue
            created_relationship = await _create_import_relationship(
                session,
                current_user.organization_id,
                source=source,
                target=target,
                relationship_type=relationship_type,
            )
            if created_relationship:
                summary.relationships_created += 1
        if summary.created or summary.updated:
            await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateAssetError() from exc

    if summary.created or summary.updated:
        await _invalidate_asset_cache(
            cache_service, current_user.organization_id, "bulk_import"
        )
    return summary


async def delete_asset(
    session: AsyncSession,
    current_user: User,
    asset_id: UUID,
    cache_service: CacheService | None = None,
) -> None:
    """Hard delete an organization-scoped asset when the user is an admin."""
    require_permission(current_user.role, Permission.DELETE_OR_ARCHIVE)
    deleted = await asset_repository.delete_for_organization(
        session, current_user.organization_id, asset_id
    )
    if not deleted:
        raise AssetNotFoundError()
    await session.commit()
    await _invalidate_asset_cache(
        cache_service, current_user.organization_id, "asset_delete_archive"
    )


async def list_assets(
    session: AsyncSession,
    current_user: User,
    params: AssetListParams,
    cache_service: CacheService | None = None,
) -> PaginatedAssets:
    """List filtered assets for the current user's organization with pagination."""
    require_permission(current_user.role, Permission.READ_ASSETS)
    if params.value_contains is not None and params.type is not None:
        params.value_contains = normalize_asset_value(
            params.type.value, params.value_contains
        )
    if cache_service is not None:
        cached = await cache_service.get_asset_list(
            current_user.organization_id, params
        )
        if cached is not None:
            return cached
    total = await asset_repository.count_for_organization(
        session, current_user.organization_id, params
    )
    assets = await asset_repository.list_for_organization(
        session, current_user.organization_id, params
    )
    total_pages, has_next, has_previous = _page(total, params)
    payload = PaginatedAssets(
        items=[AssetRead.from_model(asset) for asset in assets],
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous,
    )
    if cache_service is not None:
        await cache_service.set_asset_list(
            current_user.organization_id, params, payload
        )
    return payload


async def create_owned_relationship(
    session: AsyncSession,
    current_user: User,
    payload: RelationshipCreate,
    cache_service: CacheService | None = None,
) -> RelationshipRead:
    """Create a relationship only when both assets belong to the current tenant."""
    require_permission(current_user.role, Permission.CREATE_RELATIONSHIP)
    source_asset = await asset_repository.get_for_organization(
        session, current_user.organization_id, payload.source_asset_id
    )
    target_asset = await asset_repository.get_for_organization(
        session, current_user.organization_id, payload.target_asset_id
    )
    if source_asset is None or target_asset is None:
        raise AssetNotFoundError()

    duplicate = await relationship_repository.get_duplicate_for_organization(
        session,
        current_user.organization_id,
        payload.source_asset_id,
        payload.target_asset_id,
        payload.relationship_type.value,
    )
    if duplicate is not None:
        raise DuplicateRelationshipError()

    try:
        relationship = await relationship_repository.create_relationship(
            session,
            current_user.organization_id,
            payload.source_asset_id,
            payload.target_asset_id,
            payload.relationship_type.value,
            payload.metadata,
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateRelationshipError() from exc
    await _invalidate_asset_cache(
        cache_service, current_user.organization_id, "relationship_create"
    )
    return RelationshipRead.from_model(relationship)


def _relationship_read(relationship: AssetRelationship) -> RelationshipRead:
    """Map a relationship model to an API response with no tenant id."""
    return RelationshipRead.from_model(relationship)


def _graph_asset(asset: Asset) -> GraphAsset:
    """Map an asset model to the visualization-friendly graph node shape."""
    return GraphAsset.from_model(asset)


def _graph_edge(relationship: AssetRelationship) -> GraphEdge:
    """Map a relationship model to the visualization-friendly graph edge shape."""
    return GraphEdge.from_model(relationship)


async def list_relationships(
    session: AsyncSession, current_user: User
) -> RelationshipList:
    """List relationships scoped to the authenticated user's organization."""
    require_permission(current_user.role, Permission.READ_RELATIONSHIPS)
    relationships = await relationship_repository.list_for_organization(
        session, current_user.organization_id
    )
    return RelationshipList(items=[_relationship_read(item) for item in relationships])


async def get_asset_graph(
    session: AsyncSession,
    current_user: User,
    asset_id: UUID,
    cache_service: CacheService | None = None,
) -> AssetGraph:
    """Return a de-duplicated one-hop graph for an organization-owned asset."""
    require_permission(current_user.role, Permission.READ_GRAPH)
    if cache_service is not None:
        cached = await cache_service.get_asset_graph(
            current_user.organization_id, asset_id
        )
        if cached is not None:
            return cached
    center = await asset_repository.get_for_organization(
        session, current_user.organization_id, asset_id
    )
    if center is None:
        raise AssetNotFoundError()

    relationships = await relationship_repository.list_one_hop_for_asset(
        session, current_user.organization_id, asset_id
    )
    nodes_by_id: dict[UUID, GraphAsset] = {center.id: _graph_asset(center)}
    edges_by_id: dict[UUID, GraphEdge] = {}

    for relationship in relationships:
        source = relationship.source_asset
        target = relationship.target_asset
        if (
            source.organization_id != current_user.organization_id
            or target.organization_id != current_user.organization_id
        ):
            continue
        nodes_by_id.setdefault(source.id, _graph_asset(source))
        nodes_by_id.setdefault(target.id, _graph_asset(target))
        edges_by_id.setdefault(relationship.id, _graph_edge(relationship))

    graph = AssetGraph(
        center=_graph_asset(center),
        nodes=list(nodes_by_id.values()),
        edges=list(edges_by_id.values()),
    )
    if cache_service is not None:
        await cache_service.set_asset_graph(
            current_user.organization_id, asset_id, graph
        )
    return graph


async def _invalidate_asset_cache(
    cache_service: CacheService | None, organization_id: UUID, reason: str
) -> None:
    """Invalidate organization-scoped asset caches without failing writes."""
    if cache_service is None:
        return
    await cache_service.invalidate_assets(organization_id, reason)
