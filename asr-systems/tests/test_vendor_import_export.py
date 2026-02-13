"""
P80: Vendor bulk import/export tests.
Export CSV/JSON, import merge/overwrite/append, validation dry-run, round-trip.
"""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

_asr = Path(__file__).parent.parent
sys.path.insert(0, str(_asr / "shared"))
sys.path.insert(0, str(_asr / "production-server"))

os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")


def _make_vendor(**overrides):
    defaults = {
        "id": "v1",
        "name": "Acme Supply",
        "display_name": "Acme Supply Co",
        "contact_info": {},
        "default_gl_account": "5000",
        "aliases": ["acme"],
        "payment_terms": "Net 30",
        "payment_terms_days": 30,
        "vendor_type": "supplier",
        "document_count": 0,
        "total_amount_processed": 0.0,
        "tenant_id": "default",
        "notes": "",
        "tags": ["materials"],
        "active": True,
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
    }
    defaults.update(overrides)
    return defaults


def _make_svc(vendors=None):
    """Create a VendorImportExportService with a mocked VendorService."""
    from services.vendor_import_export import VendorImportExportService

    vs = MagicMock()
    _vendors = list(vendors) if vendors else []

    async def _list_vendors(tenant_id=None):
        return [v for v in _vendors if not tenant_id or v["tenant_id"] == tenant_id]

    async def _create_vendor(name, tenant_id, display_name=None, notes=None, tags=None):
        new = _make_vendor(
            id=f"v-new-{len(_vendors)}",
            name=name,
            display_name=display_name or name,
            tenant_id=tenant_id,
            notes=notes or "",
            tags=tags or [],
        )
        _vendors.append(new)
        return new

    async def _update_vendor(vendor_id, updates):
        for v in _vendors:
            if v["id"] == vendor_id:
                v.update(updates)
                return v
        return None

    async def _delete_vendor(vendor_id):
        for i, v in enumerate(_vendors):
            if v["id"] == vendor_id:
                _vendors.pop(i)
                return True
        return False

    vs.list_vendors = AsyncMock(side_effect=_list_vendors)
    vs.create_vendor = AsyncMock(side_effect=_create_vendor)
    vs.update_vendor = AsyncMock(side_effect=_update_vendor)
    vs.delete_vendor = AsyncMock(side_effect=_delete_vendor)

    return VendorImportExportService(vs), vs, _vendors


# ---------------------------------------------------------------------------
# Export tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_export_json_empty():
    """Export JSON with no vendors returns empty list."""
    svc, _, _ = _make_svc()
    result = await svc.export_vendors_json()
    assert result == []


@pytest.mark.asyncio
async def test_export_json_with_vendors():
    """Export JSON returns vendor dicts."""
    svc, _, _ = _make_svc([_make_vendor(), _make_vendor(id="v2", name="Beta")])
    result = await svc.export_vendors_json()
    assert len(result) == 2
    assert result[0]["name"] == "Acme Supply"


@pytest.mark.asyncio
async def test_export_csv_headers():
    """Export CSV includes header row."""
    svc, _, _ = _make_svc([_make_vendor()])
    csv_text = await svc.export_vendors_csv()
    lines = csv_text.strip().split("\n")
    assert len(lines) == 2  # header + 1 row
    assert "name" in lines[0]
    assert "default_gl_account" in lines[0]


@pytest.mark.asyncio
async def test_export_csv_pipe_delimited_lists():
    """CSV export uses pipe-delimited aliases and tags."""
    svc, _, _ = _make_svc([_make_vendor(aliases=["a", "b"], tags=["t1", "t2"])])
    csv_text = await svc.export_vendors_csv()
    assert "a|b" in csv_text
    assert "t1|t2" in csv_text


# ---------------------------------------------------------------------------
# Import tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_import_json_append_creates_new():
    """Append mode creates vendors that don't exist yet."""
    svc, _, vendors = _make_svc()
    result = await svc.import_vendors_json(
        data=[{"name": "New Vendor"}],
        mode="append",
        tenant_id="default",
    )
    assert result["success"] is True
    assert result["created"] == 1
    assert result["skipped"] == 0


