from uuid import uuid4

import pytest
from app.core.errors import AnalysisFailedError, AnalysisGroundingError
from app.schemas.analysis import AnalysisReportRequest, AnalysisReportResponse
from app.services import analysis


class FakeProvider:
    """Returns a prepared report for integration-style service tests."""

    def __init__(self, report=None, error: Exception | None = None) -> None:
        """Store the result that the fake provider should produce."""
        self.report = report
        self.error = error

    async def generate_report(self, evidence):
        """Return a report or raise the configured provider error."""
        if self.error is not None:
            raise self.error
        return self.report.model_copy(update={"evidence": evidence})


class FakeSession:
    """Placeholder session for patched repository tests."""


@pytest.mark.asyncio
async def test_analysis_no_data_returns_empty_grounded_response(
    demo_user, monkeypatch
) -> None:
    async def fake_select(*args):
        return []

    monkeypatch.setattr(
        analysis.asset_repository, "select_analysis_evidence", fake_select
    )

    report = await analysis.generate_report(
        FakeSession(), demo_user, AnalysisReportRequest(), FakeProvider()
    )

    assert report.status == "no_data"
    assert report.evidence_asset_ids == []
    assert report.risks == []


@pytest.mark.asyncio
async def test_provider_exceptions_map_to_safe_analysis_failure(
    demo_user, asset_factory, monkeypatch
) -> None:
    asset = asset_factory(demo_user.organization_id)

    async def fake_select(*args):
        return [asset]

    monkeypatch.setattr(
        analysis.asset_repository, "select_analysis_evidence", fake_select
    )

    with pytest.raises(AnalysisFailedError):
        await analysis.generate_report(
            FakeSession(),
            demo_user,
            AnalysisReportRequest(),
            FakeProvider(error=RuntimeError("secret stack trace")),
        )


@pytest.mark.asyncio
async def test_analysis_rejects_ungrounded_provider_asset_ids(
    demo_user, asset_factory, monkeypatch
) -> None:
    asset = asset_factory(demo_user.organization_id)
    unselected_id = uuid4()

    async def fake_select(*args):
        return [asset]

    monkeypatch.setattr(
        analysis.asset_repository, "select_analysis_evidence", fake_select
    )

    with pytest.raises(AnalysisGroundingError):
        await analysis.generate_report(
            FakeSession(),
            demo_user,
            AnalysisReportRequest(),
            FakeProvider(
                AnalysisReportResponse(
                    summary="bad",
                    risks=[],
                    evidence_asset_ids=[unselected_id],
                    status="completed",
                )
            ),
        )
