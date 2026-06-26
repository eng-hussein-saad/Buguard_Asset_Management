from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    verify_password,
    verify_refresh_token,
)


def test_password_hashing_does_not_store_raw_password() -> None:
    password_hash = hash_password("password123")

    assert password_hash != "password123"
    assert verify_password("password123", password_hash)
    assert not verify_password("wrong", password_hash)


def test_refresh_token_hashing_does_not_store_raw_token() -> None:
    token_hash = hash_refresh_token("raw-refresh-token")

    assert token_hash != "raw-refresh-token"
    assert verify_refresh_token("raw-refresh-token", token_hash)
    assert not verify_refresh_token("different-token", token_hash)


def test_expired_access_token_is_rejected() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/buguard",
        JWT_SECRET_KEY="test-secret",
        ACCESS_TOKEN_EXPIRE_MINUTES=1,
    )
    token = create_access_token(
        uuid4(),
        uuid4(),
        "viewer",
        settings=settings,
        now=datetime.now(UTC) - timedelta(minutes=5),
    )

    assert decode_access_token(token, settings=settings) is None
