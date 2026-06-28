from datetime import date

from app.services.certificate_lifecycle import (
    CertificateLifecycleStatus,
    classify_certificate_lifecycle,
    parse_certificate_expiry,
)


def test_certificate_lifecycle_classifies_all_required_states() -> None:
    today = date(2026, 6, 28)

    assert (
        classify_certificate_lifecycle(
            {"expires": "2026-06-27"}, evaluation_date=today
        )
        == CertificateLifecycleStatus.EXPIRED
    )
    assert (
        classify_certificate_lifecycle(
            {"expires": "2026-07-28"}, evaluation_date=today
        )
        == CertificateLifecycleStatus.EXPIRING_SOON
    )
    assert (
        classify_certificate_lifecycle(
            {"expires": "2026-07-29"}, evaluation_date=today
        )
        == CertificateLifecycleStatus.VALID
    )
    assert (
        classify_certificate_lifecycle({}, evaluation_date=today)
        == CertificateLifecycleStatus.UNKNOWN
    )
    assert (
        classify_certificate_lifecycle({"expires": "soon"}, evaluation_date=today)
        == CertificateLifecycleStatus.UNKNOWN
    )


def test_parse_certificate_expiry_accepts_iso_datetime_prefix() -> None:
    assert parse_certificate_expiry("2026-07-15T10:20:30Z") == date(2026, 7, 15)
