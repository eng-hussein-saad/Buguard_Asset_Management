from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.asset import AssetStatus, AssetType
from app.models.user import User
from app.schemas.assets import (
    AssetCreate,
    AssetListParams,
    AssetRead,
    AssetSortField,
    AssetUpdate,
    ErrorResponse,
    PaginatedAssets,
    SortOrder,
)
from app.services import tenant_assets

router = APIRouter(prefix="/assets", tags=["Assets"])

ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorResponse, "description": "Invalid request."},
    401: {"model": ErrorResponse, "description": "Missing or invalid access token."},
    403: {"model": ErrorResponse, "description": "User role cannot perform action."},
    404: {"model": ErrorResponse, "description": "Asset was not found."},
    409: {"model": ErrorResponse, "description": "Asset already exists."},
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
    summary="Create an organization-owned asset",
    responses={
        code: response for code, response in ERROR_RESPONSES.items() if code != 404
    },
)
async def create_asset(
    payload: AssetCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AssetRead:
    """Create an asset under the authenticated user's organization."""
    return await tenant_assets.create_asset(session, current_user, payload)


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
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PaginatedAssets:
    """List filtered and paginated assets for the current organization."""
    return await tenant_assets.list_assets(session, current_user, params)


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
    summary="Update one organization-owned asset",
    responses=ERROR_RESPONSES,
)
async def update_asset(
    asset_id: UUID,
    payload: AssetUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AssetRead:
    """Update an asset while preserving authenticated organization ownership."""
    return await tenant_assets.update_asset(session, current_user, asset_id, payload)


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
) -> Response:
    """Permanently delete an asset from the authenticated organization."""
    await tenant_assets.delete_asset(session, current_user, asset_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
