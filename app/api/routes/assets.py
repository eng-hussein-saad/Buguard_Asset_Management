from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_cache_service, get_current_user, get_db, get_rate_limiter
from app.models.asset import AssetStatus, AssetType
from app.models.user import User
from app.schemas.assets import (
    AssetCreate,
    AssetGraph,
    AssetImportBatch,
    AssetImportSummary,
    AssetListParams,
    AssetRead,
    AssetSortField,
    AssetUpdate,
    ErrorResponse,
    PaginatedAssets,
    RelationshipCreate,
    RelationshipList,
    RelationshipRead,
    SortOrder,
)
from app.services import tenant_assets
from app.services.cache import CacheService
from app.services.rate_limits import (
    BULK_IMPORT,
    RateLimitService,
    authenticated_effective_caller,
)
from app.services.rbac import Permission, require_permission

router = APIRouter(prefix="/assets", tags=["Assets"])
relationships_router = APIRouter(prefix="/relationships", tags=["Relationships"])

ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorResponse, "description": "Invalid request."},
    401: {"model": ErrorResponse, "description": "Missing or invalid access token."},
    403: {"model": ErrorResponse, "description": "User role cannot perform action."},
    404: {"model": ErrorResponse, "description": "Asset was not found."},
    409: {"model": ErrorResponse, "description": "Asset already exists."},
    429: {"model": ErrorResponse, "description": "Request rate limit exceeded."},
}

RELATIONSHIP_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorResponse, "description": "Invalid relationship payload."},
    401: {"model": ErrorResponse, "description": "Missing or invalid access token."},
    403: {
        "model": ErrorResponse,
        "description": "User role cannot create relationships.",
    },
    404: {"model": ErrorResponse, "description": "Asset was not found."},
    409: {"model": ErrorResponse, "description": "Relationship already exists."},
}


def list_params(
    asset_type: Annotated[AssetType | None, Query(alias="type")] = None,
    status_value: Annotated[AssetStatus | None, Query(alias="status")] = None,
    tag: Annotated[str | None, Query(min_length=1)] = None,
    source: Annotated[str | None, Query(min_length=1)] = None,
    value_contains: Annotated[str | None, Query(min_length=1)] = None,
    sort_by: AssetSortField = "created_at",
    sort_order: SortOrder = "desc",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AssetListParams:
    """Collect query parameters into the validated asset list schema."""
    return AssetListParams(
        type=asset_type,
        status=status_value,
        tag=tag,
        source=source,
        value_contains=value_contains,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create or refresh one organization-owned asset observation",
    responses={
        code: response for code, response in ERROR_RESPONSES.items() if code != 404
    },
)
async def create_asset(
    payload: AssetCreate,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    cache_service: Annotated[CacheService, Depends(get_cache_service)],
) -> AssetRead:
    """Create a new asset or refresh an existing observation lifecycle."""
    asset, created = await tenant_assets.create_asset(
        session, current_user, payload, cache_service
    )
    if not created:
        response.status_code = status.HTTP_200_OK
    return asset


@router.get(
    "",
    response_model=PaginatedAssets,
    summary="List organization-owned assets",
    responses={
        code: response
        for code, response in ERROR_RESPONSES.items()
        if code in {400, 401}
    },
)
async def list_assets(
    params: Annotated[AssetListParams, Depends(list_params)],
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    cache_service: Annotated[CacheService, Depends(get_cache_service)],
) -> PaginatedAssets:
    """List filtered and paginated assets for the current organization."""
    payload = await tenant_assets.list_assets(
        session, current_user, params, cache_service
    )
    response.headers["X-Cache"] = cache_service.last_status
    return payload


@router.post(
    "/import",
    response_model=AssetImportSummary,
    summary="Import organization-owned asset observations",
    responses={
        **{
            code: response
            for code, response in ERROR_RESPONSES.items()
            if code in {400, 401, 403, 429}
        },
        207: {
            "model": AssetImportSummary,
            "description": "At least one record was accepted and at least one failed.",
        },
        422: {
            "model": AssetImportSummary,
            "description": "Well-formed batch had no accepted records.",
        },
    },
)
async def import_assets(
    payload: AssetImportBatch,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    rate_limiter: Annotated[RateLimitService, Depends(get_rate_limiter)],
    cache_service: Annotated[CacheService, Depends(get_cache_service)],
) -> AssetImportSummary:
    """Import assets idempotently and return a stable lifecycle summary."""
    require_permission(current_user.role, Permission.BULK_IMPORT)
    await rate_limiter.check(
        BULK_IMPORT,
        authenticated_effective_caller(current_user.id, current_user.organization_id),
    )
    summary = await tenant_assets.import_assets(
        session, current_user, payload, cache_service
    )
    response.status_code = tenant_assets.import_status_code(summary)
    return summary


@router.get(
    "/{asset_id}",
    response_model=AssetRead,
    summary="Get one organization-owned asset",
    responses={
        code: response
        for code, response in ERROR_RESPONSES.items()
        if code in {401, 404}
    },
)
async def get_asset(
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AssetRead:
    """Read one asset without accepting client-supplied ownership."""
    return await tenant_assets.read_asset(session, current_user, asset_id)


@router.patch(
    "/{asset_id}",
    response_model=AssetRead,
    summary="Update one organization-owned asset, including marking stale",
    responses=ERROR_RESPONSES,
)
async def update_asset(
    asset_id: UUID,
    payload: AssetUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    cache_service: Annotated[CacheService, Depends(get_cache_service)],
) -> AssetRead:
    """Update an asset while preserving authenticated organization ownership."""
    return await tenant_assets.update_asset(
        session, current_user, asset_id, payload, cache_service
    )


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hard delete one organization-owned asset",
    responses={
        code: response
        for code, response in ERROR_RESPONSES.items()
        if code in {401, 403, 404}
    },
)
async def delete_asset(
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    cache_service: Annotated[CacheService, Depends(get_cache_service)],
) -> Response:
    """Permanently delete an asset from the authenticated organization."""
    await tenant_assets.delete_asset(session, current_user, asset_id, cache_service)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{asset_id}/graph",
    response_model=AssetGraph,
    summary="Retrieve a one-hop graph centered on one organization-owned asset",
    responses={
        code: response
        for code, response in RELATIONSHIP_ERROR_RESPONSES.items()
        if code in {401, 404}
    },
)
async def get_asset_graph(
    asset_id: UUID,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    cache_service: Annotated[CacheService, Depends(get_cache_service)],
) -> AssetGraph:
    """Return center, directly connected nodes, and directly connected edges."""
    graph = await tenant_assets.get_asset_graph(
        session, current_user, asset_id, cache_service
    )
    response.headers["X-Cache"] = cache_service.last_status
    return graph


