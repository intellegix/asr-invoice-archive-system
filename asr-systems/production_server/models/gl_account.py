"""
ASR Production Server - GL Account ORM Model
Persistent GL account records for runtime-editable classification configuration.
"""

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

try:
    from ..config.database import Base
except (ImportError, SystemError):
    from config.database import Base  # type: ignore[no-redef]


class GLAccountRecord(Base):
    """Persistent GL account record for classification."""

    __tablename__ = "gl_accounts"

    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(50), index=True)
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str] = mapped_column(Text, default="")
    tenant_id: Mapped[str] = mapped_column(String(255), default="default")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    __table_args__ = (Index("ix_gl_accounts_tenant_category", "tenant_id", "category"),)
