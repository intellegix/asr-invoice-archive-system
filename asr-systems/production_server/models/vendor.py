"""
ASR Production Server - Vendor ORM Model
Persistent vendor records for GL classification and document routing.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

try:
    from ..config.database import Base
except (ImportError, SystemError):
    from config.database import Base  # type: ignore[no-redef]


class VendorRecord(Base):
    """Persistent vendor record for classification and routing."""

    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    contact_info: Mapped[dict] = mapped_column(JSON, default=dict)
    default_gl_account: Mapped[str | None] = mapped_column(String(10), nullable=True)
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    payment_terms: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payment_terms_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vendor_type: Mapped[str] = mapped_column(String(50), default="supplier")
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    total_amount_processed: Mapped[float] = mapped_column(Float, default=0.0)
    tenant_id: Mapped[str] = mapped_column(String(255), index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (Index("ix_vendors_tenant_name", "tenant_id", "name"),)
