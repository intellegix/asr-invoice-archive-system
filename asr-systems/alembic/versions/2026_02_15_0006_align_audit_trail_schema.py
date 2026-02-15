"""Align audit_trail columns with ORM model.

Revision ID: 0006
Revises: 0005
Create Date: 2026-02-15

Migration 0001 created audit_events with columns: id (Integer), entity_id,
entity_type, action, details, metadata_json, created_at.  Migration 0005
renamed the table to audit_trail but left the columns unchanged.  The ORM
model (AuditTrailRecord) uses: id (String(36)), document_id, event_type,
event_data (JSON), user_id, system_component, timestamp, tenant_id.

This migration aligns the physical table with the ORM on PostgreSQL.
On SQLite the table is already correct (created by Base.metadata.create_all).
"""

import logging
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

logger = logging.getLogger(__name__)

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(inspector: sa.Inspector, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    try:
        columns = {c["name"] for c in inspector.get_columns(table)}
        return column in columns
    except Exception:
        return False


def _index_exists(inspector: sa.Inspector, table: str, index_name: str) -> bool:
    """Check if an index exists on a table."""
    try:
        indices = {idx["name"] for idx in inspector.get_indexes(table)}
        return index_name in indices
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "sqlite":
        # SQLite tables are created by Base.metadata.create_all() with correct
        # ORM columns.  No migration needed.
        return

    # --- PostgreSQL path ---
    inspector = sa.inspect(bind)

    # Guard: if columns already match ORM (fresh deploy with create_all),
    # skip the migration.
    if _column_exists(inspector, "audit_trail", "document_id") and not _column_exists(
        inspector, "audit_trail", "entity_id"
    ):
        logger.info("audit_trail already has ORM columns — skipping migration 0006")
        return

    # 1. Convert id from Integer to String(36) with UUID values
    #    Must be done before renames since we need to update existing rows.
    op.execute(
        "ALTER TABLE audit_trail ALTER COLUMN id SET DATA TYPE VARCHAR(36) "
        "USING id::text"
    )
    op.execute(
        "UPDATE audit_trail SET id = gen_random_uuid()::text WHERE id IS NOT NULL"
    )

    # 2. Widen tenant_id and user_id
    op.alter_column(
        "audit_trail",
        "tenant_id",
        type_=sa.String(255),
        existing_type=sa.String(100),
    )
    op.alter_column(
        "audit_trail",
        "user_id",
        type_=sa.String(255),
        existing_type=sa.String(100),
    )

    # 3. Add new columns before data migration
    op.add_column(
        "audit_trail",
        sa.Column("event_data", sa.JSON, nullable=True, server_default="{}"),
    )
    op.add_column(
        "audit_trail",
        sa.Column(
            "system_component",
            sa.String(100),
            nullable=True,
            server_default="'unknown'",
        ),
    )

    # 4. Data migration — preserve existing data in new columns
    op.execute("""
        UPDATE audit_trail
        SET event_data = jsonb_build_object(
                'legacy_details', COALESCE(details, ''),
                'legacy_metadata', COALESCE(metadata_json, '')
            )
        WHERE details IS NOT NULL OR metadata_json IS NOT NULL
        """)
    op.execute("""
        UPDATE audit_trail
        SET system_component = COALESCE(action, entity_type, 'unknown')
        WHERE system_component IS NULL OR system_component = 'unknown'
        """)

    # 5. Rename columns: entity_id → document_id, created_at → timestamp
    op.alter_column("audit_trail", "entity_id", new_column_name="document_id")
    op.alter_column("audit_trail", "created_at", new_column_name="timestamp")

    # 6. Drop old columns that have no ORM counterpart
    op.drop_column("audit_trail", "entity_type")
    op.drop_column("audit_trail", "action")
    op.drop_column("audit_trail", "details")
    op.drop_column("audit_trail", "metadata_json")

    # 7. Index changes
    #    Drop old indices (renamed in 0005 from audit_events_ to audit_trail_)
    if _index_exists(inspector, "audit_trail", "ix_audit_trail_entity_id"):
        op.drop_index("ix_audit_trail_entity_id", table_name="audit_trail")
    if _index_exists(inspector, "audit_trail", "ix_audit_trail_created_at"):
        op.drop_index("ix_audit_trail_created_at", table_name="audit_trail")

    #    Create ORM-matching composite indices
    op.create_index(
        "ix_audit_trail_doc_event", "audit_trail", ["document_id", "event_type"]
    )
    op.create_index(
        "ix_audit_trail_tenant_timestamp", "audit_trail", ["tenant_id", "timestamp"]
    )

    #    Single-column indices the ORM expects
    op.create_index("ix_audit_trail_document_id", "audit_trail", ["document_id"])
    op.create_index("ix_audit_trail_timestamp", "audit_trail", ["timestamp"])


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "sqlite":
        return

    # --- PostgreSQL reverse ---

    # Drop new indices
    op.drop_index("ix_audit_trail_timestamp", table_name="audit_trail")
    op.drop_index("ix_audit_trail_document_id", table_name="audit_trail")
    op.drop_index("ix_audit_trail_tenant_timestamp", table_name="audit_trail")
    op.drop_index("ix_audit_trail_doc_event", table_name="audit_trail")

    # Rename columns back
    op.alter_column("audit_trail", "document_id", new_column_name="entity_id")
    op.alter_column("audit_trail", "timestamp", new_column_name="created_at")

    # Re-add dropped columns
    op.add_column(
        "audit_trail",
        sa.Column("entity_type", sa.String(100), nullable=True),
    )
    op.add_column(
        "audit_trail",
        sa.Column("action", sa.String(100), nullable=True),
    )
    op.add_column(
        "audit_trail",
        sa.Column("details", sa.Text(), nullable=True),
    )
    op.add_column(
        "audit_trail",
        sa.Column("metadata_json", sa.Text(), nullable=True),
    )

    # Restore data from event_data/system_component back to legacy columns
    op.execute("""
        UPDATE audit_trail
        SET action = system_component,
            entity_type = system_component
        WHERE system_component IS NOT NULL
        """)

    # Drop new columns
    op.drop_column("audit_trail", "system_component")
    op.drop_column("audit_trail", "event_data")

    # Revert id to Integer (loses UUID values — downgrade is lossy)
    op.execute(
        "ALTER TABLE audit_trail ALTER COLUMN id SET DATA TYPE INTEGER " "USING 0"
    )

    # Revert tenant_id and user_id widths
    op.alter_column(
        "audit_trail",
        "tenant_id",
        type_=sa.String(100),
        existing_type=sa.String(255),
    )
    op.alter_column(
        "audit_trail",
        "user_id",
        type_=sa.String(100),
        existing_type=sa.String(255),
    )

    # Restore old indices
    op.create_index("ix_audit_trail_entity_id", "audit_trail", ["entity_id"])
    op.create_index("ix_audit_trail_created_at", "audit_trail", ["created_at"])
