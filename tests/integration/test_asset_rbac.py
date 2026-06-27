from uuid import uuid4

import pytest
from app.core.errors import AuthorizationError
from app.schemas.assets import AssetCreate, AssetUpdate
from app.services import tenant_assets


class DummySession:
    """Placeholder session for RBAC tests that fail before persistence."""


@pytest.mark.asyncio
async def test_viewer_mutations_are_denied(viewer_user) -> None:
    with pytest.raises(AuthorizationError):
        await tenant_assets.create_asset(
            DummySession(), viewer_user, AssetCreate(type="domain", value="example.com")
        )

    with pytest.raises(AuthorizationError):
        await tenant_assets.update_asset(
            DummySession(), viewer_user, uuid4(), AssetUpdate(status="stale")
        )

    with pytest.raises(AuthorizationError):
        await tenant_assets.delete_asset(DummySession(), viewer_user, uuid4())


@pytest.mark.asyncio
async def test_analyst_delete_is_denied(demo_user) -> None:
    with pytest.raises(AuthorizationError):
        await tenant_assets.delete_asset(DummySession(), demo_user, uuid4())
