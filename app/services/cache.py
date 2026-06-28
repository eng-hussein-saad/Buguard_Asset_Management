from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ValidationError

from app.core.config import Settings
from app.schemas.assets import AssetGraph, AssetListParams, PaginatedAssets

logger = logging.getLogger(__name__)
_MEMORY_CACHE: dict[str, str] = {}
_MEMORY_NAMESPACES: dict[str, int] = {}
CacheStatus = Literal["HIT", "MISS", "BYPASS"]


class CacheService:
    """Caches organization-scoped read responses with graceful fallback."""

    def __init__(self, settings: Settings, store: Any | None = None) -> None:
        """Create a cache service using an optional Redis-compatible store."""
        self.settings = settings
        self.store = store
        self.last_status: CacheStatus = "BYPASS"
        self._last_lookup_unavailable = False

    async def get_asset_list(
        self, organization_id: UUID, params: AssetListParams
    ) -> PaginatedAssets | None:
        """Return a cached asset list when a valid scoped payload exists."""
        key = await self.asset_list_key(organization_id, params)
        model = await self._get_model(key, PaginatedAssets)
        if isinstance(model, PaginatedAssets):
            self.last_status = "HIT"
            return model
        self.last_status = "BYPASS" if self._last_lookup_unavailable else "MISS"
        return None

    async def set_asset_list(
        self, organization_id: UUID, params: AssetListParams, payload: PaginatedAssets
    ) -> None:
        """Store a scoped asset list payload if cache storage is available."""
        key = await self.asset_list_key(organization_id, params)
        await self._set_model(key, payload)

    async def get_asset_graph(
        self, organization_id: UUID, asset_id: UUID
    ) -> AssetGraph | None:
        """Return a cached graph when a valid scoped payload exists."""
        key = await self.asset_graph_key(organization_id, asset_id)
        model = await self._get_model(key, AssetGraph)
        if isinstance(model, AssetGraph):
            self.last_status = "HIT"
            return model
        self.last_status = "BYPASS" if self._last_lookup_unavailable else "MISS"
        return None

    async def set_asset_graph(
        self, organization_id: UUID, asset_id: UUID, payload: AssetGraph
    ) -> None:
        """Store a scoped graph payload if cache storage is available."""
        key = await self.asset_graph_key(organization_id, asset_id)
        await self._set_model(key, payload)

    async def invalidate_assets(self, organization_id: UUID, reason: str) -> None:
        """Invalidate all cached asset and graph reads for one organization."""
        try:
            for namespace in ("asset_list", "asset_graph"):
                key = self._namespace_key(namespace, organization_id)
                if self.store is not None:
                    try:
                        await self.store.incr(key)
                        continue
                    except Exception:
                        pass
                _MEMORY_NAMESPACES[key] = _MEMORY_NAMESPACES.get(key, 0) + 1
            logger.info(
                "Invalidated asset cache namespaces",
                extra={"organization_id": str(organization_id), "reason": reason},
            )
        except Exception:
            logger.info("Cache invalidation unavailable", extra={"reason": reason})

    async def namespace_version(self, namespace: str, organization_id: UUID) -> int:
        """Return the current organization namespace version for cache keys."""
        key = self._namespace_key(namespace, organization_id)
        if self.store is not None:
            try:
                value = await self.store.get(key)
                return int(value or 0)
            except Exception:
                pass
        return _MEMORY_NAMESPACES.get(key, 0)

    async def asset_list_key(
        self, organization_id: UUID, params: AssetListParams
    ) -> str:
        """Build an organization and query scoped asset-list cache key."""
        version = await self.namespace_version("asset_list", organization_id)
        payload = params.model_dump(mode="json")
        return self._key("asset_list", organization_id, version, payload)

    async def asset_graph_key(self, organization_id: UUID, asset_id: UUID) -> str:
        """Build an organization and center-asset scoped graph cache key."""
        version = await self.namespace_version("asset_graph", organization_id)
        return self._key(
            "asset_graph", organization_id, version, {"asset_id": str(asset_id)}
        )

    async def _get_model(
        self, key: str, model_type: type[BaseModel]
    ) -> BaseModel | None:
        """Deserialize and validate one cached model payload."""
        try:
            raw = await self._get_raw(key)
            if raw is None:
                return None
            return model_type.model_validate_json(raw)
        except (ValidationError, ValueError, TypeError):
            logger.info("Ignoring invalid cached payload", extra={"cache_key": key})
            return None

    async def _set_model(self, key: str, payload: BaseModel) -> None:
        """Serialize and store one cached model payload."""
        raw = payload.model_dump_json()
        try:
            if self.store is not None:
                try:
                    await self.store.set(key, raw, ex=self.settings.cache_ttl_seconds)
                    return
                except Exception:
                    logger.info(
                        "External cache set unavailable", extra={"cache_key": key}
                    )
                    return
            _MEMORY_CACHE[key] = raw
        except Exception:
            logger.info("Cache set unavailable", extra={"cache_key": key})

    async def _get_raw(self, key: str) -> str | None:
        """Read raw JSON from Redis or the in-process fallback cache."""
        self._last_lookup_unavailable = False
        if self.store is not None:
            try:
                value = await self.store.get(key)
                if isinstance(value, bytes):
                    return value.decode()
                if isinstance(value, str):
                    return value
            except Exception:
                self._last_lookup_unavailable = True
                logger.info("External cache get unavailable", extra={"cache_key": key})
                return None
        return _MEMORY_CACHE.get(key)

    def _namespace_key(self, namespace: str, organization_id: UUID) -> str:
        """Build the namespace-version key for one organization."""
        return f"cache-ns:{namespace}:{organization_id}"

    def _key(
        self,
        cache_type: str,
        organization_id: UUID,
        version: int,
        inputs: dict[str, Any],
    ) -> str:
        """Build a stable hashed cache key that includes tenant scope."""
        stable_inputs = json.dumps(inputs, sort_keys=True, separators=(",", ":"))
        input_hash = hashlib.sha256(stable_inputs.encode()).hexdigest()
        return f"cache:{cache_type}:{organization_id}:v{version}:{input_hash}"
