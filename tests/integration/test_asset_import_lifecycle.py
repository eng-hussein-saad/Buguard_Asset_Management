from datetime import UTC, datetime

import pytest
from app.schemas.assets import AssetImportBatch, AssetUpdate
from app.services import tenant_assets


class FakeSession:
    """Tracks import transaction boundaries in service tests."""

    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    async def commit(self) -> None:
        """Record that accepted records were committed."""
        self.committed = True

    async def rollback(self) -> None:
        """Record that a failed import rolled back."""
        self.rolled_back = True


def _install_import_store(monkeypatch, asset_factory, demo_user):
    """Patch repository calls with an organization-scoped in-memory store."""
    store = {}

    async def fake_get(session, organization_id, asset_type, value):
        return store.get((organization_id, asset_type, value))

    async def fake_create(
        session,
        organization_id,
        asset_type,
        value,
        status="active",
        first_seen=None,
        last_seen=None,
        source=None,
        tags=None,
        metadata=None,
    ):
        asset = asset_factory(
            organization_id,
            asset_type=asset_type,
            value=value,
            status=status,
            tags=tags or [],
            source=source,
        )
        asset.first_seen = first_seen or datetime.now(UTC)
        asset.last_seen = last_seen or asset.first_seen
        asset.asset_metadata = metadata or {}
        store[(organization_id, asset_type, value)] = asset
        return asset

    async def fake_update(session, asset, *, status, last_seen, source, tags, metadata):
        asset.status = status
        asset.last_seen = last_seen
        asset.source = source
        asset.tags = tags
        asset.asset_metadata = metadata
        return asset

    monkeypatch.setattr(
        tenant_assets.asset_repository, "get_by_org_type_value", fake_get
    )
    monkeypatch.setattr(tenant_assets.asset_repository, "create_asset", fake_create)
    monkeypatch.setattr(
        tenant_assets.asset_repository, "update_imported_asset", fake_update
    )
    return store


@pytest.mark.asyncio
async def test_import_creates_and_reimport_updates_without_duplicates(
    demo_user, asset_factory, import_payload_factory, monkeypatch
) -> None:
    store = _install_import_store(monkeypatch, asset_factory, demo_user)
    session = FakeSession()

    first = await tenant_assets.import_assets(
        session, demo_user, AssetImportBatch(**import_payload_factory())
    )
    second = await tenant_assets.import_assets(
        session, demo_user, AssetImportBatch(**import_payload_factory())
    )

    assert first.created == 1
    assert second.updated == 1
    assert len(store) == 1
    assert session.committed


@pytest.mark.asyncio
async def test_duplicate_records_in_one_batch_become_create_plus_update(
    demo_user, asset_factory, monkeypatch
) -> None:
    store = _install_import_store(monkeypatch, asset_factory, demo_user)
    payload = AssetImportBatch(
        items=[
            {"type": "domain", "value": "Example.COM"},
            {"type": "domain", "value": " example.com ", "tags": ["again"]},
        ]
    )

    summary = await tenant_assets.import_assets(FakeSession(), demo_user, payload)

    assert summary.created == 1
    assert summary.updated == 1
    assert len(store) == 1
    assert next(iter(store.values())).tags == ["again"]


@pytest.mark.asyncio
async def test_reimport_preserves_first_seen_refreshes_last_seen_and_merges_details(
    demo_user, asset_factory, monkeypatch
) -> None:
    store = _install_import_store(monkeypatch, asset_factory, demo_user)
    existing = asset_factory(
        demo_user.organization_id,
        value="example.com",
        tags=["external"],
        source="manual",
    )
    existing.asset_metadata = {"owner": "security", "tier": "old"}
    original_first_seen = existing.first_seen
    store[(demo_user.organization_id, "domain", "example.com")] = existing

    summary = await tenant_assets.import_assets(
        FakeSession(),
        demo_user,
        AssetImportBatch(
            items=[
                {
                    "type": "domain",
                    "value": "Example.COM",
                    "tags": ["external", "priority"],
                    "metadata": {"tier": "new", "env": "prod"},
                    "first_seen": "1999-01-01T00:00:00Z",
                    "last_seen": "1999-01-01T00:00:00Z",
                }
            ]
        ),
    )

    assert summary.updated == 1
    assert existing.first_seen == original_first_seen
    assert existing.last_seen > original_first_seen
    assert existing.tags == ["external", "priority"]
    assert existing.asset_metadata == {
        "owner": "security",
        "tier": "new",
        "env": "prod",
    }


@pytest.mark.asyncio
async def test_import_partial_and_all_record_failures(
    demo_user, asset_factory, monkeypatch
) -> None:
    _install_import_store(monkeypatch, asset_factory, demo_user)

    partial = await tenant_assets.import_assets(
        FakeSession(),
        demo_user,
        AssetImportBatch(
            items=[
                {"type": "domain", "value": "valid.example.com"},
                {"type": "domain", "value": ""},
                {"type": "unsupported", "value": "bad.example.com"},
            ]
        ),
    )
    failure = await tenant_assets.import_assets(
        FakeSession(),
        demo_user,
        AssetImportBatch(items=[{"type": "domain", "value": ""}]),
    )

    assert partial.created == 1
    assert partial.failed == 2
    assert tenant_assets.import_status_code(partial) == 207
    assert failure.failed == 1
    assert tenant_assets.import_status_code(failure) == 422


@pytest.mark.asyncio
async def test_stale_and_archived_import_lifecycle_rules(
    demo_user, asset_factory, monkeypatch
) -> None:
    store = _install_import_store(monkeypatch, asset_factory, demo_user)
    stale = asset_factory(
        demo_user.organization_id, value="stale.example", status="stale"
    )
    archived = asset_factory(
        demo_user.organization_id, value="archived.example", status="archived"
    )
    store[(demo_user.organization_id, "domain", "stale.example")] = stale
    store[(demo_user.organization_id, "domain", "archived.example")] = archived

    await tenant_assets.import_assets(
        FakeSession(),
        demo_user,
        AssetImportBatch(
            items=[
                {"type": "domain", "value": "stale.example"},
                {"type": "domain", "value": "archived.example"},
            ]
        ),
    )
    assert stale.status == "active"
    assert archived.status == "archived"

    await tenant_assets.import_assets(
        FakeSession(),
        demo_user,
        AssetImportBatch(
            items=[{"type": "domain", "value": "archived.example", "status": "active"}]
        ),
    )
    assert archived.status == "active"


@pytest.mark.asyncio
async def test_patch_stale_uses_existing_update_permissions(
    demo_user, asset_factory, monkeypatch
) -> None:
    existing = asset_factory(demo_user.organization_id, status="active")

    async def fake_get(*args):
        return existing

    async def no_duplicate(*args):
        return None

    async def fake_update(session, asset, updates):
        asset.status = updates["status"]
        return asset

    monkeypatch.setattr(
        tenant_assets.asset_repository, "get_for_organization", fake_get
    )
    monkeypatch.setattr(
        tenant_assets.asset_repository, "get_duplicate_for_organization", no_duplicate
    )
    monkeypatch.setattr(tenant_assets.asset_repository, "update_asset", fake_update)

    updated = await tenant_assets.update_asset(
        FakeSession(), demo_user, existing.id, AssetUpdate(status="stale")
    )

    assert updated.status == "stale"
