import pytest
from app.schemas.assets import AssetImportBatch
from app.services import tenant_assets


class FakeSession:
    """Records whether import work committed."""

    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    async def commit(self) -> None:
        """Mark the fake transaction as committed."""
        self.committed = True

    async def rollback(self) -> None:
        """Mark the fake transaction as rolled back."""
        self.rolled_back = True


@pytest.mark.asyncio
async def test_sample_shaped_import_creates_parent_and_covers_relationships(
    demo_user, asset_factory, monkeypatch
) -> None:
    stored_assets = {
        ("domain", "example.com"): asset_factory(
            demo_user.organization_id, asset_type="domain", value="example.com"
        ),
        ("subdomain", "api.example.com"): asset_factory(
            demo_user.organization_id, asset_type="subdomain", value="api.example.com"
        ),
        ("certificate", "cert-api"): asset_factory(
            demo_user.organization_id, asset_type="certificate", value="cert-api"
        ),
    }
    created_relationships = []

    async def fake_observe(session, organization_id, **kwargs):
        key = (kwargs["asset_type"], kwargs["value"])
        return stored_assets[key], True

    async def fake_duplicate(*args):
        return None

    async def fake_create_relationship(
        session,
        organization_id,
        source_asset_id,
        target_asset_id,
        relationship_type,
        metadata=None,
    ):
        created_relationships.append(
            (source_asset_id, target_asset_id, relationship_type)
        )

    monkeypatch.setattr(tenant_assets, "observe_asset", fake_observe)
    monkeypatch.setattr(
        tenant_assets.relationship_repository,
        "get_duplicate_for_organization",
        fake_duplicate,
    )
    monkeypatch.setattr(
        tenant_assets.relationship_repository,
        "create_relationship",
        fake_create_relationship,
    )

    summary = await tenant_assets.import_assets(
        FakeSession(),
        demo_user,
        AssetImportBatch(
            items=[
                {"id": "a1", "type": "domain", "value": "example.com"},
                {
                    "id": "a2",
                    "type": "subdomain",
                    "value": "api.example.com",
                    "parent": "a1",
                },
                {
                    "id": "a3",
                    "type": "certificate",
                    "value": "cert-api",
                    "metadata": {"expires": "2026-07-15"},
                    "covers": "a2",
                },
            ]
        ),
    )

    assert summary.created == 3
    assert summary.failed == 0
    assert summary.relationships_created == 2
    assert [item[2] for item in created_relationships] == ["parent", "covers"]
