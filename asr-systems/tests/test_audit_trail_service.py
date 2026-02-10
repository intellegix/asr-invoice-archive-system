"""
Unit Tests for Audit Trail Service
Uses in-memory SQLite via aiosqlite — no disk I/O.
"""

import pytest
from datetime import datetime, timedelta

from config.database import init_database, close_database
from models.audit_trail import AuditTrailRecord  # noqa: F401 — registers table
from services.audit_trail_service import AuditTrailService
from shared.core.models import AuditTrailEntry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def db():
    """Spin up an in-memory SQLite DB for each test."""
    await init_database("sqlite:///:memory:")
    yield
    await close_database()


@pytest.fixture
async def service(db):
    svc = AuditTrailService(enabled=True, retention_days=30)
    await svc.initialize()
    return svc


def _entry(
    document_id: str = "doc-001",
    tenant_id: str = "tenant-a",
    event_type: str = "billing_routing",
    **kwargs,
) -> AuditTrailEntry:
    return AuditTrailEntry(
        document_id=document_id,
        event_type=event_type,
        event_data=kwargs.get("event_data", {"destination": "open_payable"}),
        system_component="billing_router_service",
        tenant_id=tenant_id,
        timestamp=kwargs.get("timestamp", datetime.utcnow()),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAuditTrail:
    @pytest.mark.asyncio
    async def test_record_and_query(self, service):
        await service.record(_entry())
        rows = await service.query_by_document("doc-001")
        assert len(rows) == 1
        assert rows[0]["document_id"] == "doc-001"
        assert rows[0]["event_type"] == "billing_routing"

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, service):
        await service.record(_entry(document_id="doc-001", tenant_id="tenant-a"))
        await service.record(_entry(document_id="doc-001", tenant_id="tenant-b"))

        rows_a = await service.query_by_document("doc-001", tenant_id="tenant-a")
        rows_b = await service.query_by_document("doc-001", tenant_id="tenant-b")
        assert len(rows_a) == 1
        assert len(rows_b) == 1
        assert rows_a[0]["tenant_id"] == "tenant-a"

    @pytest.mark.asyncio
    async def test_disabled_service_skips_write(self, db):
        svc = AuditTrailService(enabled=False, retention_days=30)
        await svc.initialize()
        await svc.record(_entry())
        rows = await svc.query_by_document("doc-001")
        # Service is disabled, but query still works — just no records
        assert len(rows) == 0

    @pytest.mark.asyncio
    async def test_filtered_query_by_event_type(self, service):
        await service.record(_entry(event_type="billing_routing"))
        await service.record(_entry(event_type="classification"))
        rows = await service.query_by_tenant("tenant-a", event_type="classification")
        assert len(rows) == 1
        assert rows[0]["event_type"] == "classification"

    @pytest.mark.asyncio
    async def test_purge_expired(self, service):
        old_ts = datetime.utcnow() - timedelta(days=60)
        await service.record(_entry(timestamp=old_ts))
        await service.record(_entry(document_id="doc-new"))

        deleted = await service.purge_expired()
        assert deleted == 1

        remaining = await service.query_by_tenant("tenant-a")
        assert len(remaining) == 1
        assert remaining[0]["document_id"] == "doc-new"
