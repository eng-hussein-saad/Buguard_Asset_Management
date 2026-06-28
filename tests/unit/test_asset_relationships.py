from uuid import uuid4

from app.schemas.assets import RelationshipCreate
from app.services import tenant_assets


def test_relationship_response_mapping_hides_organization_id(
    demo_user, relationship_factory
) -> None:
    relationship = relationship_factory(demo_user.organization_id, uuid4(), uuid4())

    response = tenant_assets._relationship_read(relationship)

    body = response.model_dump()
    assert "organization_id" not in body
    assert body["relationship_type"].value == "resolves_to"


def test_graph_mapping_uses_asset_values_and_relationship_types(
    demo_user, asset_factory, relationship_factory
) -> None:
    asset = asset_factory(demo_user.organization_id, value="example.com")
    relationship = relationship_factory(
        demo_user.organization_id, asset.id, asset.id, relationship_type="belongs_to"
    )

    node = tenant_assets._graph_asset(asset)
    edge = tenant_assets._graph_edge(relationship)

    assert node.label == "example.com"
    assert edge.label == "belongs_to"


def test_relationship_create_rejects_extra_fields_and_bad_type() -> None:
    source_id = "00000000-0000-0000-0000-000000000001"
    target_id = "00000000-0000-0000-0000-000000000002"

    try:
        RelationshipCreate(
            source_asset_id=source_id,
            target_asset_id=target_id,
            relationship_type="bad",
        )
    except ValueError as exc:
        assert "relationship_type" in str(exc)
    else:
        raise AssertionError("bad relationship type should fail validation")

    try:
        RelationshipCreate(
            source_asset_id=source_id,
            target_asset_id=target_id,
            relationship_type="resolves_to",
            organization_id="00000000-0000-0000-0000-000000000003",
        )
    except ValueError as exc:
        assert "organization_id" in str(exc)
    else:
        raise AssertionError("organization ownership should not be accepted")
