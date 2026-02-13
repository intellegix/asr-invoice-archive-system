"""Add gl_accounts table and seed 79 accounts from constants.

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-13

Creates the gl_accounts table and seeds all 79 QuickBooks GL accounts
from the shared.core.constants.GL_ACCOUNTS dict so classification
can load from DB at runtime.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# Ensure shared/ is importable for GL_ACCOUNTS constant
_asr = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_asr / "shared"))

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create gl_accounts table
    op.create_table(
        "gl_accounts",
        sa.Column("code", sa.String(10), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("keywords", sa.JSON, nullable=True),
        sa.Column("active", sa.Boolean, default=True),
        sa.Column("description", sa.Text, default=""),
        sa.Column("tenant_id", sa.String(255), default="default"),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )
    op.create_index("ix_gl_accounts_category", "gl_accounts", ["category"])
    op.create_index(
        "ix_gl_accounts_tenant_category", "gl_accounts", ["tenant_id", "category"]
    )

    # Seed 79 accounts from constants
    from shared.core.constants import GL_ACCOUNTS

    gl_table = sa.table(
        "gl_accounts",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("category", sa.String),
        sa.column("keywords", sa.JSON),
        sa.column("active", sa.Boolean),
        sa.column("description", sa.Text),
        sa.column("tenant_id", sa.String),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )

    now = datetime.now(timezone.utc)
    conn = op.get_bind()

    for code, data in GL_ACCOUNTS.items():
        # Skip if already seeded (idempotent)
        exists = conn.execute(
            sa.text("SELECT 1 FROM gl_accounts WHERE code = :code"),
            {"code": str(code)},
        ).fetchone()

        if not exists:
            op.bulk_insert(
                gl_table,
                [
                    {
                        "code": str(code),
                        "name": data["name"],
                        "category": data["category"],
                        "keywords": data.get("keywords", []),
                        "active": True,
                        "description": "",
                        "tenant_id": "default",
                        "created_at": now,
                        "updated_at": now,
                    }
                ],
            )


def downgrade() -> None:
    op.drop_index("ix_gl_accounts_tenant_category", table_name="gl_accounts")
    op.drop_index("ix_gl_accounts_category", table_name="gl_accounts")
    op.drop_table("gl_accounts")
