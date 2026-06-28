from uuid import uuid4

import pytest
from app.core.errors import AssetNotFoundError, DuplicateRelationshipError
from app.schemas.assets import RelationshipCreate
from app.services import tenant_assets


class FakeSession:
    """Tracks transaction boundaries for relationship service tests."""

    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    async def commit(self) -> None:
        """Record a committed transaction."""
        self.committed = True

    async def rollback(self) -> None:
        """Record a rolled-back transaction."""
        self.rolled_back = True


@pytest.mark.asyncio
async def test_analyst_and_admin_can_create_relationships(
    demo_user, admin_user, asset_factory, relationship_factory, monkeypatch
) -> None:
    for current_user in (demo_user, admin_user):
        session = FakeSession()
        source = asset_factory(current_user.organization_id, value="example.com")
        target = asset_factory(
            current_user.organization_id, asset_type="ip_address", value="192.0.2.10"
        )
        stored = relationship_factory(
            current_user.organization_id,
            source.id,
            target.id,
            metadata={"confidence": "manual"},
        )
        assets_by_id = {source.id: source, target.id: target}
        organization_id = current_user.organization_id

        async def fake_get(
            session,
            requested_organization_id,
            asset_id,
            *,
            expected_org=organization_id,
            assets=assets_by_id,
        ):
            assert requested_organization_id == expected_org
            return assets.get(asset_id)

        async def fake_duplicate(*args):
            return None

        async def fake_create(
            session,
            organization_id,
            source_asset_id,
            target_asset_id,
            relationship_type,
            metadata=None,
            *,
            stored_relationship=stored,
        ):
            assert organization_id == stored_relationship.organization_id
            assert metadata == {"confidence": "manual"}
            return stored_relationship

        monkeypatch.setattr(
            tenant_assets.asset_repository, "get_for_organization", fake_get
        )
        monkeypatch.setattr(
            tenant_assets.relationship_repository,
            "get_duplicate_for_organization",
            fake_duplicate,
        )
        monkeypatch.setattr(
            tenant_assets.relationship_repository, "create_relationship", fake_create
        )

        result = await tenant_assets.create_owned_relationship(
            session,
            current_user,
            RelationshipCreate(
                source_asset_id=source.id,
                target_asset_id=target.id,
                relationship_type="resolves_to",
                metadata={"confidence": "manual"},
            ),
        )

        assert result.source_asset_id == source.id
        assert result.target_asset_id == target.id
        assert result.metadata == {"confidence": "manual"}
        assert session.committed


@pytest.mark.asyncio
async def test_duplicate_relationship_returns_conflict_without_creating(
    demo_user, asset_factory, relationship_factory, monkeypatch
) -> None:
    source = asset_factory(demo_user.organization_id)
    target = asset_factory(demo_user.organization_id, value="api.example.com")
    duplicate = relationship_factory(demo_user.organization_id, source.id, target.id)

    async def fake_get(session, organization_id, asset_id):
        return {source.id: source, target.id: target}.get(asset_id)

    async def fake_duplicate(*args):
        return duplicate

    async def fail_create(*args):
        raise AssertionError("duplicate precheck should prevent persistence")

    monkeypatch.setattr(
        tenant_assets.asset_repository, "get_for_organization", fake_get
    )
    monkeypatch.setattr(
        tenant_assets.relationship_repository,
        "get_duplicate_for_organization",
        fake_duplicate,
    )
    monkeypatch.setattr(
        tenant_assets.relationship_repository, "create_relationship", fail_create
    )

    with pytest.raises(DuplicateRelationshipError):
        await tenant_assets.create_owned_relationship(
            FakeSession(),
            demo_user,
            RelationshipCreate(
                source_asset_id=source.id,
                target_asset_id=target.id,
                relationship_type="resolves_to",
            ),
        )


