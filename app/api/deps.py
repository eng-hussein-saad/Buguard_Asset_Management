from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AuthenticationError
from app.core.security import decode_access_token
from app.db.session import get_async_session
from app.models.user import User
from app.repositories.users import get_by_id
from app.services.rbac import Permission, require_permission

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in get_async_session():
        yield session


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if credentials is None:
        raise AuthenticationError()

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise AuthenticationError()

    try:
        user_id = UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise AuthenticationError() from exc

    user = await get_by_id(session, user_id)
    if user is None or not user.is_active:
        raise AuthenticationError()

    if (
        str(user.organization_id) != payload["organization_id"]
        or user.role != payload["role"]
    ):
        raise AuthenticationError()
    return user


def require_role_permission(
    permission: Permission,
) -> Callable[[User], Coroutine[Any, Any, User]]:
    async def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        require_permission(current_user.role, permission)
        return current_user

    return dependency

