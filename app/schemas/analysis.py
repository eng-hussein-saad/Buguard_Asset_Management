from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.asset import AssetStatus, AssetType
from app.services.certificate_lifecycle import CertificateLifecycleStatus

AnalysisStatus = Literal["completed", "no_data", "unavailable", "failed"]
RiskSeverity = Literal["low", "medium", "high", "critical"]


class AnalysisReportRequest(BaseModel):
    """Validates filters used to select tenant-owned report evidence."""

    model_config = ConfigDict(extra="forbid")

    type: AssetType | None = None
    status: AssetStatus | None = None
    tag: str | None = Field(default=None, min_length=1)
    source: str | None = Field(default=None, min_length=1)
    value_contains: str | None = Field(default=None, min_length=1)
    certificate_lifecycle_status: CertificateLifecycleStatus | None = None
    limit: int = Field(default=50, ge=1, le=100)

    @model_validator(mode="after")
    def trim_text_filters(self) -> AnalysisReportRequest:
        """Normalize string filters before repository selection."""
        for field_name in ("tag", "source", "value_contains"):
            value = getattr(self, field_name)
            if value is not None:
                trimmed = value.strip()
                if not trimmed:
                    raise ValueError(f"{field_name} must not be blank.")
                setattr(self, field_name, trimmed)
        return self


class EvidenceAsset(BaseModel):
    """Serializes one tenant-owned asset used as report evidence."""

    id: UUID
    type: AssetType
    value: str
    status: AssetStatus
    source: str | None
    tags: list[str]
    metadata: dict[str, Any]
    certificate_lifecycle_status: CertificateLifecycleStatus | None = None


class RiskEntry(BaseModel):
    """Serializes one grounded report risk."""

    title: str = Field(min_length=1)
    severity: RiskSeverity = "medium"
    description: str = Field(min_length=1)
    evidence_asset_ids: list[UUID] = Field(default_factory=list)


class AnalysisReportResponse(BaseModel):
    """Serializes a grounded or intentionally empty analysis report."""

    summary: str
    risks: list[RiskEntry]
    evidence_asset_ids: list[UUID] = Field(default_factory=list, exclude=True)
    evidence: list[EvidenceAsset] = Field(default_factory=list)
    status: AnalysisStatus
    message: str | None = None
    generated_at: datetime | None = None
