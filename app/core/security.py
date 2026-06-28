import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import Settings, get_settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return cast(str, password_context.hash(password))


def verify_password(password: str, password_hash: str) -> bool:
    return cast(bool, password_context.verify(password, password_hash))


def create_access_token(
    user_id: UUID,
    organization_id: UUID,
    role: str,
    settings: Settings | None = None,
    now: datetime | None = None,
) -> str:
    active_settings = settings or get_settings()
    issued_at = now or datetime.now(UTC)
    expires_at = issued_at + timedelta(
        minutes=active_settings.access_token_expire_minutes
    )
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "organization_id": str(organization_id),
        "role": role,
        "exp": expires_at,
    }
    return cast(
        str,
        jwt.encode(
            payload,
            active_settings.jwt_secret_key,
            algorithm=active_settings.jwt_algorithm,
        ),
    )


def decode_access_token(
    token: str, settings: Settings | None = None
) -> dict[str, Any] | None:
    active_settings = settings or get_settings()
    try:
        payload = cast(
            dict[str, Any],
            jwt.decode(
                token,
                active_settings.jwt_secret_key,
                algorithms=[active_settings.jwt_algorithm],
            ),
        )
    except JWTError:
        return None

    required_claims = {"sub", "organization_id", "role", "exp"}
    if not required_claims.issubset(payload):
        return None
    return payload


def hash_refresh_token(token: str, settings: Settings | None = None) -> str:
    """Create a keyed digest for direct lookup of high-entropy refresh tokens."""
    active_settings = settings or get_settings()
    digest = hmac.new(
        active_settings.jwt_secret_key.encode(),
        token.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"hmac-sha256:{digest}"
