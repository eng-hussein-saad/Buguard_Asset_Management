from uuid import uuid4

import pytest
from app.core.errors import AssetNotFoundError
from app.schemas.assets import AssetCreate, AssetUpdate
from app.services import tenant_assets


class FakeSession:
    """Tracks transaction calls made by service methods."""

    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    async def commit(self) -> None:
        """Record that a service committed its transaction."""
        self.committed = True

    async def rollback(self) -> None:
        """Record that a service rolled back its transaction."""
        self.rolled_back = True


@pytest.mark.asyncio
async def test_analyst_create_update_and_read(
    demo_user, asset_factory, monkeypatch
) -> None:
    session = FakeSession()
    stored_asset = asset_factory(demo_user.organization_id, value="example.com")

    async def no_existing_observation(*args):
        return None

    async def no_duplicate(*args):
        return None

    async def fake_create(*args):
        return stored_asset

    async def fake_get(*args):
        return stored_asset

    async def fake_update(session, asset, updates):
        asset.status = updates["status"]
        return asset

    monkeypatch.setattr(
        tenant_assets.asset_repository, "get_by_org_type_value", no_existing_observation
    )
    monkeypatch.setattr(
        tenant_assets.asset_repository, "get_duplicate_for_organization", no_duplicate
    )
    monkeypatch.setattr(tenant_assets.asset_repository, "create_asset", fake_create)
    monkeypatch.setattr(
        tenant_assets.asset_repository, "get_for_organization", fake_get
    )
    monkeypatch.setattr(tenant_assets.asset_repository, "update_asset", fake_update)

    created, was_created = await tenant_assets.create_asset(
        session,
        demo_user,
        AssetCreate(type="domain", value=" Example.COM ", source="manual"),
    )
    read = await tenant_assets.read_asset(session, demo_user, stored_asset.id)
    updated = await tenant_assets.update_asset(
        session, demo_user, stored_asset.id, AssetUpdate(status="stale")
    )

    assert created.value == "example.com"
    assert was_created is True
    assert read.id == stored_asset.id
    assert updated.status == "stale"
    assert session.committed


@pytest.mark.asyncio
async def test_admin_hard_delete(admin_user, monkeypatch) -> None:
    session = FakeSession()
    asset_id = uuid4()

    async def fake_delete(session, organization_id, requested_asset_id):
        assert organization_id == admin_user.organization_id
        assert requested_asset_id == asset_id
        return True

    monkeypatch.setattr(
        tenant_assets.asset_repository, "delete_for_organization", fake_delete
    )

    await tenant_assets.delete_asset(session, admin_user, asset_id)

    assert session.committed


@pytest.mark.asyncio
async def test_missing_asset_uses_asset_not_found(demo_user, monkeypatch) -> None:
    async def fake_get(*args):
        return None

    monkeypatch.setattr(
        tenant_assets.asset_repository, "get_for_organization", fake_get
    )

    with pytest.raises(AssetNotFoundError):
        await tenant_assets.read_asset(FakeSession(), demo_user, uuid4())


@pytest.mark.asyncio
async def test_create_existing_asset_refreshes_observation(
    demo_user, asset_factory, monkeypatch
) -> None:
    existing = asset_factory(
        demo_user.organization_id,
        value="example.com",
        status="stale",
        tags=["external"],
        source="old-source",
    )
    existing.asset_metadata = {"owner": "security", "tier": "old"}
    original_first_seen = existing.first_seen

    async def fake_existing(*args):
        return existing

    async def fake_update(session, asset, *, status, last_seen, source, tags, metadata):
        asset.status = status
        asset.last_seen = last_seen
        asset.source = source
        asset.tags = tags
        asset.asset_metadata = metadata
        return asset

    monkeypatch.setattr(
        tenant_assets.asset_repository, "get_by_org_type_value", fake_existing
    )
    monkeypatch.setattr(
        tenant_assets.asset_repository, "update_imported_asset", fake_update
    )

    refreshed, was_created = await tenant_assets.create_asset(
        FakeSession(),
        demo_user,
        AssetCreate(
            type="domain",
            value=" Example.COM ",
            tags=["external", "priority"],
            metadata={"tier": "new", "env": "prod"},
        ),
    )

    assert was_created is False
    assert refreshed.status == "active"
    assert existing.first_seen == original_first_seen
    assert existing.last_seen > original_first_seen
    assert refreshed.tags == ["external", "priority"]
    assert refreshed.metadata == {"owner": "security", "tier": "new", "env": "prod"}
