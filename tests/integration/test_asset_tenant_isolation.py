from uuid import uuid4

import pytest
from app.core.errors import AssetNotFoundError
from app.schemas.assets import AssetCreate, AssetListParams, AssetUpdate
from app.services import tenant_assets


class DummySession:
    """Placeholder session for tenant isolation tests."""

    async def commit(self) -> None:
        """Pretend to commit a transaction."""


@pytest.mark.asyncio
async def test_same_asset_value_can_exist_in_two_organizations(
    demo_user, asset_factory, monkeypatch
) -> None:
    created = asset_factory(demo_user.organization_id, value="example.com")

    async def fake_duplicate(*args):
        return None

    async def fake_create(session, organization_id, asset_type, value, *args):
        assert organization_id == demo_user.organization_id
        assert value == "example.com"
        return created

    monkeypatch.setattr(
        tenant_assets.asset_repository, "get_duplicate_for_organization", fake_duplicate
    )
    monkeypatch.setattr(tenant_assets.asset_repository, "create_asset", fake_create)

    result = await tenant_assets.create_asset(
        DummySession(), demo_user, AssetCreate(type="domain", value="Example.COM")
    )

    assert result.value == "example.com"


@pytest.mark.asyncio
async def test_cross_organization_detail_update_and_delete_return_not_found(
    demo_user, admin_user, monkeypatch
) -> None:
    async def fake_get(*args):
        return None

    async def fake_delete(*args):
        return False

    monkeypatch.setattr(
        tenant_assets.asset_repository, "get_for_organization", fake_get
    )
    monkeypatch.setattr(
        tenant_assets.asset_repository, "delete_for_organization", fake_delete
    )

    with pytest.raises(AssetNotFoundError):
        await tenant_assets.read_asset(DummySession(), demo_user, uuid4())
    with pytest.raises(AssetNotFoundError):
        await tenant_assets.update_asset(
            DummySession(), demo_user, uuid4(), AssetUpdate(status="stale")
        )
    with pytest.raises(AssetNotFoundError):
        await tenant_assets.delete_asset(DummySession(), admin_user, uuid4())


def test_client_supplied_organization_id_is_rejected() -> None:
    with pytest.raises(ValueError):
        AssetCreate(
            type="domain",
            value="example.com",
            organization_id=str(uuid4()),
        )
    with pytest.raises(ValueError):
        AssetUpdate(status="stale", organization_id=str(uuid4()))


@pytest.mark.asyncio
async def test_list_is_scoped_to_authenticated_organization(
    demo_user, monkeypatch
) -> None:
    captured = {}

    async def fake_count(session, organization_id, params):
        captured["organization_id"] = organization_id
        return 0

    async def fake_list(session, organization_id, params):
        assert organization_id == captured["organization_id"]
        return []

    monkeypatch.setattr(
        tenant_assets.asset_repository, "count_for_organization", fake_count
    )
    monkeypatch.setattr(
        tenant_assets.asset_repository, "list_for_organization", fake_list
    )

    result = await tenant_assets.list_assets(
        DummySession(), demo_user, AssetListParams(value_contains="example")
    )

    assert captured["organization_id"] == demo_user.organization_id
    assert result.items == []
