from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models import TimestampMixin, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.models.organization import Organization


class AssetType(StrEnum):
    DOMAIN = "domain"
    SUBDOMAIN = "subdomain"
    IP_ADDRESS = "ip_address"
    SERVICE = "service"
    CERTIFICATE = "certificate"
    TECHNOLOGY = "technology"


class AssetStatus(StrEnum):
    ACTIVE = "active"
    STALE = "stale"
    ARCHIVED = "archived"


class RelationshipType(StrEnum):
    BELONGS_TO = "belongs_to"
    PARENT = "parent"
    RESOLVES_TO = "resolves_to"
    RUNS_ON = "runs_on"
    COVERS = "covers"
    DETECTED_ON = "detected_on"


class Asset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assets"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "type", "value", name="uq_assets_org_type_value"
        ),
        CheckConstraint(
            "type IN ('domain', 'subdomain', 'ip_address', 'service', "
            "'certificate', 'technology')",
            name="ck_assets_type",
        ),
        CheckConstraint(
            "status IN ('active', 'stale', 'archived')", name="ck_assets_status"
        ),
        Index("ix_assets_org_lookup", "organization_id", "type", "value"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(30))
    value: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(20), default=AssetStatus.ACTIVE.value)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    source: Mapped[str | None] = mapped_column(String(255))
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    asset_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict
    )

    organization: Mapped[Organization] = relationship(back_populates="assets")
    outgoing_relationships: Mapped[list[AssetRelationship]] = relationship(
        foreign_keys="AssetRelationship.source_asset_id",
        back_populates="source_asset",
    )
    incoming_relationships: Mapped[list[AssetRelationship]] = relationship(
        foreign_keys="AssetRelationship.target_asset_id",
        back_populates="target_asset",
    )


class AssetRelationship(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_relationships"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "source_asset_id",
            "target_asset_id",
            "relationship_type",
            name="uq_relationships_org_source_target_type",
        ),
        CheckConstraint(
            "relationship_type IN ('belongs_to', 'parent', 'resolves_to', 'runs_on', "
            "'covers', 'detected_on')",
            name="ck_relationships_type",
        ),
        Index(
            "ix_relationships_org_lookup",
            "organization_id",
            "source_asset_id",
            "target_asset_id",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    source_asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE")
    )
    target_asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE")
    )
    relationship_type: Mapped[str] = mapped_column(String(30))
    relationship_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    source_asset: Mapped[Asset] = relationship(
        foreign_keys=[source_asset_id], back_populates="outgoing_relationships"
    )
    target_asset: Mapped[Asset] = relationship(
        foreign_keys=[target_asset_id], back_populates="incoming_relationships"
    )
