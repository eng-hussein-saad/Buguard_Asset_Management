from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import (
    AnalysisFailedError,
    AnalysisGroundingError,
    AnalysisUnavailableError,
)
from app.models.asset import Asset, AssetType
from app.models.user import User
from app.repositories import assets as asset_repository
from app.schemas.analysis import (
    AnalysisReportRequest,
    AnalysisReportResponse,
    EvidenceAsset,
    RiskEntry,
)
from app.schemas.assets import AssetListParams
from app.services.certificate_lifecycle import (
    classify_certificate_lifecycle,
)
from app.services.rbac import Permission, require_permission

logger = logging.getLogger(__name__)


class AnalysisProvider(Protocol):
    """Defines the provider contract used by the analysis service."""

    async def generate_report(
        self, evidence: list[EvidenceAsset]
    ) -> AnalysisReportResponse:
        """Generate a report from bounded tenant-owned evidence."""


class UnavailableAnalysisProvider:
    """Provider used when live analysis configuration is absent."""

    async def generate_report(
        self, evidence: list[EvidenceAsset]
    ) -> AnalysisReportResponse:
        """Raise a structured unavailable error instead of calling a provider."""
        raise AnalysisUnavailableError()


class _LLMRiskEntry(BaseModel):
    """Defines the structured risk item expected from LangChain."""

    title: str = Field(default="Potential inventory risk", min_length=1)
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    description: str = Field(min_length=1)
    evidence_asset_ids: list[UUID] = Field(default_factory=list)


class _LLMAnalysisReport(BaseModel):
    """Defines the structured report payload expected from LangChain."""

    summary: str = Field(min_length=1)
    risks: list[_LLMRiskEntry] = Field(default_factory=list)
    evidence_asset_ids: list[UUID] = Field(default_factory=list)


class ConfiguredAnalysisProvider:
    """LangChain-backed provider adapter for configured analysis requests."""

    def __init__(
        self,
        provider: str,
        model: str | None,
        api_key: str,
        timeout_seconds: int,
        base_url: str | None = None,
        http_referer: str | None = None,
        app_title: str | None = None,
        chain: Any | None = None,
    ) -> None:
        """Store LangChain provider settings without exposing secrets."""
        self.provider = provider
        self.model = model or self._default_model(provider)
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.base_url = base_url or self._default_base_url(provider)
        self.http_referer = http_referer
        self.app_title = app_title
        self._chain = chain

    async def generate_report(
        self, evidence: list[EvidenceAsset]
    ) -> AnalysisReportResponse:
        """Generate a structured report through LangChain."""
        if self.provider.lower() not in {"openai", "langchain-openai", "openrouter"}:
            raise AnalysisUnavailableError()
        chain = self._chain or self._build_chain()
        llm_report = await chain.ainvoke(
            [
                (
                    "system",
                    "You are a security asset analyst. Use only the provided "
                    "JSON evidence. Do not invent assets, ids, counts, "
                    "relationships, organizations, or risks. Every asset-specific "
                    "risk must cite evidence_asset_ids from the evidence only.",
                ),
                (
                    "human",
                    "Generate a concise inventory risk report. Pay special "
                    "attention to certificate_lifecycle_status values. Return only "
                    "a JSON object with summary, risks, and evidence_asset_ids. "
                    "Evidence "
                    f"JSON: {[item.model_dump(mode='json') for item in evidence]}",
                ),
            ]
        )
        llm_report = self._parse_llm_report(llm_report)
        return AnalysisReportResponse(
            summary=llm_report.summary,
            risks=[
                RiskEntry(
                    title=risk.title,
                    severity=risk.severity,
                    description=risk.description,
                    evidence_asset_ids=risk.evidence_asset_ids,
                )
                for risk in llm_report.risks
            ],
            evidence_asset_ids=llm_report.evidence_asset_ids,
            evidence=evidence,
            status="completed",
            generated_at=datetime.now(UTC),
        )

    def _build_chain(self) -> Any:
        """Create the LangChain structured-output chain for chat models."""
        from langchain_openai import ChatOpenAI

        default_headers: dict[str, str] = {}
        if self.http_referer:
            default_headers["HTTP-Referer"] = self.http_referer
        if self.app_title:
            default_headers["X-OpenRouter-Title"] = self.app_title

        if self.provider.lower() == "openrouter":
            default_headers.setdefault("HTTP-Referer", "http://localhost:8000")
            default_headers.setdefault("X-OpenRouter-Title", "Buguard Asset Management")

        model = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout_seconds,
            default_headers=default_headers or None,
        )
        if self.provider.lower() == "openrouter":
            return model
        return model.with_structured_output(_LLMAnalysisReport)

    def _parse_llm_report(self, raw_report: Any) -> _LLMAnalysisReport:
        """Parse LangChain model output into the expected report schema."""
        if isinstance(raw_report, _LLMAnalysisReport):
            return raw_report
        if isinstance(raw_report, dict):
            return _LLMAnalysisReport.model_validate(raw_report)
        content = getattr(raw_report, "content", raw_report)
        if isinstance(content, list):
            content = "".join(
                str(part.get("text", part)) if isinstance(part, dict) else str(part)
                for part in content
            )
        if isinstance(content, str):
            return _LLMAnalysisReport.model_validate(json.loads(_json_text(content)))
        return _LLMAnalysisReport.model_validate(content)

    def _default_base_url(self, provider: str) -> str | None:
        """Return the OpenRouter-compatible base URL when requested."""
        if provider.lower() == "openrouter":
            return "https://openrouter.ai/api/v1"
        return None

    def _default_model(self, provider: str) -> str:
        """Return a provider-specific default model for local setup."""
        if provider.lower() == "openrouter":
            return "nvidia/nemotron-3-ultra-550b-a55b:free"
        return "gpt-4.1-mini"


