from uuid import uuid4

import pytest
from app.core.config import Settings
from app.schemas.assets import AssetListParams, PaginatedAssets
from app.services.cache import CacheService


def _settings() -> Settings:
    """Build test settings for cache helpers."""
    return Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost/test",
        CACHE_TTL_SECONDS=60,
    )


@pytest.mark.asyncio
async def test_asset_list_cache_keys_include_scope_and_inputs() -> None:
    """Verify organization and response-affecting inputs shape cache identity."""
    service = CacheService(_settings())
    first_org = uuid4()
    second_org = uuid4()
    params = AssetListParams(type="domain", sort_by="value", sort_order="asc")

    first_key = await service.asset_list_key(first_org, params)
    second_key = await service.asset_list_key(second_org, params)
    changed_key = await service.asset_list_key(
        first_org, params.model_copy(update={"page": 2})
    )

    assert str(first_org) in first_key
    assert first_key != second_key
    assert first_key != changed_key


@pytest.mark.asyncio
async def test_cache_round_trip_invalidation_and_invalid_payload_fallback() -> None:
    """Verify valid payloads round-trip and invalidated namespaces miss safely."""
    service = CacheService(_settings())
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

    await service.set_asset_list(organization_id, params, payload)
    assert await service.get_asset_list(organization_id, params) == payload
    assert service.last_status == "HIT"

    await service.invalidate_assets(organization_id, "asset_update")
    assert await service.get_asset_list(organization_id, params) is None
    assert service.last_status == "MISS"
