"""
ASR Production Server - Vendor CRUD Service
In-memory vendor store with optional future persistence.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VendorService:
    """In-memory vendor CRUD service.

    Stores vendor records in a dict keyed by vendor ``id``.
    Each vendor is a plain dict matching the frontend ``Vendor`` interface.
    """

    def __init__(self) -> None:
        self._vendors: Dict[str, Dict[str, Any]] = {}

    async def initialize(self) -> None:
        """No-op for in-memory backend; keeps parity with other services."""
        logger.info("VendorService initialized (in-memory)")

    async def cleanup(self) -> None:
        """Clear in-memory store."""
        self._vendors.clear()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def _make_vendor(
        self,
        name: str,
        tenant_id: str,
        display_name: Optional[str] = None,
        contact_info: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Build a vendor dict with sensible defaults."""
        now = datetime.utcnow().isoformat()
        return {
            "id": str(uuid.uuid4()),
            "name": name,
            "display_name": display_name or name,
            "contact_info": contact_info or {},
            "document_count": 0,
            "total_amount_processed": 0.0,
            "average_amount": 0.0,
            "last_document_date": None,
            "common_gl_accounts": [],
            "payment_accuracy": 0.0,
            "payment_patterns": {"paid": 0, "unpaid": 0, "partial": 0, "void": 0},
            "tenant_id": tenant_id,
            "notes": notes or "",
            "tags": tags or [],
            "created_at": now,
            "updated_at": now,
        }

    async def list_vendors(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return all vendors, optionally filtered by tenant."""
        vendors = list(self._vendors.values())
        if tenant_id:
            vendors = [v for v in vendors if v["tenant_id"] == tenant_id]
        return sorted(vendors, key=lambda v: v["name"].lower())

    async def get_vendor(self, vendor_id: str) -> Optional[Dict[str, Any]]:
        """Return a single vendor by id, or ``None``."""
        return self._vendors.get(vendor_id)

    async def create_vendor(
        self,
        name: str,
        tenant_id: str,
        display_name: Optional[str] = None,
        contact_info: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create and store a new vendor. Returns the created vendor dict."""
        vendor = self._make_vendor(
            name=name,
            tenant_id=tenant_id,
            display_name=display_name,
            contact_info=contact_info,
            notes=notes,
            tags=tags,
        )
        self._vendors[vendor["id"]] = vendor
        logger.info("Vendor created id=%s name=%s", vendor["id"], name)
        return vendor

    async def update_vendor(
        self, vendor_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Apply partial updates to a vendor. Returns updated vendor or ``None``."""
        vendor = self._vendors.get(vendor_id)
        if vendor is None:
            return None

        # Only allow updating known mutable fields
        allowed = {
            "name",
            "display_name",
            "contact_info",
            "notes",
            "tags",
        }
        for key, value in updates.items():
            if key in allowed:
                vendor[key] = value

        vendor["updated_at"] = datetime.utcnow().isoformat()
        return vendor

    async def delete_vendor(self, vendor_id: str) -> bool:
        """Delete a vendor. Returns ``True`` if found and removed."""
        if vendor_id in self._vendors:
            del self._vendors[vendor_id]
            logger.info("Vendor deleted id=%s", vendor_id)
            return True
        return False

    async def get_vendor_stats(self, vendor_id: str) -> Optional[Dict[str, Any]]:
        """Return stats for a vendor, or ``None`` if not found."""
        vendor = self._vendors.get(vendor_id)
        if vendor is None:
            return None

        return {
            "documents": {
                "total": vendor["document_count"],
                "by_month": [],
                "by_gl_account": [],
            },
            "payments": {
                "accuracy": vendor["payment_accuracy"],
                "detection_methods": [],
                "status_distribution": vendor["payment_patterns"],
            },
            "trends": {
                "document_volume": [],
                "amount_processed": [],
                "accuracy_over_time": [],
            },
        }