def _graph_view_html(asset_id: UUID) -> str:
    """Render the simple endpoint-driven graph visualization shell."""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Buguard Asset Graph</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #111827; }}
    main {{ max-width: 960px; margin: 0 auto; }}
    form {{
      display: grid;
      gap: 0.75rem;
      grid-template-columns: minmax(0, 1fr) auto;
      margin: 1rem 0;
    }}
    input {{
      border: 1px solid #cbd5e1;
      font: inherit;
      min-width: 0;
      padding: 0.65rem 0.75rem;
    }}
    button {{
      background: #0f766e;
      border: 1px solid #0f766e;
      color: white;
      cursor: pointer;
      font: inherit;
      padding: 0.65rem 1rem;
    }}
    svg {{ width: 100%; height: 520px; border: 1px solid #d1d5db; }}
    .node {{ fill: #0f766e; }}
    .edge {{ stroke: #64748b; stroke-width: 2; }}
    text {{ font-size: 13px; fill: #111827; }}
    pre {{ background: #f3f4f6; padding: 1rem; overflow: auto; }}
    @media (max-width: 640px) {{
      body {{ margin: 1rem; }}
      form {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main>
    <h1>Asset Graph</h1>
    <form id="token-form">
      <input
        id="token"
        name="token"
        type="password"
        autocomplete="off"
        placeholder="Bearer access token"
        aria-label="Bearer access token"
      >
      <button type="submit">Load Graph</button>
    </form>
    <p id="status">Paste a bearer access token to load graph for {asset_id}.</p>
    <svg id="graph" role="img" aria-label="Asset relationship graph"></svg>
    <pre id="error" hidden></pre>
  </main>
  <script>
    const assetId = "{asset_id}";
    const storageKey = "buguardGraphAccessToken";
    const form = document.getElementById("token-form");
    const tokenInput = document.getElementById("token");
    const graph = document.getElementById("graph");
    const statusEl = document.getElementById("status");
    const errorEl = document.getElementById("error");
    const queryToken = new URLSearchParams(window.location.search).get("token");
    tokenInput.value = queryToken || localStorage.getItem(storageKey) || "";

    function draw(payload) {{
      graph.innerHTML = "";
      errorEl.hidden = true;
      const width = graph.clientWidth || 900;
      const height = graph.clientHeight || 520;
      const cx = width / 2;
      const cy = height / 2;
      const radius = Math.min(width, height) / 3;
      const positions = new Map();
      payload.nodes.forEach((node, index) => {{
        if (node.id === payload.center.id) {{
          positions.set(node.id, [cx, cy]);
          return;
        }}
        const divisor = Math.max(payload.nodes.length - 1, 1);
        const angle = (2 * Math.PI * index) / divisor;
        const x = cx + radius * Math.cos(angle);
        const y = cy + radius * Math.sin(angle);
        positions.set(node.id, [x, y]);
      }});
      payload.edges.forEach((edge) => {{
        const source = positions.get(edge.source_asset_id);
        const target = positions.get(edge.target_asset_id);
        if (!source || !target) return;
        const midX = (source[0] + target[0]) / 2;
        const midY = (source[1] + target[1]) / 2 - 8;
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("class", "edge");
        line.setAttribute("x1", source[0]);
        line.setAttribute("y1", source[1]);
        line.setAttribute("x2", target[0]);
        line.setAttribute("y2", target[1]);
        graph.appendChild(line);
        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("x", midX);
        label.setAttribute("y", midY);
        label.setAttribute("text-anchor", "middle");
        label.textContent = edge.label;
        graph.appendChild(label);
      }});
      payload.nodes.forEach((node) => {{
        const pos = positions.get(node.id);
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("class", "node");
        circle.setAttribute("cx", pos[0]);
        circle.setAttribute("cy", pos[1]);
        circle.setAttribute("r", 24);
        graph.appendChild(circle);
        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("x", pos[0]);
        label.setAttribute("y", pos[1] + 44);
        label.setAttribute("text-anchor", "middle");
        label.textContent = node.label;
        graph.appendChild(label);
      }});
      statusEl.textContent =
        `${{payload.nodes.length}} nodes, ${{payload.edges.length}} edges`;
    }}

    function normalizeToken(value) {{
      return value.trim().replace(/^Bearer\\s+/i, "");
    }}

    function loadGraph(token) {{
      const accessToken = normalizeToken(token);
      if (!accessToken) {{
        statusEl.textContent =
          "Paste a bearer access token to load graph for {asset_id}.";
        return;
      }}
      localStorage.setItem(storageKey, accessToken);
      statusEl.textContent = `Loading graph for ${{assetId}}...`;
      graph.innerHTML = "";
      errorEl.hidden = true;
      fetch(`/assets/${{assetId}}/graph`, {{
        headers: {{ Authorization: `Bearer ${{accessToken}}` }},
      }})
        .then(async (response) => {{
          const payload = await response.json();
          if (!response.ok) throw payload;
          return payload;
        }})
        .then(draw)
        .catch((error) => {{
          statusEl.textContent = "Graph could not be loaded.";
          errorEl.hidden = false;
          errorEl.textContent = JSON.stringify(error, null, 2);
        }});
    }}

    form.addEventListener("submit", (event) => {{
      event.preventDefault();
      loadGraph(tokenInput.value);
    }});

    if (tokenInput.value) {{
      loadGraph(tokenInput.value);
    }}
  </script>
</body>
</html>"""


@router.get(
    "/{asset_id}/graph/view",
    response_class=HTMLResponse,
    summary="Render a simple endpoint-driven graph visualization",
)
async def view_asset_graph(asset_id: UUID) -> HTMLResponse:
    """Return a dev-friendly HTML shell that fetches protected graph data."""
    return HTMLResponse(_graph_view_html(asset_id))


@relationships_router.post(
    "",
    response_model=RelationshipRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an organization-owned asset relationship",
    responses=RELATIONSHIP_ERROR_RESPONSES,
)
async def create_relationship(
    payload: RelationshipCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    cache_service: Annotated[CacheService, Depends(get_cache_service)],
) -> RelationshipRead:
    """Create a typed relationship between two current-organization assets."""
    return await tenant_assets.create_owned_relationship(
        session, current_user, payload, cache_service
    )


@relationships_router.get(
    "",
    response_model=RelationshipList,
    summary="List organization-owned asset relationships",
    responses={
        code: response
        for code, response in RELATIONSHIP_ERROR_RESPONSES.items()
        if code in {401}
    },
)
async def list_relationships(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RelationshipList:
    """List relationships visible to the authenticated organization."""
    return await tenant_assets.list_relationships(session, current_user)
