"""
ASR Production Server - Vendor Bulk Import/Export Service
CSV and JSON import/export with merge/overwrite/append modes.
"""

import csv
import io
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Fields that can be exported/imported
VENDOR_EXPORT_FIELDS = [
    "name",
    "display_name",
    "default_gl_account",
    "aliases",
    "payment_terms",
    "payment_terms_days",
    "vendor_type",
    "notes",
    "tags",
    "active",
    "tenant_id",
]


class VendorImportExportService:
    """Bulk import/export of vendors in CSV and JSON formats."""

    def __init__(self, vendor_service: Any) -> None:
        self.vendor_service = vendor_service

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    async def export_vendors_json(
        self, tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Export vendors as a list of dicts (JSON-serialisable)."""
        vendors = await self.vendor_service.list_vendors(tenant_id=tenant_id)
        return [self._export_row(v) for v in vendors]

    async def export_vendors_csv(self, tenant_id: Optional[str] = None) -> str:
        """Export vendors as a CSV string."""
        vendors = await self.vendor_service.list_vendors(tenant_id=tenant_id)
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=VENDOR_EXPORT_FIELDS)
        writer.writeheader()
        for v in vendors:
            row = self._export_row(v)
            # Flatten list fields for CSV
            row["aliases"] = "|".join(row.get("aliases") or [])
            row["tags"] = "|".join(row.get("tags") or [])
            writer.writerow(row)
        return buf.getvalue()

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    async def import_vendors_json(
        self,
        data: List[Dict[str, Any]],
        mode: str = "merge",
        tenant_id: str = "default",
        gl_codes: Optional[set] = None,
    ) -> Dict[str, Any]:
        """Import vendors from JSON list.

        Modes:
            merge   - update existing (by name), create new
            overwrite - delete all tenant vendors first, then insert
            append  - insert only, skip duplicates
        """
        errors = self._validate_import_data(data, gl_codes)
        if errors:
            return {
                "success": False,
                "created": 0,
                "updated": 0,
                "skipped": 0,
                "errors": errors,
            }

        return await self._execute_import(data, mode, tenant_id)

    async def import_vendors_csv(
        self,
        csv_text: str,
        mode: str = "merge",
        tenant_id: str = "default",
        gl_codes: Optional[set] = None,
    ) -> Dict[str, Any]:
        """Import vendors from CSV string."""
        reader = csv.DictReader(io.StringIO(csv_text))
        rows: List[Dict[str, Any]] = []
        for row in reader:
            # Unflatten list fields
            if "aliases" in row and isinstance(row["aliases"], str):
                row["aliases"] = [
                    a.strip() for a in row["aliases"].split("|") if a.strip()
                ]
            if "tags" in row and isinstance(row["tags"], str):
                row["tags"] = [t.strip() for t in row["tags"].split("|") if t.strip()]
            if "payment_terms_days" in row and row["payment_terms_days"]:
                try:
                    row["payment_terms_days"] = int(row["payment_terms_days"])
                except ValueError:
                    row["payment_terms_days"] = None
            if "active" in row:
                row["active"] = str(row["active"]).lower() in ("true", "1", "yes")
            rows.append(row)

        errors = self._validate_import_data(rows, gl_codes)
        if errors:
            return {
                "success": False,
                "created": 0,
                "updated": 0,
                "skipped": 0,
                "errors": errors,
            }

        return await self._execute_import(rows, mode, tenant_id)

    def validate_import_data(
        self,
        data: List[Dict[str, Any]],
        gl_codes: Optional[set] = None,
    ) -> Dict[str, Any]:
        """Dry-run validation without executing import."""
        errors = self._validate_import_data(data, gl_codes)
        return {
            "valid": len(errors) == 0,
            "total_rows": len(data),
            "error_count": len(errors),
            "errors": errors,
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _validate_import_data(
        self, data: List[Dict[str, Any]], gl_codes: Optional[set] = None
    ) -> List[str]:
        """Return a list of validation error strings."""
        errors: List[str] = []
        names_seen: set = set()

        for idx, row in enumerate(data):
            name = row.get("name", "").strip()
            if not name:
                errors.append(f"Row {idx + 1}: missing required field 'name'")
                continue
            if name.lower() in names_seen:
                errors.append(f"Row {idx + 1}: duplicate name '{name}'")
            names_seen.add(name.lower())

            gl = row.get("default_gl_account")
            if gl and gl_codes and gl not in gl_codes:
                errors.append(f"Row {idx + 1}: unknown GL account code '{gl}'")

        return errors

    async def _execute_import(
        self, data: List[Dict[str, Any]], mode: str, tenant_id: str
    ) -> Dict[str, Any]:
        """Run the actual import logic."""
        created = 0
        updated = 0
        skipped = 0

        if mode == "overwrite":
            # Delete all tenant vendors first
            existing = await self.vendor_service.list_vendors(tenant_id=tenant_id)
            for v in existing:
                await self.vendor_service.delete_vendor(v["id"])

        # Build name→vendor lookup for merge/append
        existing_vendors = await self.vendor_service.list_vendors(tenant_id=tenant_id)
        name_map = {v["name"].lower(): v for v in existing_vendors}

        for row in data:
            name = row["name"].strip()
            existing = name_map.get(name.lower())

            if existing and mode == "append":
                skipped += 1
                continue

            if existing and mode in ("merge", "overwrite"):
                # Update existing vendor
                updates = {
                    k: v
                    for k, v in row.items()
                    if k != "name" and k in VENDOR_EXPORT_FIELDS
                }
                await self.vendor_service.update_vendor(existing["id"], updates)
                updated += 1
            else:
                # Create new vendor
                await self.vendor_service.create_vendor(
                    name=name,
                    tenant_id=tenant_id,
                    display_name=row.get("display_name", name),
                    notes=row.get("notes", ""),
                    tags=row.get("tags", []),
                )
                # Apply additional fields via update
                vendor_list = await self.vendor_service.list_vendors(
                    tenant_id=tenant_id
                )
                new_vendor = next(
                    (v for v in vendor_list if v["name"].lower() == name.lower()), None
                )
                if new_vendor:
                    extra_updates = {}
                    for f in (
                        "default_gl_account",
                        "aliases",
                        "payment_terms",
                        "payment_terms_days",
                        "vendor_type",
                    ):
                        if f in row and row[f]:
                            extra_updates[f] = row[f]
                    if extra_updates:
                        await self.vendor_service.update_vendor(
                            new_vendor["id"], extra_updates
                        )
                created += 1

        return {
            "success": True,
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "errors": [],
        }

    @staticmethod
    def _export_row(vendor: Dict[str, Any]) -> Dict[str, Any]:
        """Extract exportable fields from a vendor dict."""
        return {k: vendor.get(k) for k in VENDOR_EXPORT_FIELDS}
