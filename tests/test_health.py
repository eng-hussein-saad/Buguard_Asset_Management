from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_health_returns_exact_ok_body(app_instance) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app_instance), base_url="http://testserver"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_route_matches_openapi_contract(app_instance) -> None:
    contract = Path("specs/001-backend-foundation/contracts/openapi.yaml").read_text()
    generated = app_instance.openapi()

    assert "/health" in generated["paths"]
    assert "get" in generated["paths"]["/health"]
    assert generated["paths"]["/health"]["get"]["operationId"] == "getHealth"
    assert "operationId: getHealth" in contract
    assert "const: ok" in contract
