from uuid import uuid4

import pytest
from app.core.errors import AnalysisGroundingError, AnalysisUnavailableError
from app.schemas.analysis import AnalysisReportResponse, EvidenceAsset, RiskEntry
from app.services.analysis import (
    ConfiguredAnalysisProvider,
    UnavailableAnalysisProvider,
    _validate_grounding,
)
from app.services.certificate_lifecycle import CertificateLifecycleStatus


class FakeLangChainReport:
    """Fake LangChain chain that returns structured output without network calls."""

    async def ainvoke(self, messages):
        """Return a grounded report for the evidence embedded in the prompt."""
        evidence_id = messages[1][1].split("'id': '", 1)[1].split("'", 1)[0]
        return {
            "summary": "Analyzed certificate evidence.",
            "risks": [
                {
                    "title": "Certificate expired",
                    "severity": "high",
                    "description": "The certificate is expired.",
                    "evidence_asset_ids": [evidence_id],
                }
            ],
            "evidence_asset_ids": [evidence_id],
        }


class FakeOpenRouterReport:
    """Fake OpenRouter chat model that returns a JSON string response."""

    async def ainvoke(self, messages):
        """Return a JSON-only response like an OpenRouter chat completion."""
        evidence_id = messages[1][1].split("'id': '", 1)[1].split("'", 1)[0]
        return (
            "```json\n"
            '{"summary":"Analyzed OpenRouter evidence.",'
            '"risks":[{"title":"Certificate expired","severity":"high",'
            '"description":"The certificate is expired.",'
            f'"evidence_asset_ids":["{evidence_id}"]'
            f'}}],"evidence_asset_ids":["{evidence_id}"]}}'
            "\n```"
        )


@pytest.mark.asyncio
async def test_unavailable_provider_raises_structured_error() -> None:
    with pytest.raises(AnalysisUnavailableError):
        await UnavailableAnalysisProvider().generate_report([])


@pytest.mark.asyncio
async def test_configured_provider_returns_grounded_certificate_risks() -> None:
    asset_id = uuid4()
    provider = ConfiguredAnalysisProvider(
        "openai", "gpt-4.1-mini", "test-key", 30, chain=FakeLangChainReport()
    )

    report = await provider.generate_report(
        [
            EvidenceAsset(
                id=asset_id,
                type="certificate",
                value="cert-api-example",
                status="active",
                source="sample",
                tags=[],
                metadata={"expires": "2026-06-27"},
                certificate_lifecycle_status=CertificateLifecycleStatus.EXPIRED,
            )
        ]
    )

    assert report.status == "completed"
    assert report.evidence_asset_ids == [asset_id]
    assert report.risks[0].evidence_asset_ids == [asset_id]


def test_openrouter_provider_defaults_to_nemotron_model() -> None:
    provider = ConfiguredAnalysisProvider("openrouter", None, "test-key", 30)

    assert provider.model == "nvidia/nemotron-3-ultra-550b-a55b:free"
    assert provider.base_url == "https://openrouter.ai/api/v1"


@pytest.mark.asyncio
async def test_openrouter_provider_parses_json_string_output() -> None:
    asset_id = uuid4()
    provider = ConfiguredAnalysisProvider(
        "openrouter", None, "test-key", 30, chain=FakeOpenRouterReport()
    )

    report = await provider.generate_report(
        [
            EvidenceAsset(
                id=asset_id,
                type="certificate",
                value="cert-api-example",
                status="active",
                source="sample",
                tags=[],
                metadata={"expires": "2026-06-27"},
                certificate_lifecycle_status=CertificateLifecycleStatus.EXPIRED,
            )
        ]
    )

    assert report.summary == "Analyzed OpenRouter evidence."
    assert report.evidence_asset_ids == [asset_id]


def test_grounding_validation_rejects_unselected_evidence() -> None:
    selected_id = uuid4()
    unselected_id = uuid4()
    report = AnalysisReportResponse(
        summary="bad",
        risks=[
            RiskEntry(
                title="Ungrounded",
                description="Uses an unselected asset.",
                evidence_asset_ids=[unselected_id],
            )
        ],
        evidence_asset_ids=[selected_id],
        status="completed",
    )

    with pytest.raises(AnalysisGroundingError):
        _validate_grounding(report, {selected_id})
