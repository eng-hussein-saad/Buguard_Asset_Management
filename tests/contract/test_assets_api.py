from pathlib import Path
from uuid import uuid4

import pytest
from app.api.deps import get_current_user, get_db
from app.models.asset import AssetStatus, AssetType
from app.schemas.assets import (
    AssetGraph,
    AssetImportSummary,
    AssetRead,
    GraphAsset,
    PaginatedAssets,
    RelationshipList,
    RelationshipRead,
)
from app.services import tenant_assets
from httpx import ASGITransport, AsyncClient


class DummySession:
    """Minimal async session used when route tests patch service behavior."""

    async def commit(self) -> None:
        """Pretend to commit a transaction."""


async def _client(app_instance, user):
    """Create an ASGI client with auth and database dependencies overridden."""
    app_instance.dependency_overrides[get_current_user] = lambda: user
    app_instance.dependency_overrides[get_db] = lambda: DummySession()
    return AsyncClient(
        transport=ASGITransport(app=app_instance), base_url="http://testserver"
    )


def test_assets_openapi_contract_is_exposed(app_instance) -> None:
    generated = app_instance.openapi()
    contract = Path("specs/003-asset-crud/contracts/assets-api.yaml").read_text()

    for path in ("/assets", "/assets/{asset_id}"):
        assert path in generated["paths"]
        assert path in contract
    assert "/assets/import" in generated["paths"]
    assert "/relationships" in generated["paths"]
    assert "/assets/{asset_id}/graph" in generated["paths"]
    assert "/assets/{asset_id}/graph/view" in generated["paths"]

    assets_path = generated["paths"]["/assets"]
    asset_detail_path = generated["paths"]["/assets/{asset_id}"]
    assert assets_path["post"]["tags"] == ["Assets"]
    assert (
        assets_path["post"]["summary"]
        == "Create or refresh one organization-owned asset observation"
    )
    assert (
        generated["paths"]["/assets/import"]["post"]["summary"]
        == "Import organization-owned asset observations"
    )
    assert assets_path["get"]["summary"] == "List organization-owned assets"
    assert asset_detail_path["get"]["summary"] == "Get one organization-owned asset"
    assert (
        asset_detail_path["patch"]["summary"]
        == "Update one organization-owned asset, including marking stale"
    )
    assert (
        asset_detail_path["delete"]["summary"]
        == "Hard delete one organization-owned asset"
    )
    assert (
        generated["paths"]["/relationships"]["post"]["summary"]
        == "Create an organization-owned asset relationship"
    )
    assert (
        generated["paths"]["/relationships"]["get"]["summary"]
        == "List organization-owned asset relationships"
    )
    assert (
        generated["paths"]["/assets/{asset_id}/graph"]["get"]["summary"]
        == "Retrieve a one-hop graph centered on one organization-owned asset"
    )
    assert (
        generated["paths"]["/assets/{asset_id}/graph/view"]["get"]["responses"]["200"][
            "content"
        ]["text/html"]["schema"]["type"]
        == "string"
    )


@pytest.mark.asyncio
async def test_asset_crud_route_response_shapes(
    app_instance, demo_user, asset_factory, monkeypatch
) -> None:
    asset = asset_factory(demo_user.organization_id)
    response_body = AssetRead.from_model(asset)

    async def fake_create(session, current_user, payload, cache_service=None):
        assert payload.value == " Example.COM "
        return response_body, True

    async def fake_read(session, current_user, asset_id):
        assert asset_id == asset.id
        return response_body

    async def fake_update(session, current_user, asset_id, payload, cache_service=None):
        assert payload.status == AssetStatus.STALE
        return response_body.model_copy(update={"status": AssetStatus.STALE})

    async def fake_delete(session, current_user, asset_id, cache_service=None):
        assert asset_id == asset.id

    monkeypatch.setattr(tenant_assets, "create_asset", fake_create)
    monkeypatch.setattr(tenant_assets, "read_asset", fake_read)
    monkeypatch.setattr(tenant_assets, "update_asset", fake_update)
    monkeypatch.setattr(tenant_assets, "delete_asset", fake_delete)

    async with await _client(app_instance, demo_user) as client:
        create = await client.post(
            "/assets", json={"type": "domain", "value": " Example.COM "}
        )
        detail = await client.get(f"/assets/{asset.id}")
        update = await client.patch(f"/assets/{asset.id}", json={"status": "stale"})
        delete = await client.delete(f"/assets/{asset.id}")

    assert create.status_code == 201
    assert create.json()["value"] == "example.com"
    assert detail.status_code == 200
    assert update.status_code == 200
    assert update.json()["status"] == "stale"
    assert delete.status_code == 204


@pytest.mark.asyncio
async def test_asset_create_route_returns_ok_when_observation_is_refreshed(
    app_instance, demo_user, asset_factory, monkeypatch
) -> None:
    asset = asset_factory(demo_user.organization_id)

    async def fake_create(session, current_user, payload, cache_service=None):
        return AssetRead.from_model(asset), False

    monkeypatch.setattr(tenant_assets, "create_asset", fake_create)

    async with await _client(app_instance, demo_user) as client:
        response = await client.post(
            "/assets", json={"type": "domain", "value": "example.com"}
        )

    assert response.status_code == 200
    assert response.json()["id"] == str(asset.id)


