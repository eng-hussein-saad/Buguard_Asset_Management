from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import Settings, get_settings
from app.models.user import User
from app.schemas.auth import CurrentUser, LoginRequest, RefreshRequest, TokenPair
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


def _token_response(
    access_token: str, refresh_token: str, settings: Settings
) -> TokenPair:
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/login", response_model=TokenPair)
async def login(
    payload: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenPair:
    _user, access_token, refresh_token = await auth_service.authenticate(
        session, str(payload.email), payload.password
    )
    return _token_response(access_token, refresh_token, settings)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    payload: RefreshRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenPair:
    _user, access_token, refresh_token = await auth_service.refresh_session(
        session, payload.refresh_token
    )
    return _token_response(access_token, refresh_token, settings)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    await auth_service.logout(session, payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=CurrentUser)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> CurrentUser:
    return CurrentUser(
        id=current_user.id,
        email=current_user.email,
        organization_id=current_user.organization_id,
        role=current_user.role,
        is_active=current_user.is_active,
    )