def evidence_from_asset(asset: Asset) -> EvidenceAsset:
    """Map an asset model into the provider-safe evidence shape."""
    metadata = dict(asset.asset_metadata or {})
    lifecycle = (
        classify_certificate_lifecycle(metadata)
        if asset.type == AssetType.CERTIFICATE.value
        else None
    )
    return EvidenceAsset(
        id=asset.id,
        type=AssetType(asset.type),
        value=asset.value,
        status=asset.status,
        source=asset.source,
        tags=list(asset.tags or []),
        metadata=metadata,
        certificate_lifecycle_status=lifecycle,
    )


def _json_text(content: str) -> str:
    """Extract a JSON object from plain or fenced model output."""
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end >= start:
        return text[start : end + 1]
    return text


def _asset_params(payload: AnalysisReportRequest) -> AssetListParams:
    """Convert report filters into the shared asset filtering schema."""
    return AssetListParams(
        type=payload.type,
        status=payload.status,
        tag=payload.tag,
        source=payload.source,
        value_contains=payload.value_contains,
        certificate_lifecycle_status=payload.certificate_lifecycle_status,
        page_size=min(payload.limit, 100),
    )


def _validate_grounding(
    report: AnalysisReportResponse, evidence_ids: set[UUID]
) -> None:
    """Reject provider output that references assets outside selected evidence."""
    if not set(report.evidence_asset_ids).issubset(evidence_ids):
        raise AnalysisGroundingError()
    for risk in report.risks:
        if not set(risk.evidence_asset_ids).issubset(evidence_ids):
            raise AnalysisGroundingError()


async def generate_report(
    session: AsyncSession,
    current_user: User,
    payload: AnalysisReportRequest,
    provider: AnalysisProvider,
) -> AnalysisReportResponse:
    """Generate a grounded analysis report for the authenticated organization."""
    require_permission(current_user.role, Permission.READ_ASSETS)
    assets = await asset_repository.select_analysis_evidence(
        session,
        current_user.organization_id,
        _asset_params(payload),
        payload.limit,
    )
    evidence = [evidence_from_asset(asset) for asset in assets]
    if not evidence:
        return AnalysisReportResponse(
            summary="No matching assets were found for the selected filters.",
            risks=[],
            evidence_asset_ids=[],
            evidence=[],
            status="no_data",
            message="No matching organization-owned assets were available.",
        )
    try:
        report = await provider.generate_report(evidence)
    except AnalysisUnavailableError:
        raise
    except AnalysisGroundingError:
        raise
    except Exception as exc:
        logger.info(
            "Analysis provider failed",
            extra={"provider_error_type": type(exc).__name__},
        )
        raise AnalysisFailedError() from exc
    _validate_grounding(report, {item.id for item in evidence})
    return report