@pytest.mark.asyncio
async def test_asset_list_query_parameters_and_pagination_metadata(
    app_instance, demo_user, asset_factory, monkeypatch
) -> None:
    asset = asset_factory(demo_user.organization_id, tags=["external"])

    async def fake_list(session, current_user, params, cache_service=None):
        assert params.type == AssetType.DOMAIN
        assert params.status == AssetStatus.ACTIVE
        assert params.tag == "external"
        assert params.source == "manual"
        assert params.value_contains == "example"
        assert params.sort_by == "value"
        assert params.sort_order == "asc"
        assert params.page == 1
        assert params.page_size == 20
        return PaginatedAssets(
            items=[AssetRead.from_model(asset)],
            page=1,
            page_size=20,
            total=1,
            total_pages=1,
            has_next=False,
            has_previous=False,
        )

    monkeypatch.setattr(tenant_assets, "list_assets", fake_list)

    async with await _client(app_instance, demo_user) as client:
        response = await client.get(
            "/assets?type=domain&status=active&tag=external&source=manual"
            "&value_contains=example&sort_by=value&sort_order=asc"
        )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == str(asset.id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"type": "unsupported", "value": "example.com"},
        {"type": "domain", "value": "   "},
        {"type": "domain", "value": "example.com", "organization_id": str(uuid4())},
    ],
)
async def test_asset_create_validation_rejects_invalid_payloads(
    app_instance, demo_user, payload
) -> None:
    async with await _client(app_instance, demo_user) as client:
        response = await client.post("/assets", json=payload)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.asyncio
async def test_asset_import_route_success_and_multistatus_shapes(
    app_instance,
    demo_user,
    import_payload_factory,
    import_summary_assertion,
    monkeypatch,
) -> None:
    async def fake_import(session, current_user, payload, cache_service=None):
        assert payload.items[0]["value"] == "Example.COM"
        return AssetImportSummary(created=1, updated=0, failed=0, errors=[])

    monkeypatch.setattr(tenant_assets, "import_assets", fake_import)

    async with await _client(app_instance, demo_user) as client:
        response = await client.post("/assets/import", json=import_payload_factory())

    assert response.status_code == 200
    import_summary_assertion(response.json(), created=1, updated=0, failed=0)

    async def fake_partial(session, current_user, payload, cache_service=None):
        return AssetImportSummary(
            created=1,
            updated=0,
            failed=1,
            errors=[{"index": 1, "reason": "Asset value must not be blank."}],
        )

    monkeypatch.setattr(tenant_assets, "import_assets", fake_partial)

    async with await _client(app_instance, demo_user) as client:
        partial = await client.post("/assets/import", json=import_payload_factory())

    assert partial.status_code == 207
    import_summary_assertion(partial.json(), created=1, updated=0, failed=1)


@pytest.mark.asyncio
async def test_asset_import_route_all_record_failure_shape(
    app_instance,
    demo_user,
    import_payload_factory,
    import_summary_assertion,
    monkeypatch,
) -> None:
    async def fake_failure(session, current_user, payload, cache_service=None):
        return AssetImportSummary(
            created=0,
            updated=0,
            failed=1,
            errors=[{"index": 0, "reason": "Unsupported asset type."}],
        )

    monkeypatch.setattr(tenant_assets, "import_assets", fake_failure)

    async with await _client(app_instance, demo_user) as client:
        response = await client.post("/assets/import", json=import_payload_factory())

    assert response.status_code == 422
    import_summary_assertion(response.json(), created=0, updated=0, failed=1)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    ["sort_by=bad", "sort_order=sideways", "page=0", "page_size=0", "page_size=101"],
)
async def test_asset_list_validation_rejects_invalid_query(
    app_instance, demo_user, query
) -> None:
    async with await _client(app_instance, demo_user) as client:
        response = await client.get(f"/assets?{query}")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.asyncio
async def test_relationship_routes_response_shapes(
    app_instance,
    demo_user,
    asset_factory,
    relationship_factory,
    relationship_payload_factory,
    monkeypatch,
) -> None:
    source = asset_factory(demo_user.organization_id, value="example.com")
    target = asset_factory(demo_user.organization_id, value="api.example.com")
    relationship = relationship_factory(demo_user.organization_id, source.id, target.id)
    relationship_response = RelationshipRead.from_model(relationship)

    async def fake_create(session, current_user, payload, cache_service=None):
        assert payload.source_asset_id == source.id
        return relationship_response

    async def fake_list(session, current_user):
        return RelationshipList(items=[relationship_response])

    monkeypatch.setattr(tenant_assets, "create_owned_relationship", fake_create)
    monkeypatch.setattr(tenant_assets, "list_relationships", fake_list)

    async with await _client(app_instance, demo_user) as client:
        create = await client.post(
            "/relationships",
            json=relationship_payload_factory(source.id, target.id),
        )
        list_response = await client.get("/relationships")

    assert create.status_code == 201
    assert create.json()["id"] == str(relationship.id)
    assert "organization_id" not in create.json()
    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["id"] == str(relationship.id)


@pytest.mark.asyncio
async def test_graph_routes_response_shapes(
    app_instance,
    demo_user,
    asset_factory,
    monkeypatch,
) -> None:
    asset = asset_factory(demo_user.organization_id, value="example.com")
    graph = AssetGraph(
        center=GraphAsset.from_model(asset),
        nodes=[GraphAsset.from_model(asset)],
        edges=[],
    )

    async def fake_graph(session, current_user, asset_id, cache_service=None):
        assert asset_id == asset.id
        return graph

    monkeypatch.setattr(tenant_assets, "get_asset_graph", fake_graph)

    async with await _client(app_instance, demo_user) as client:
        graph_response = await client.get(f"/assets/{asset.id}/graph")
        view_response = await client.get(f"/assets/{asset.id}/graph/view")

    assert graph_response.status_code == 200
    assert graph_response.json()["center"]["id"] == str(asset.id)
    assert view_response.status_code == 200
    assert 'id="token"' in view_response.text
    assert "localStorage" in view_response.text
    assert "Authorization: `Bearer ${accessToken}`" in view_response.text
    assert "/assets/${assetId}/graph" in view_response.text
