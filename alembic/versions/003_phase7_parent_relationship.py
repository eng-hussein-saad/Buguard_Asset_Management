"""phase7 parent relationship

Revision ID: 003_phase7_parent_relationship
Revises: 002_multi_tenant_auth
Create Date: 2026-06-28
"""

from collections.abc import Sequence

from alembic import op

revision: str = "003_phase7_parent_relationship"
down_revision: str | Sequence[str] | None = "002_multi_tenant_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Allow parent and covers relationship types in the database constraint."""
    op.drop_constraint(
        "ck_relationships_type", "asset_relationships", type_="check"
    )
    op.create_check_constraint(
        "ck_relationships_type",
        "asset_relationships",
        "relationship_type IN ('belongs_to', 'parent', 'resolves_to', "
        "'runs_on', 'covers', 'detected_on')",
    )


def downgrade() -> None:
    """Restore the pre-Phase 7 relationship type constraint."""
    op.drop_constraint(
        "ck_relationships_type", "asset_relationships", type_="check"
    )
    op.create_check_constraint(
        "ck_relationships_type",
        "asset_relationships",
        "relationship_type IN ('belongs_to', 'resolves_to', 'runs_on', "
        "'covers', 'detected_on')",
    )
