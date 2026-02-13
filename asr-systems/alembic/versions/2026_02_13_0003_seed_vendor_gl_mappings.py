"""Seed vendor GL mappings from hardcoded dict.

Revision ID: 0003
Revises: 0002
Create Date: 2026-02-13

Migrates the 40 hardcoded vendor→GL mappings from GLAccountService into the
vendors table so classification uses a single DB-driven path.
"""

import uuid
from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The 40 vendor→GL mappings previously hardcoded in gl_account_service.py
_VENDOR_SEEDS = [
    # Materials/Supplies → 5000
    ("Home Depot", "5000", ["the home depot", "homedepot"]),
    ("Lowe's", "5000", ["lowes"]),
    ("ABC Supply", "5000", []),
    ("Beacon", "5000", ["beacon roofing"]),
    ("Ferguson", "5000", ["ferguson enterprises"]),
    # Utilities → 6600
    ("SDG&E", "6600", ["sdge", "san diego gas"]),
    ("Cox Communications", "6600", ["cox"]),
    ("Verizon", "6600", []),
    ("AT&T", "6600", ["att"]),
    ("USA Waste", "6600", []),
    ("Waste Management", "6600", []),
    ("Republic Services", "6600", ["republic"]),
    ("EDCO", "6600", ["edco waste"]),
    # Fuel → 6900
    ("Shell", "6900", ["shell oil"]),
    ("Chevron", "6900", []),
    ("Mobil", "6900", ["exxon mobil", "exxonmobil"]),
    ("Exxon", "6900", []),
    ("ARCO", "6900", []),
    # Professional Services → 5700
    ("Attorney", "5700", ["law firm", "legal"]),
    ("Accountant", "5700", ["cpa"]),
    # Insurance → 5500
    ("Insurance", "5500", []),
    ("Farmers Insurance", "5500", ["farmers"]),
    ("State Farm", "5500", []),
    ("Allstate", "5500", []),
]

_TENANT_ID = "default"


def upgrade() -> None:
    vendors = sa.table(
        "vendors",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("display_name", sa.String),
        sa.column("default_gl_account", sa.String),
        sa.column("aliases", sa.JSON),
        sa.column("tenant_id", sa.String),
        sa.column("vendor_type", sa.String),
        sa.column("active", sa.Boolean),
        sa.column("notes", sa.Text),
        sa.column("tags", sa.JSON),
        sa.column("contact_info", sa.JSON),
        sa.column("document_count", sa.Integer),
        sa.column("total_amount_processed", sa.Float),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )

    now = datetime.now(timezone.utc)

    for name, gl_code, aliases in _VENDOR_SEEDS:
        # Use INSERT with a subquery check to avoid duplicates
        # (name + tenant_id uniqueness)
        conn = op.get_bind()
        exists = conn.execute(
            sa.text(
                "SELECT 1 FROM vendors WHERE LOWER(name) = :name AND tenant_id = :tid"
            ),
            {"name": name.lower(), "tid": _TENANT_ID},
        ).fetchone()

        if not exists:
            op.bulk_insert(
                vendors,
                [
                    {
                        "id": str(uuid.uuid4()),
                        "name": name,
                        "display_name": name,
                        "default_gl_account": gl_code,
                        "aliases": aliases,
                        "tenant_id": _TENANT_ID,
                        "vendor_type": "supplier",
                        "active": True,
                        "notes": "Seeded from hardcoded vendor mapping",
                        "tags": ["seeded"],
                        "contact_info": {},
                        "document_count": 0,
                        "total_amount_processed": 0.0,
                        "created_at": now,
                        "updated_at": now,
                    }
                ],
            )


def downgrade() -> None:
    # Remove only seeded vendors (identified by the "seeded" tag/notes)
    op.execute(
        sa.text(
            "DELETE FROM vendors WHERE notes = 'Seeded from hardcoded vendor mapping'"
        )
    )
