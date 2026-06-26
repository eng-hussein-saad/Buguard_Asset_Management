from uuid import uuid4

import pytest
from app.core.errors import NotFoundError
from app.models.user import User
from app.services import tenant_assets


@pytest.mark.asyncio
async def test_cross_organization_asset_access_returns_not_found(monkeypatch) -> None:
    organization_id = uuid4()
    other_asset_id = uuid4()
    user = User(
        id=uuid4(),
        organization_id=organization_id,
        email="admin@example.com",
        password_hash="hash",
        role="admin",
        is_active=True,
    )

    async def fake_get_for_organization(session, scoped_org_id, asset_id):
        assert scoped_org_id == organization_id
        assert asset_id == other_asset_id
        return None

    monkeypatch.setattr(
        tenant_assets.asset_repository,
        "get_for_organization",
        fake_get_for_organization,
    )

    with pytest.raises(NotFoundError):
        await tenant_assets.get_owned_asset(None, user, other_asset_id)


@pytest.mark.asyncio
async def test_cross_organization_relationship_is_rejected(monkeypatch) -> None:
    organization_id = uuid4()
    user = User(
        id=uuid4(),
        organization_id=organization_id,
        email="analyst@example.com",
        password_hash="hash",
        role="analyst",
        is_active=True,
    )

    async def fake_get_for_organization(session, scoped_org_id, asset_id):
        return None

    monkeypatch.setattr(
        tenant_assets.asset_repository,
        "get_for_organization",
        fake_get_for_organization,
    )

    with pytest.raises(NotFoundError):
        await tenant_assets.create_owned_relationship(
            None,
            user,
            uuid4(),
            uuid4(),
            "resolves_to",
        )
