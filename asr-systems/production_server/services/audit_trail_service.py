"""
ASR Production Server - Audit Trail Service
Persists audit trail entries to the database. Failures are logged but never
propagate — audit recording must not break the document routing pipeline.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from shared.core.models import AuditTrailEntry
from sqlalchemy import delete, select

try:
    from ..config.database import get_async_session
    from ..models.audit_trail import AuditTrailRecord
except (ImportError, SystemError):
    from config.database import get_async_session  # type: ignore[no-redef]
    from models.audit_trail import AuditTrailRecord  # type: ignore[no-redef]

logger = logging.getLogger(__name__)


class AuditTrailService:
    """Async audit trail persistence following the project's initialize/cleanup pattern."""

    def __init__(self, enabled: bool = True, retention_days: int = 2555) -> None:
        self.enabled = enabled
        self.retention_days = retention_days
        self.initialized = False
        self._records_written: int = 0

    async def initialize(self) -> None:
        self.initialized = True
        logger.info(
            "Audit Trail Service initialized (enabled=%s, retention=%d days)",
            self.enabled,
            self.retention_days,
        )

    async def cleanup(self) -> None:
        logger.info("Cleaning up Audit Trail Service...")
        self.initialized = False

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def record(self, entry: AuditTrailEntry) -> None:
        """Persist an AuditTrailEntry. Never raises — logs on failure."""
        if not self.enabled:
            return
        try:
            async with get_async_session() as session:
                row = AuditTrailRecord(
                    document_id=entry.document_id,
                    event_type=entry.event_type,
                    event_data=entry.event_data,
                    user_id=entry.user_id,
                    system_component=entry.system_component,
                    timestamp=entry.timestamp,
                    tenant_id=entry.tenant_id,
                )
                session.add(row)
                await session.commit()
                self._records_written += 1
        except Exception:
            logger.exception(
                "Failed to persist audit trail entry for document %s", entry.document_id
            )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def query_by_document(
        self, document_id: str, tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return audit entries for a document, optionally scoped to tenant."""
        try:
            async with get_async_session() as session:
                stmt = select(AuditTrailRecord).where(
                    AuditTrailRecord.document_id == document_id
                )
                if tenant_id:
                    stmt = stmt.where(AuditTrailRecord.tenant_id == tenant_id)
                stmt = stmt.order_by(AuditTrailRecord.timestamp)
                result = await session.execute(stmt)
                return [self._row_to_dict(r) for r in result.scalars().all()]
        except Exception:
            logger.exception("Failed to query audit trail for document %s", document_id)
            return []

    async def query_by_tenant(
        self,
        tenant_id: str,
        event_type: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Return audit entries for a tenant with optional filters."""
        try:
            async with get_async_session() as session:
                stmt = select(AuditTrailRecord).where(
                    AuditTrailRecord.tenant_id == tenant_id
                )
                if event_type:
                    stmt = stmt.where(AuditTrailRecord.event_type == event_type)
                if since:
                    stmt = stmt.where(AuditTrailRecord.timestamp >= since)
                stmt = stmt.order_by(AuditTrailRecord.timestamp.desc()).limit(limit)
                result = await session.execute(stmt)
                return [self._row_to_dict(r) for r in result.scalars().all()]
        except Exception:
            logger.exception("Failed to query audit trail for tenant %s", tenant_id)
            return []

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    async def purge_expired(self) -> int:
        """Delete records older than retention_days. Returns count deleted."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        try:
            async with get_async_session() as session:
                stmt = delete(AuditTrailRecord).where(
                    AuditTrailRecord.timestamp < cutoff
                )
                result = await session.execute(stmt)
                await session.commit()
                deleted: int = result.rowcount if result.rowcount is not None else 0  # type: ignore[attr-defined]
                logger.info("Purged %d expired audit trail records", deleted)
                return deleted
        except Exception:
            logger.exception("Failed to purge expired audit trail records")
            return 0

    # ------------------------------------------------------------------
    # Health / Stats
    # ------------------------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:
        """Return stats for the health endpoint."""
        return {
            "enabled": self.enabled,
            "initialized": self.initialized,
            "records_written": self._records_written,
            "retention_days": self.retention_days,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_dict(row: AuditTrailRecord) -> Dict[str, Any]:
        return {
            "id": row.id,
            "document_id": row.document_id,
            "event_type": row.event_type,
            "event_data": row.event_data,
            "user_id": row.user_id,
            "system_component": row.system_component,
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            "tenant_id": row.tenant_id,
        }
