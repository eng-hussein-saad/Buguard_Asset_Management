from app.schemas.assets import AssetRead, GraphAsset


def test_asset_and_graph_responses_include_certificate_lifecycle(
    asset_factory, demo_user
):
    certificate = asset_factory(
        demo_user.organization_id,
        asset_type="certificate",
        value="cert-api",
    )
    certificate.asset_metadata = {"expires": "2000-01-01"}

    assert AssetRead.from_model(certificate).certificate_lifecycle_status == "expired"
    assert GraphAsset.from_model(certificate).certificate_lifecycle_status == "expired"
