"""
ASR Production Server - Vendor CRUD Service
Persistent vendor store backed by async SQLAlchemy (SQLite / PostgreSQL).
Follows the AuditTrailService pattern: get_async_session(), select(), session.add(), etc.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select

try:
    from ..config.database import get_async_session
    from ..models.vendor import VendorRecord
except (ImportError, SystemError):
    from config.database import get_async_session  # type: ignore[no-redef]
    from models.vendor import VendorRecord  # type: ignore[no-redef]

logger = logging.getLogger(__name__)


class VendorService:
    """Async vendor CRUD service backed by the database.

    Provides the same public interface as the previous in-memory service
    so that API endpoints require no changes.
    """

    def __init__(self) -> None:
        self.initialized = False

    async def initialize(self) -> None:
        """Mark service as ready. Table creation is handled by init_database()."""
        self.initialized = True
        logger.info("VendorService initialized (database-backed)")

    async def cleanup(self) -> None:
        """No-op — database connections are managed by the engine."""
        self.initialized = False
        logger.info("VendorService cleaned up")

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def list_vendors(
        self, tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return all vendors, optionally filtered by tenant."""
        try:
            async with get_async_session() as session:
                stmt = select(VendorRecord)
                if tenant_id:
                    stmt = stmt.where(VendorRecord.tenant_id == tenant_id)
                stmt = stmt.order_by(func.lower(VendorRecord.name))
                result = await session.execute(stmt)
                return [self._row_to_dict(r) for r in result.scalars().all()]
        except Exception:
            logger.exception("Failed to list vendors")
            return []

    async def get_vendor(
        self, vendor_id: str, tenant_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Return a single vendor by id, or ``None``.

        When *tenant_id* is provided the query is scoped so that only
        vendors belonging to that tenant are returned.
        """
        try:
            async with get_async_session() as session:
                stmt = select(VendorRecord).where(VendorRecord.id == vendor_id)
                if tenant_id is not None:
                    stmt = stmt.where(VendorRecord.tenant_id == tenant_id)
                result = await session.execute(stmt)
                row = result.scalar_one_or_none()
                return self._row_to_dict(row) if row else None
        except Exception:
            logger.exception("Failed to get vendor %s", vendor_id)
            return None

    async def create_vendor(
        self,
        name: str,
        tenant_id: str,
        display_name: Optional[str] = None,
        contact_info: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create and persist a new vendor. Returns the created vendor dict."""
        try:
            async with get_async_session() as session:
                row = VendorRecord(
                    name=name,
                    display_name=display_name or name,
                    contact_info=contact_info or {},
                    tenant_id=tenant_id,
                    notes=notes or "",
                    tags=tags or [],
                )
                session.add(row)
                await session.commit()
                await session.refresh(row)
                logger.info(
                    "vendor_crud action=create vendor_id=%s name=%s tenant_id=%s",
                    row.id,
                    name,
                    tenant_id,
                )
                return self._row_to_dict(row)
        except Exception:
            logger.exception("Failed to create vendor %s", name)
            raise

    async def update_vendor(
        self,
        vendor_id: str,
        updates: Dict[str, Any],
        tenant_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Apply partial updates to a vendor. Returns updated vendor or ``None``.

        When *tenant_id* is provided the lookup is scoped to that tenant,
        preventing cross-tenant modification.
        """
        allowed = {
            "name",
            "display_name",
            "contact_info",
            "notes",
            "tags",
            "default_gl_account",
            "aliases",
            "payment_terms",
            "payment_terms_days",
            "vendor_type",
            "active",
        }
        try:
            async with get_async_session() as session:
                stmt = select(VendorRecord).where(VendorRecord.id == vendor_id)
                if tenant_id is not None:
                    stmt = stmt.where(VendorRecord.tenant_id == tenant_id)
                result = await session.execute(stmt)
                row = result.scalar_one_or_none()
                if row is None:
                    return None

                for key, value in updates.items():
                    if key in allowed:
                        setattr(row, key, value)
                row.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

                await session.commit()
                await session.refresh(row)
                logger.info(
                    "vendor_crud action=update vendor_id=%s tenant_id=%s fields=%s",
                    vendor_id,
                    row.tenant_id,
                    list(updates.keys()),
                )
                return self._row_to_dict(row)
        except Exception:
            logger.exception("Failed to update vendor %s", vendor_id)
            raise

    async def delete_vendor(
        self, vendor_id: str, tenant_id: Optional[str] = None
    ) -> bool:
        """Delete a vendor. Returns ``True`` if found and removed.

        When *tenant_id* is provided the lookup is scoped to that tenant,
        preventing cross-tenant deletion.
        """
        try:
            async with get_async_session() as session:
                stmt = select(VendorRecord).where(VendorRecord.id == vendor_id)
                if tenant_id is not None:
                    stmt = stmt.where(VendorRecord.tenant_id == tenant_id)
                result = await session.execute(stmt)
                row = result.scalar_one_or_none()
                if row is None:
                    return False
                tenant_id = row.tenant_id
                await session.delete(row)
                await session.commit()
                logger.info(
                    "vendor_crud action=delete vendor_id=%s tenant_id=%s",
                    vendor_id,
                    tenant_id,
                )
                return True
        except Exception:
            logger.exception("Failed to delete vendor %s", vendor_id)
            return False

    async def get_vendor_stats(
        self, vendor_id: str, tenant_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Return stats for a vendor, or ``None`` if not found."""
        vendor = await self.get_vendor(vendor_id, tenant_id=tenant_id)
        if vendor is None:
            return None

        return {
            "documents": {
                "total": vendor["document_count"],
                "by_month": [],
                "by_gl_account": [],
            },
            "payments": {
                "accuracy": 0.0,
                "detection_methods": [],
                "status_distribution": {
                    "paid": 0,
                    "unpaid": 0,
                    "partial": 0,
                    "void": 0,
                },
            },
            "trends": {
                "document_volume": [],
                "amount_processed": [],
                "accuracy_over_time": [],
            },
        }

    # ------------------------------------------------------------------
    # Vendor matching (for GL classification integration)
    # ------------------------------------------------------------------

    async def match_vendor(
        self, name: str, tenant_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Find a vendor by case-insensitive name or alias match.

        Returns the first matching vendor dict, or ``None``.
        """
        if not name:
            return None
        name_lower = name.lower()
        try:
            async with get_async_session() as session:
                stmt = select(VendorRecord).where(VendorRecord.active.is_(True))
                if tenant_id:
                    stmt = stmt.where(VendorRecord.tenant_id == tenant_id)
                result = await session.execute(stmt)
                for row in result.scalars().all():
                    # Exact name match (case-insensitive)
                    if row.name.lower() == name_lower:
                        return self._row_to_dict(row)
                    # Alias match (case-insensitive)
                    aliases = row.aliases or []
                    for alias in aliases:
                        if isinstance(alias, str) and alias.lower() == name_lower:
                            return self._row_to_dict(row)
                return None
        except Exception:
            logger.exception("Failed to match vendor '%s'", name)
            return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_dict(row: VendorRecord) -> Dict[str, Any]:
        return {
            "id": row.id,
            "name": row.name,
            "display_name": row.display_name,
            "contact_info": row.contact_info or {},
            "default_gl_account": row.default_gl_account,
            "aliases": row.aliases or [],
            "payment_terms": row.payment_terms,
            "payment_terms_days": row.payment_terms_days,
            "vendor_type": row.vendor_type,
            "document_count": row.document_count,
            "total_amount_processed": row.total_amount_processed,
            "average_amount": 0.0,
            "last_document_date": None,
            "common_gl_accounts": [],
            "payment_accuracy": 0.0,
            "payment_patterns": {
                "paid": 0,
                "unpaid": 0,
                "partial": 0,
                "void": 0,
            },
            "tenant_id": row.tenant_id,
            "notes": row.notes or "",
            "tags": row.tags or [],
            "active": row.active,
            "created_at": (row.created_at.isoformat() if row.created_at else None),
            "updated_at": (row.updated_at.isoformat() if row.updated_at else None),
        }
