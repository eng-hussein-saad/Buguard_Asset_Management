from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_rate_limiter
from app.core.config import Settings, get_settings
from app.models.user import User
from app.schemas.assets import ErrorResponse
from app.schemas.auth import CurrentUser, LoginRequest, RefreshRequest, TokenPair
from app.services import auth as auth_service
from app.services.rate_limits import (
    LOGIN,
    REFRESH,
    RateLimitService,
    authenticated_effective_caller,
    login_effective_caller,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

RATE_LIMIT_RESPONSE: dict[int | str, dict[str, Any]] = {
    429: {"model": ErrorResponse, "description": "Request rate limit exceeded."}
}


def _token_response(
    access_token: str, refresh_token: str, settings: Settings
) -> TokenPair:
    """Build a token-pair response using configured access-token lifetime."""
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/login", response_model=TokenPair, responses=RATE_LIMIT_RESPONSE)
async def login(
    payload: LoginRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    rate_limiter: Annotated[RateLimitService, Depends(get_rate_limiter)],
) -> TokenPair:
    """Authenticate a seeded user after checking the login rate limit."""
    await rate_limiter.check(
        LOGIN,
        login_effective_caller(
            str(payload.email), request.client.host if request.client else None
        ),
    )
    _user, access_token, refresh_token = await auth_service.authenticate(
        session, str(payload.email), payload.password
    )
    return _token_response(access_token, refresh_token, settings)


@router.post("/refresh", response_model=TokenPair, responses=RATE_LIMIT_RESPONSE)
async def refresh(
    payload: RefreshRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    rate_limiter: Annotated[RateLimitService, Depends(get_rate_limiter)],
) -> TokenPair:
    """Rotate a refresh token after checking the authenticated caller limit."""
    token_user = await auth_service.refresh_token_user(session, payload.refresh_token)
    await rate_limiter.check(
        REFRESH,
        authenticated_effective_caller(token_user.id, token_user.organization_id),
    )
    _user, access_token, refresh_token = await auth_service.refresh_session(
        session, payload.refresh_token
    )
    return _token_response(access_token, refresh_token, settings)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Revoke a refresh token and return an empty success response."""
    await auth_service.logout(session, payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=CurrentUser)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> CurrentUser:
    """Return the authenticated user's non-secret profile fields."""
    return CurrentUser(
        id=current_user.id,
        email=current_user.email,
        organization_id=current_user.organization_id,
        role=current_user.role,
        is_active=current_user.is_active,
    )
