from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.core.errors import AuthenticationError
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services import auth as auth_service


@pytest.mark.asyncio
async def test_refresh_rejects_unknown_token(monkeypatch) -> None:
    async def missing_token(session, token_hash):
        return None

    monkeypatch.setattr(
        auth_service.auth_repository,
        "get_unrevoked_refresh_token_by_hash",
        missing_token,
    )

    with pytest.raises(AuthenticationError):
        await auth_service.refresh_session(None, "unknown-token")


@pytest.mark.asyncio
async def test_refresh_rejects_expired_token(monkeypatch) -> None:
    user = User(
        id=uuid4(),
        organization_id=uuid4(),
        email="admin@example.com",
        password_hash="hash",
        role="admin",
        is_active=True,
    )
    token = RefreshToken(
        user_id=user.id,
        token_hash="hash",
        expires_at=datetime.now(UTC) - timedelta(days=1),
        revoked_at=None,
    )
    token.user = user

    async def find_token(session, raw_refresh_token):
        return token

    monkeypatch.setattr(auth_service, "_find_refresh_record", find_token)

    with pytest.raises(AuthenticationError):
        await auth_service.refresh_session(None, "expired-token")
