import pytest
from app.models.asset import AssetType
from app.schemas.assets import AssetCreate, AssetImportSummary, AssetUpdate
from app.services.tenant_assets import (
    import_status_code,
    merge_import_metadata,
    merge_import_tags,
    normalize_asset_value,
    resolve_import_status,
)


@pytest.mark.parametrize(
    ("asset_type", "raw_value", "expected"),
    [
        ("domain", " Example.COM ", "example.com"),
        ("subdomain", " App.Example.COM ", "app.example.com"),
        ("ip_address", " 192.0.2.10 ", "192.0.2.10"),
        ("service", " HTTPS ", "HTTPS"),
        ("certificate", " Cert-ABC ", "Cert-ABC"),
        ("technology", " Nginx ", "Nginx"),
    ],
)
def test_normalize_asset_value_trims_and_lowercases_domains(
    asset_type: str, raw_value: str, expected: str
) -> None:
    assert normalize_asset_value(asset_type, raw_value) == expected


def test_create_schema_rejects_blank_values() -> None:
    with pytest.raises(ValueError):
        AssetCreate(type=AssetType.DOMAIN, value="   ")


def test_update_schema_rejects_empty_body() -> None:
    with pytest.raises(ValueError):
        AssetUpdate()


def test_import_tag_merge_preserves_order_without_duplicates() -> None:
    assert merge_import_tags(["external", "api"], ["api", "priority"]) == [
        "external",
        "api",
        "priority",
    ]


def test_import_metadata_merge_is_shallow_newest_wins() -> None:
    assert merge_import_metadata(
        {"owner": "security", "tier": "old"}, {"tier": "new", "env": "prod"}
    ) == {"owner": "security", "tier": "new", "env": "prod"}


@pytest.mark.parametrize(
    ("existing", "explicit", "expected"),
    [
        (None, None, "active"),
        ("active", None, "active"),
        ("active", "archived", "archived"),
        ("stale", None, "active"),
        ("archived", None, "archived"),
        ("archived", "active", "active"),
    ],
)
def test_import_lifecycle_status_transitions(existing, explicit, expected) -> None:
    assert resolve_import_status(existing, explicit) == expected


@pytest.mark.parametrize(
    ("summary", "expected"),
    [
        (AssetImportSummary(created=1, updated=0, failed=0), 200),
        (AssetImportSummary(created=1, updated=0, failed=1), 207),
        (AssetImportSummary(created=0, updated=0, failed=1), 422),
    ],
)
def test_import_summary_status_mapping(summary, expected) -> None:
    assert import_status_code(summary) == expected
