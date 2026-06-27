import pytest
from app.models.asset import AssetStatus, AssetType
from app.schemas.assets import AssetListParams
from app.services import tenant_assets


class DummySession:
    """Placeholder session for mocked list tests."""


@pytest.mark.asyncio
async def test_filters_sorting_and_pagination_are_passed_to_repository(
    demo_user, asset_factory, monkeypatch
) -> None:
    captured = {}
    asset = asset_factory(demo_user.organization_id)

    async def fake_count(session, organization_id, params):
        captured["count_org"] = organization_id
        captured["params"] = params
        return 1

    async def fake_list(session, organization_id, params):
        captured["list_org"] = organization_id
        return [asset]

    monkeypatch.setattr(
        tenant_assets.asset_repository, "count_for_organization", fake_count
    )
    monkeypatch.setattr(
        tenant_assets.asset_repository, "list_for_organization", fake_list
    )

    result = await tenant_assets.list_assets(
        DummySession(),
        demo_user,
        AssetListParams(
            type=AssetType.DOMAIN,
            status=AssetStatus.ACTIVE,
            tag="external",
            source="manual",
            value_contains=" Example ",
            sort_by="value",
            sort_order="asc",
            page=1,
            page_size=20,
        ),
    )

    assert captured["count_org"] == demo_user.organization_id
    assert captured["list_org"] == demo_user.organization_id
    assert captured["params"].value_contains == "example"
    assert result.total == 1
    assert result.total_pages == 1
    assert not result.has_next
    assert not result.has_previous


def test_pagination_bounds_are_validated() -> None:
    with pytest.raises(ValueError):
        AssetListParams(page=0)
    with pytest.raises(ValueError):
        AssetListParams(page_size=0)
    with pytest.raises(ValueError):
        AssetListParams(page_size=101)


@pytest.mark.asyncio
async def test_empty_results_have_zero_total_pages(demo_user, monkeypatch) -> None:
    async def fake_count(*args):
        return 0

    async def fake_list(*args):
        return []

    monkeypatch.setattr(
        tenant_assets.asset_repository, "count_for_organization", fake_count
    )
    monkeypatch.setattr(
        tenant_assets.asset_repository, "list_for_organization", fake_list
    )

    result = await tenant_assets.list_assets(
        DummySession(), demo_user, AssetListParams()
    )
    assert result.items == []
    assert result.total == 0
    assert result.total_pages == 0
