from pathlib import Path


def test_auth_openapi_contract_is_exposed(app_instance) -> None:
    generated = app_instance.openapi()
    contract = Path("specs/002-multi-tenant-auth/contracts/auth-api.yaml").read_text()

    for path in ("/auth/login", "/auth/refresh", "/auth/logout", "/auth/me"):
        assert path in generated["paths"]
        assert path in contract

    assert "post" in generated["paths"]["/auth/login"]
    assert "post" in generated["paths"]["/auth/refresh"]
    assert "post" in generated["paths"]["/auth/logout"]
    assert "get" in generated["paths"]["/auth/me"]


def test_no_public_onboarding_routes_are_exposed(app_instance) -> None:
    paths = app_instance.openapi()["paths"]

    assert "/auth/register" not in paths
    assert "/organizations" not in paths
    assert "/auth/switch-organization" not in paths
