from app.db.base import metadata


def test_phase_2_tables_are_registered_with_metadata() -> None:
    assert {
        "organizations",
        "users",
        "refresh_tokens",
        "assets",
        "asset_relationships",
    }.issubset(metadata.tables)


def test_schema_contains_required_uniqueness_and_lookup_indexes() -> None:
    assets = metadata.tables["assets"]
    relationships = metadata.tables["asset_relationships"]

    assert any(
        constraint.name == "uq_assets_org_type_value"
        for constraint in assets.constraints
    )
    assert any(
        constraint.name == "uq_relationships_org_source_target_type"
        for constraint in relationships.constraints
    )
    assert "ix_assets_org_lookup" in {index.name for index in assets.indexes}
    assert "ix_relationships_org_lookup" in {
        index.name for index in relationships.indexes
    }
