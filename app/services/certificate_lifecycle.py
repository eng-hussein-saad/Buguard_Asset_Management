from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from enum import StrEnum
from typing import Any


class CertificateLifecycleStatus(StrEnum):
    """Derived lifecycle states for certificate expiry metadata."""

    EXPIRED = "expired"
    EXPIRING_SOON = "expiring_soon"
    VALID = "valid"
    UNKNOWN = "unknown"


def parse_certificate_expiry(raw_value: Any) -> date | None:
    """Parse supported certificate expiry values into a calendar date."""
    if isinstance(raw_value, datetime):
        return raw_value.date()
    if isinstance(raw_value, date):
        return raw_value
    if not isinstance(raw_value, str) or not raw_value.strip():
        return None
    value = raw_value.strip()
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            return None


def classify_certificate_lifecycle(
    metadata: dict[str, Any] | None,
    *,
    evaluation_date: date | None = None,
) -> CertificateLifecycleStatus:
    """Classify certificate expiry using a 30-day inclusive warning window."""
    expires_at = parse_certificate_expiry((metadata or {}).get("expires"))
    if expires_at is None:
        return CertificateLifecycleStatus.UNKNOWN
    today = evaluation_date or datetime.now(UTC).date()
    if expires_at < today:
        return CertificateLifecycleStatus.EXPIRED
    if expires_at <= today + timedelta(days=30):
        return CertificateLifecycleStatus.EXPIRING_SOON
    return CertificateLifecycleStatus.VALID


def lifecycle_value(metadata: dict[str, Any] | None) -> str:
    """Return the serialized lifecycle status for response enrichment."""
    return classify_certificate_lifecycle(metadata).value
