from pathlib import Path


def test_phase_6_contract_documents_rate_limits_and_cache() -> None:
    """Verify the Phase 6 contract captures the new operational behavior."""
    contract = Path(
        "specs/006-test-ci-rate-limits/contracts/test-ci-rate-limits-api.yaml"
    ).read_text()

    assert "x-rate-limit" in contract
    assert "x-cache" in contract
    assert "rate_limited" in contract
    assert (
        "authenticated organization plus all response-affecting query inputs"
        in contract
    )


def test_openapi_exposes_phase_6_rate_limit_responses(app_instance) -> None:
    """Verify generated OpenAPI includes structured 429 response metadata."""
    paths = app_instance.openapi()["paths"]

    assert "429" in paths["/auth/login"]["post"]["responses"]
    assert "429" in paths["/auth/refresh"]["post"]["responses"]
    assert "429" in paths["/assets/import"]["post"]["responses"]
