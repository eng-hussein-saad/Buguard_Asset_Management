from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from app.models.asset import Asset, AssetStatus, AssetType

AssetSortField = Literal[
    "value", "type", "status", "first_seen", "last_seen", "created_at"
]
SortOrder = Literal["asc", "desc"]


class AssetBase(BaseModel):
    """Defines shared editable asset fields for create and update payloads."""

    type: AssetType | None = None
    value: str | None = Field(default=None, min_length=1)
    status: AssetStatus | None = None
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    source: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, JsonValue] | None = None

    @model_validator(mode="after")
    def validate_non_blank_value(self) -> AssetBase:
        """Reject values that become empty after trimming whitespace."""
        if self.value is not None and not self.value.strip():
            raise ValueError("Asset value must not be blank.")
        return self


class AssetCreate(AssetBase):
    """Validates input for creating an organization-owned asset."""

    model_config = ConfigDict(extra="forbid")

    type: AssetType
    value: str = Field(min_length=1)
    status: AssetStatus = AssetStatus.ACTIVE
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, JsonValue] = Field(default_factory=dict)


class AssetUpdate(AssetBase):
    """Validates partial asset updates while forbidding ownership changes."""

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_has_changes(self) -> AssetUpdate:
        """Reject empty patch documents with no editable fields set."""
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        return self


class AssetRead(BaseModel):
    """Serializes an asset without exposing tenant ownership."""

    id: UUID
    type: AssetType
    value: str
    status: AssetStatus
    first_seen: datetime
    last_seen: datetime
    source: str | None
    tags: list[str]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, asset: Asset) -> AssetRead:
        """Build an API response from the SQLAlchemy asset model."""
        return cls(
            id=asset.id,
            type=AssetType(asset.type),
            value=asset.value,
            status=AssetStatus(asset.status),
            first_seen=asset.first_seen,
            last_seen=asset.last_seen,
            source=asset.source,
            tags=list(asset.tags or []),
            metadata=dict(asset.asset_metadata or {}),
            created_at=asset.created_at,
            updated_at=asset.updated_at,
        )


class AssetListParams(BaseModel):
    """Validates supported filters, sorting, and bounded pagination."""

    type: AssetType | None = None
    status: AssetStatus | None = None
    tag: str | None = Field(default=None, min_length=1)
    source: str | None = Field(default=None, min_length=1)
    value_contains: str | None = Field(default=None, min_length=1)
    sort_by: AssetSortField = "created_at"
    sort_order: SortOrder = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def trim_text_filters(self) -> AssetListParams:
        """Trim text filters and reject values that become empty."""
        for field_name in ("tag", "source", "value_contains"):
            value = getattr(self, field_name)
            if value is not None:
                trimmed = value.strip()
                if not trimmed:
                    raise ValueError(f"{field_name} must not be blank.")
                setattr(self, field_name, trimmed)
        return self


class PaginatedAssets(BaseModel):
    """Serializes a page of assets and its navigation metadata."""

    items: list[AssetRead]
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool


class ErrorBody(BaseModel):
    """Documents the structured error body used by asset endpoints."""

    code: str
    message: str
    details: dict[str, Any]


class ErrorResponse(BaseModel):
    """Documents the project-wide structured error envelope."""

    error: ErrorBody
