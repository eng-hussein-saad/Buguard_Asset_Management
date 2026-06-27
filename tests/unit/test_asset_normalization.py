import pytest
from app.models.asset import AssetType
from app.schemas.assets import AssetCreate, AssetUpdate
from app.services.tenant_assets import normalize_asset_value


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
