from uuid import uuid4

import pytest
from app.api.deps import get_analysis_provider, get_current_user, get_db
from app.schemas.analysis import AnalysisReportResponse
from app.services import analysis
from httpx import ASGITransport, AsyncClient


class DummySession:
    """Minimal async session for patched route contract tests."""


class DummyProvider:
    """Placeholder provider dependency for route contract tests."""


async def _client(app_instance, user):
    """Create an ASGI client with analysis dependencies overridden."""
    app_instance.dependency_overrides[get_current_user] = lambda: user
    app_instance.dependency_overrides[get_db] = lambda: DummySession()
    app_instance.dependency_overrides[get_analysis_provider] = lambda: DummyProvider()
    return AsyncClient(
        transport=ASGITransport(app=app_instance), base_url="http://testserver"
    )


def test_analysis_openapi_contract_is_exposed(app_instance) -> None:
    generated = app_instance.openapi()

    assert "/analysis/report" in generated["paths"]
    operation = generated["paths"]["/analysis/report"]["post"]
    assert operation["tags"] == ["Analysis"]
    assert operation["summary"] == (
        "Generate a grounded organization-owned asset analysis report"
    )
    assert "503" in operation["responses"]
    assert "502" in operation["responses"]


@pytest.mark.asyncio
async def test_analysis_report_route_response_shape(
    app_instance, demo_user, monkeypatch
) -> None:
    evidence_id = uuid4()

    async def fake_generate(session, current_user, payload, provider):
        assert current_user == demo_user
        assert payload.limit == 5
        return AnalysisReportResponse(
            summary="ok",
            risks=[],
            evidence_asset_ids=[evidence_id],
            status="completed",
        )

    monkeypatch.setattr(analysis, "generate_report", fake_generate)

    async with await _client(app_instance, demo_user) as client:
        response = await client.post("/analysis/report", json={"limit": 5})

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["evidence_asset_ids"] == [str(evidence_id)]
