"""Add vendors table.

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-13

Adds persistent vendor storage to replace the in-memory VendorService dict.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vendors",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("contact_info", sa.JSON(), server_default="{}"),
        sa.Column("default_gl_account", sa.String(10), nullable=True),
        sa.Column("aliases", sa.JSON(), server_default="[]"),
        sa.Column("payment_terms", sa.String(50), nullable=True),
        sa.Column("payment_terms_days", sa.Integer(), nullable=True),
        sa.Column(
            "vendor_type", sa.String(50), nullable=False, server_default="supplier"
        ),
        sa.Column("document_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "total_amount_processed",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),
        sa.Column("tenant_id", sa.String(255), nullable=False),
        sa.Column("notes", sa.Text(), server_default=""),
        sa.Column("tags", sa.JSON(), server_default="[]"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        if_not_exists=True,
    )
    op.create_index("ix_vendors_name", "vendors", ["name"], if_not_exists=True)
    op.create_index(
        "ix_vendors_tenant_id", "vendors", ["tenant_id"], if_not_exists=True
    )
    op.create_index(
        "ix_vendors_tenant_name",
        "vendors",
        ["tenant_id", "name"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_vendors_tenant_name", table_name="vendors")
    op.drop_index("ix_vendors_tenant_id", table_name="vendors")
    op.drop_index("ix_vendors_name", table_name="vendors")
    op.drop_table("vendors")
