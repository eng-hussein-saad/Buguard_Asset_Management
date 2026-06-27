from datetime import UTC, datetime
from uuid import uuid4

from app.core.config import Settings
from app.core.security import create_access_token, decode_access_token


def test_access_token_contains_required_auth_context() -> None:
    user_id = uuid4()
    organization_id = uuid4()
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/buguard",
        JWT_SECRET_KEY="test-secret",
    )

    token = create_access_token(
        user_id,
        organization_id,
        "admin",
        settings=settings,
        now=datetime.now(UTC),
    )
    payload = decode_access_token(token, settings=settings)

    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["organization_id"] == str(organization_id)
    assert payload["role"] == "admin"
    assert "exp" in payload
