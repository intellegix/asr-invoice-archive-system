"""
Unit Tests for Multi-Tenant Isolation
Tests that document storage, retrieval, and API responses
respect tenant boundaries.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "production-server"))

from services.storage_service import ProductionStorageService


class _FakeMetadata:
    """Lightweight metadata stub matching the attributes storage_service accesses.

    The Pydantic DocumentMetadata model uses ``mime_type`` but storage_service
    reads ``content_type`` via getattr.  This stub exposes both attributes so
    store/retrieve round-trips work in tests.
    """

    def __init__(self, tenant_id, filename="invoice.pdf"):
        self.filename = filename
        self.file_size = 100
        self.mime_type = "application/pdf"
        self.content_type = "application/pdf"
        self.tenant_id = tenant_id
        self.upload_source = "test"
        self.scanner_id = None
        self.scanner_metadata = {}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def storage(tmp_path):
    """Initialize a local storage service with a temporary directory."""
    config = {"backend": "local", "local_path": str(tmp_path / "storage")}
    service = ProductionStorageService(config)
    await service.initialize()
    return service


def _make_metadata(tenant_id, filename="invoice.pdf"):
    """Create a lightweight metadata object for testing."""
    return _FakeMetadata(tenant_id=tenant_id, filename=filename)


# ---------------------------------------------------------------------------
# Storage-level tenant isolation
# ---------------------------------------------------------------------------


class TestStorageTenantIsolation:
    @pytest.mark.asyncio
    async def test_upload_creates_tenant_scoped_path(self, storage):
        """Documents should be stored under a tenant-specific directory."""
        meta = _make_metadata("tenant-alpha")
        result = await storage.store_document("doc-alpha-1", b"alpha data", meta)
        assert result.success is True
        assert "tenant-alpha" in result.storage_path

    @pytest.mark.asyncio
    async def test_tenant_a_docs_separated_from_tenant_b(self, storage):
        """Documents for different tenants must reside in separate directories."""
        meta_a = _make_metadata("tenant-a")
        res_a = await storage.store_document("doc-a-001", b"secret A", meta_a)
        assert res_a.success is True

        meta_b = _make_metadata("tenant-b")
        res_b = await storage.store_document("doc-b-001", b"secret B", meta_b)
        assert res_b.success is True

        # Verify files land in separate tenant directories
        docs_a = list(storage.base_path.glob("documents/tenant-a/*"))
        docs_b = list(storage.base_path.glob("documents/tenant-b/*"))
        assert len(docs_a) == 1
        assert len(docs_b) == 1

        # Verify content integrity via filesystem
        assert Path(res_a.storage_path).read_bytes() == b"secret A"
        assert Path(res_b.storage_path).read_bytes() == b"secret B"

        # Tenant A's directory must not contain tenant B's file
        a_filenames = {f.name for f in docs_a}
        b_filenames = {f.name for f in docs_b}
        assert a_filenames.isdisjoint(b_filenames)

    @pytest.mark.asyncio
    async def test_default_tenant_has_own_space(self, storage):
        """The 'default' tenant should have its own isolated storage area."""
        meta = _make_metadata("default")
        result = await storage.store_document("doc-default-1", b"default data", meta)
        assert result.success is True
        assert "default" in result.storage_path

        # Verify file actually exists in the default tenant directory
        docs_default = list(storage.base_path.glob("documents/default/*"))
        assert len(docs_default) == 1
        assert Path(result.storage_path).read_bytes() == b"default data"

    @pytest.mark.asyncio
    async def test_metadata_isolated_per_tenant(self, storage):
        """Metadata JSON files should be stored in tenant-scoped directories."""
        meta_x = _make_metadata("tenant-x")
        meta_y = _make_metadata("tenant-y")

        await storage.store_document("doc-x-1", b"x data", meta_x)
        await storage.store_document("doc-y-1", b"y data", meta_y)

        meta_x_files = list(storage.base_path.glob("metadata/tenant-x/*.json"))
        meta_y_files = list(storage.base_path.glob("metadata/tenant-y/*.json"))
        assert len(meta_x_files) == 1
        assert len(meta_y_files) == 1


# ---------------------------------------------------------------------------
# API-level tenant isolation (via TestClient)
# ---------------------------------------------------------------------------


class TestAPITenantIsolation:
    """Test tenant isolation through the full FastAPI middleware stack."""

    @pytest.fixture(scope="class")
    def client(self):
        """Create a TestClient using the real app (with lifespan)."""
        from fastapi.testclient import TestClient
        from production_server.api.main import app

        with TestClient(app, raise_server_exceptions=False) as c:
            yield c

    def test_response_tenant_matches_request(self, client):
        """The X-Tenant-ID in the response should match the request header."""
        resp = client.get(
            "/api/v1/gl-accounts",
            headers={
                "Authorization": "Bearer test-key",
                "X-Tenant-ID": "acme-corp",
            },
        )
        # The response should include the tenant header
        assert resp.headers.get("X-Tenant-ID") == "acme-corp"

    def test_different_tenants_get_own_headers(self, client):
        """Two sequential requests with different tenants should each get their own ID back."""
        resp_a = client.get(
            "/api/v1/gl-accounts",
            headers={
                "Authorization": "Bearer test-key",
                "X-Tenant-ID": "tenant-alpha",
            },
        )
        resp_b = client.get(
            "/api/v1/gl-accounts",
            headers={
                "Authorization": "Bearer test-key",
                "X-Tenant-ID": "tenant-beta",
            },
        )
        assert resp_a.headers.get("X-Tenant-ID") == "tenant-alpha"
        assert resp_b.headers.get("X-Tenant-ID") == "tenant-beta"


# ---------------------------------------------------------------------------
# Scanner registration scoped to tenant
# ---------------------------------------------------------------------------


class TestScannerTenantScope:
    @pytest.mark.asyncio
    async def test_scanner_registration_includes_tenant(self):
        """Scanner registration should store the tenant_id."""
        from services.scanner_manager_service import ScannerManagerService

        service = ScannerManagerService(max_clients=10)
        service.initialized = True

        result = await service.register_scanner(
            scanner_id="scanner-001",
            name="Office Scanner",
            version="1.0.0",
            capabilities=["pdf", "jpg"],
            ip_address="192.168.1.100",
            tenant_id="tenant-gamma",
        )
        assert result["status"] == "registered"

        scanners = await service.get_connected_scanners()
        gamma_scanners = [s for s in scanners if s["tenant_id"] == "tenant-gamma"]
        assert len(gamma_scanners) == 1
        assert gamma_scanners[0]["scanner_id"] == "scanner-001"

    @pytest.mark.asyncio
    async def test_scanners_from_different_tenants_isolated(self):
        """Scanners registered under different tenants should be separately tracked."""
        from services.scanner_manager_service import ScannerManagerService

        service = ScannerManagerService(max_clients=10)
        service.initialized = True

        await service.register_scanner(
            scanner_id="scanner-t1",
            name="Tenant 1 Scanner",
            version="1.0",
            capabilities=["pdf"],
            ip_address="10.0.0.1",
            tenant_id="tenant-1",
        )
        await service.register_scanner(
            scanner_id="scanner-t2",
            name="Tenant 2 Scanner",
            version="1.0",
            capabilities=["pdf"],
            ip_address="10.0.0.2",
            tenant_id="tenant-2",
        )

        all_scanners = await service.get_connected_scanners()
        t1_scanners = [s for s in all_scanners if s["tenant_id"] == "tenant-1"]
        t2_scanners = [s for s in all_scanners if s["tenant_id"] == "tenant-2"]

        assert len(t1_scanners) == 1
        assert len(t2_scanners) == 1
        assert t1_scanners[0]["scanner_id"] == "scanner-t1"
        assert t2_scanners[0]["scanner_id"] == "scanner-t2"