@pytest.mark.asyncio
async def test_missing_source_or_target_assets_return_asset_not_found(
    demo_user, asset_factory, monkeypatch
) -> None:
    source = asset_factory(demo_user.organization_id)
    target_id = uuid4()

    async def fake_get(session, organization_id, asset_id):
        return source if asset_id == source.id else None

    monkeypatch.setattr(
        tenant_assets.asset_repository, "get_for_organization", fake_get
    )

    with pytest.raises(AssetNotFoundError):
        await tenant_assets.create_owned_relationship(
            FakeSession(),
            demo_user,
            RelationshipCreate(
                source_asset_id=source.id,
                target_asset_id=target_id,
                relationship_type="resolves_to",
            ),
        )


def test_relationship_payload_rejects_ownership_and_invalid_types() -> None:
    source_id = uuid4()
    target_id = uuid4()
    with pytest.raises(ValueError):
        RelationshipCreate(
            source_asset_id=source_id,
            target_asset_id=target_id,
            relationship_type="resolves-to",
        )
    with pytest.raises(ValueError):
        RelationshipCreate(
            source_asset_id=source_id,
            target_asset_id=target_id,
            relationship_type="resolves_to",
            organization_id=str(uuid4()),
        )


@pytest.mark.asyncio
async def test_relationship_listing_returns_current_organization_items(
    demo_user, relationship_factory, monkeypatch
) -> None:
    relationship = relationship_factory(demo_user.organization_id, uuid4(), uuid4())

    async def fake_list(session, organization_id):
        assert organization_id == demo_user.organization_id
        return [relationship]

    monkeypatch.setattr(
        tenant_assets.relationship_repository, "list_for_organization", fake_list
    )

    result = await tenant_assets.list_relationships(FakeSession(), demo_user)

    assert len(result.items) == 1
    assert result.items[0].id == relationship.id


@pytest.mark.asyncio
async def test_graph_retrieval_includes_one_hop_nodes_and_edges(
    demo_user,
    asset_factory,
    relationship_factory,
    graph_response_assertion,
    monkeypatch,
) -> None:
    center = asset_factory(demo_user.organization_id, value="example.com")
    direct = asset_factory(demo_user.organization_id, value="api.example.com")
    second_hop = asset_factory(demo_user.organization_id, value="deep.example.com")
    edge = relationship_factory(demo_user.organization_id, center.id, direct.id)
    ignored_edge = relationship_factory(
        demo_user.organization_id, direct.id, second_hop.id
    )
    edge.source_asset = center
    edge.target_asset = direct
    ignored_edge.source_asset = direct
    ignored_edge.target_asset = second_hop

    async def fake_get(session, organization_id, asset_id):
        return center if asset_id == center.id else None

    async def fake_one_hop(session, organization_id, asset_id):
        assert asset_id == center.id
        return [edge]

    monkeypatch.setattr(
        tenant_assets.asset_repository, "get_for_organization", fake_get
    )
    monkeypatch.setattr(
        tenant_assets.relationship_repository, "list_one_hop_for_asset", fake_one_hop
    )

    result = await tenant_assets.get_asset_graph(FakeSession(), demo_user, center.id)
    body = result.model_dump(mode="json")

    graph_response_assertion(body, nodes=2, edges=1)
    assert body["center"]["id"] == str(center.id)
    assert str(second_hop.id) not in {node["id"] for node in body["nodes"]}


@pytest.mark.asyncio
async def test_isolated_asset_graph_returns_center_and_empty_edges(
    demo_user, asset_factory, monkeypatch
) -> None:
    center = asset_factory(demo_user.organization_id, value="isolated.example.com")

    async def fake_get(session, organization_id, asset_id):
        return center

    async def fake_one_hop(session, organization_id, asset_id):
        return []

    monkeypatch.setattr(
        tenant_assets.asset_repository, "get_for_organization", fake_get
    )
    monkeypatch.setattr(
        tenant_assets.relationship_repository, "list_one_hop_for_asset", fake_one_hop
    )

    result = await tenant_assets.get_asset_graph(FakeSession(), demo_user, center.id)

    assert result.center.id == center.id
    assert [node.id for node in result.nodes] == [center.id]
    assert result.edges == []
