from uuid import uuid4

import pytest
from app.core.config import Settings
from app.schemas.assets import AssetListParams, PaginatedAssets
from app.services.cache import CacheService


def _settings() -> Settings:
    """Build settings for cache integration behavior tests."""
    return Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost/test",
        CACHE_TTL_SECONDS=60,
    )


@pytest.mark.asyncio
async def test_asset_list_cache_is_isolated_by_organization() -> None:
    """Verify equivalent list inputs do not share cached tenant payloads."""
    cache = CacheService(_settings())
    first_org = uuid4()
    second_org = uuid4()
    params = AssetListParams(value_contains="shared.example.com")
    first_payload = PaginatedAssets(
        items=[],
        page=1,
        page_size=20,
        total=1,
        total_pages=1,
        has_next=False,
        has_previous=False,
    )
    second_payload = first_payload.model_copy(update={"total": 2})

    await cache.set_asset_list(first_org, params, first_payload)
    await cache.set_asset_list(second_org, params, second_payload)

    assert (await cache.get_asset_list(first_org, params)).total == 1
    assert (await cache.get_asset_list(second_org, params)).total == 2


@pytest.mark.asyncio
async def test_cache_invalidation_and_unavailable_store_fallback() -> None:
    """Verify namespace invalidation misses and broken stores are ignored."""
    cache = CacheService(_settings())
    organization_id = uuid4()
    params = AssetListParams()
    payload = PaginatedAssets(
        items=[],
        page=1,
        page_size=20,
        total=0,
        total_pages=0,
        has_next=False,
        has_previous=False,
    )

    await cache.set_asset_list(organization_id, params, payload)
    assert await cache.get_asset_list(organization_id, params) == payload
    await cache.invalidate_assets(organization_id, "bulk_import")
    assert await cache.get_asset_list(organization_id, params) is None

    class BrokenStore:
        """Store stub that raises to exercise graceful fallback paths."""

        async def get(self, key):
            """Pretend cache reads are unavailable."""
            raise RuntimeError("cache unavailable")

        async def set(self, key, value, ex=None):
            """Pretend cache writes are unavailable."""
            raise RuntimeError("cache unavailable")

        async def incr(self, key):
            """Pretend namespace updates are unavailable."""
            raise RuntimeError("cache unavailable")

    broken_cache = CacheService(_settings(), BrokenStore())
    await broken_cache.set_asset_list(organization_id, params, payload)
    assert await broken_cache.get_asset_list(organization_id, params) == payload