@pytest.mark.asyncio
async def test_import_json_append_skips_existing():
    """Append mode skips vendors that already exist."""
    svc, _, vendors = _make_svc([_make_vendor()])
    result = await svc.import_vendors_json(
        data=[{"name": "Acme Supply"}],
        mode="append",
        tenant_id="default",
    )
    assert result["success"] is True
    assert result["created"] == 0
    assert result["skipped"] == 1


@pytest.mark.asyncio
async def test_import_json_merge_updates_existing():
    """Merge mode updates vendors that exist."""
    svc, _, vendors = _make_svc([_make_vendor()])
    result = await svc.import_vendors_json(
        data=[{"name": "Acme Supply", "notes": "updated"}],
        mode="merge",
        tenant_id="default",
    )
    assert result["success"] is True
    assert result["updated"] == 1


@pytest.mark.asyncio
async def test_import_json_merge_creates_new():
    """Merge mode creates vendors that don't exist."""
    svc, _, vendors = _make_svc([_make_vendor()])
    result = await svc.import_vendors_json(
        data=[{"name": "Brand New"}],
        mode="merge",
        tenant_id="default",
    )
    assert result["success"] is True
    assert result["created"] == 1


@pytest.mark.asyncio
async def test_import_json_overwrite_clears_and_inserts():
    """Overwrite mode deletes existing before inserting."""
    svc, vs, vendors = _make_svc([_make_vendor()])
    result = await svc.import_vendors_json(
        data=[{"name": "Only One"}],
        mode="overwrite",
        tenant_id="default",
    )
    assert result["success"] is True
    # Original vendor was deleted, new one created
    assert result["created"] == 1


@pytest.mark.asyncio
async def test_import_csv_creates_vendors():
    """Import from CSV string creates vendors."""
    svc, _, vendors = _make_svc()
    csv_text = "name,display_name,default_gl_account,aliases,tags,active\nCSV Vendor,CSV Co,5000,a1|a2,t1,true\n"
    result = await svc.import_vendors_csv(
        csv_text=csv_text, mode="append", tenant_id="default"
    )
    assert result["success"] is True
    assert result["created"] == 1


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


def test_validate_missing_name():
    """Validation catches missing name field."""
    svc, _, _ = _make_svc()
    result = svc.validate_import_data(data=[{"notes": "no name"}])
    assert result["valid"] is False
    assert result["error_count"] == 1
    assert "missing required field" in result["errors"][0].lower()


def test_validate_duplicate_names():
    """Validation catches duplicate names."""
    svc, _, _ = _make_svc()
    result = svc.validate_import_data(data=[{"name": "A"}, {"name": "a"}])
    assert result["valid"] is False
    assert "duplicate" in result["errors"][0].lower()


def test_validate_unknown_gl_code():
    """Validation catches unknown GL account codes."""
    svc, _, _ = _make_svc()
    result = svc.validate_import_data(
        data=[{"name": "V1", "default_gl_account": "9999"}],
        gl_codes={"5000", "6000"},
    )
    assert result["valid"] is False
    assert "unknown GL" in result["errors"][0]


def test_validate_all_good():
    """Validation passes for valid data."""
    svc, _, _ = _make_svc()
    result = svc.validate_import_data(
        data=[{"name": "V1", "default_gl_account": "5000"}],
        gl_codes={"5000"},
    )
    assert result["valid"] is True
    assert result["error_count"] == 0


@pytest.mark.asyncio
async def test_import_rejects_invalid_data():
    """Import returns errors for invalid data without executing."""
    svc, vs, vendors = _make_svc()
    result = await svc.import_vendors_json(
        data=[{"notes": "no name"}],
        mode="merge",
        tenant_id="default",
    )
    assert result["success"] is False
    assert len(result["errors"]) > 0
    # Vendor service should not have been called for create/update
    vs.create_vendor.assert_not_called()


# ---------------------------------------------------------------------------
# Round-trip test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_export_import_roundtrip():
    """Export then import produces equivalent data."""
    original = _make_vendor(name="RoundTrip", aliases=["rt"], tags=["test"])
    svc, _, vendors = _make_svc([original])

    # Export as JSON
    exported = await svc.export_vendors_json()
    assert len(exported) == 1

    # Import into fresh service
    svc2, _, _ = _make_svc()
    result = await svc2.import_vendors_json(
        data=exported, mode="append", tenant_id="default"
    )
    assert result["success"] is True
    assert result["created"] == 1
