"""
ASR Production Server - Audit Trail ORM Model
Persistent audit trail records for billing routing decisions.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

try:
    from ..config.database import Base
except (ImportError, SystemError):
    from config.database import Base  # type: ignore[no-redef]


class AuditTrailRecord(Base):
    """Persistent audit trail record for document routing events."""

    __tablename__ = "audit_trail"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    document_id: Mapped[str] = mapped_column(String(255), index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    event_data: Mapped[dict] = mapped_column(JSON, default=dict)
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    system_component: Mapped[str] = mapped_column(String(100))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(255), index=True)

    __table_args__ = (
        Index("ix_audit_trail_tenant_timestamp", "tenant_id", "timestamp"),
        Index("ix_audit_trail_doc_event", "document_id", "event_type"),
    )
