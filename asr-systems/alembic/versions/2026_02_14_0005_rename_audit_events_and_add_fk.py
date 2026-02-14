"""Rename audit_events → audit_trail and add vendor FK.

Revision ID: 0005
Revises: 0004
Create Date: 2026-02-14

The ORM model AuditTrailRecord uses __tablename__ = "audit_trail" but
migration 0001 created the table as "audit_events".  This migration aligns
the physical table name with the ORM and adds a FK from vendors.default_gl_account
to gl_accounts.code.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Rename audit_events → audit_trail ---
    op.rename_table("audit_events", "audit_trail")

    # Rename indices to match new table name.
    # SQLite doesn't support ALTER INDEX, so we drop and re-create.
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "sqlite":
        # SQLite: drop old indices, create new ones on renamed table
        op.drop_index("ix_audit_events_entity_id", table_name="audit_trail")
        op.drop_index("ix_audit_events_tenant_id", table_name="audit_trail")
        op.drop_index("ix_audit_events_created_at", table_name="audit_trail")
        op.create_index(
            "ix_audit_trail_entity_id", "audit_trail", ["entity_id"]
        )
        op.create_index(
            "ix_audit_trail_tenant_id", "audit_trail", ["tenant_id"]
        )
        op.create_index(
            "ix_audit_trail_created_at", "audit_trail", ["created_at"]
        )
    else:
        # PostgreSQL supports ALTER INDEX ... RENAME TO
        op.execute(
            "ALTER INDEX ix_audit_events_entity_id RENAME TO ix_audit_trail_entity_id"
        )
        op.execute(
            "ALTER INDEX ix_audit_events_tenant_id RENAME TO ix_audit_trail_tenant_id"
        )
        op.execute(
            "ALTER INDEX ix_audit_events_created_at RENAME TO ix_audit_trail_created_at"
        )

    # --- Add FK: vendors.default_gl_account → gl_accounts.code ---
    # Only for PostgreSQL — SQLite doesn't enforce FKs by default and
    # can't ALTER TABLE ADD CONSTRAINT.
    if dialect != "sqlite":
        op.create_foreign_key(
            "fk_vendors_default_gl_account",
            "vendors",
            "gl_accounts",
            ["default_gl_account"],
            ["code"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # --- Drop FK ---
    if dialect != "sqlite":
        op.drop_constraint(
            "fk_vendors_default_gl_account", "vendors", type_="foreignkey"
        )

    # --- Rename audit_trail → audit_events ---
    if dialect == "sqlite":
        op.drop_index("ix_audit_trail_entity_id", table_name="audit_trail")
        op.drop_index("ix_audit_trail_tenant_id", table_name="audit_trail")
        op.drop_index("ix_audit_trail_created_at", table_name="audit_trail")

    op.rename_table("audit_trail", "audit_events")

    if dialect == "sqlite":
        op.create_index(
            "ix_audit_events_entity_id", "audit_events", ["entity_id"]
        )
        op.create_index(
            "ix_audit_events_tenant_id", "audit_events", ["tenant_id"]
        )
        op.create_index(
            "ix_audit_events_created_at", "audit_events", ["created_at"]
        )
    else:
        op.execute(
            "ALTER INDEX ix_audit_trail_entity_id RENAME TO ix_audit_events_entity_id"
        )
        op.execute(
            "ALTER INDEX ix_audit_trail_tenant_id RENAME TO ix_audit_events_tenant_id"
        )
        op.execute(
            "ALTER INDEX ix_audit_trail_created_at RENAME TO ix_audit_events_created_at"
        )
