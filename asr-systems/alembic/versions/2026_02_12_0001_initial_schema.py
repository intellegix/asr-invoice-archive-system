"""Initial schema — audit_events table.

Revision ID: 0001
Revises: None
Create Date: 2026-02-12

This captures the existing ORM model created by Base.metadata.create_all()
so that future migrations can build on it.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the audit_events table if it doesn't already exist.
    # The existing app uses Base.metadata.create_all at startup, so on
    # first deploy this is effectively a no-op but records the baseline.
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", sa.String(255), nullable=True),
        sa.Column("tenant_id", sa.String(100), nullable=True),
        sa.Column("user_id", sa.String(100), nullable=True),
        sa.Column("action", sa.String(100), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        if_not_exists=True,
    )
    op.create_index(
        "ix_audit_events_entity_id",
        "audit_events",
        ["entity_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_audit_events_tenant_id",
        "audit_events",
        ["tenant_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_audit_events_created_at",
        "audit_events",
        ["created_at"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_audit_events_created_at", table_name="audit_events")
    op.drop_index("ix_audit_events_tenant_id", table_name="audit_events")
    op.drop_index("ix_audit_events_entity_id", table_name="audit_events")
    op.drop_table("audit_events")
