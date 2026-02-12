"""
Unit Tests for Production Storage Service
Tests local storage CRUD, tenant isolation, and metadata persistence.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "production-server"))

from production_server.services.storage_service import ProductionStorageService


class _FakeMetadata:
    """Lightweight metadata stub matching the attributes storage_service accesses."""

    def __init__(
        self,
        tenant_id: str = "test-tenant",
        filename: str = "invoice.pdf",
    ):
        self.filename = filename
        self.file_size = 1024
        self.mime_type = "application/pdf"
        self.content_type = "application/pdf"
        self.tenant_id = tenant_id
        self.upload_source = "test"
        self.scanner_id = None
        self.scanner_metadata = {}


@pytest.fixture
async def storage_service(tmp_path):
    config = {"backend": "local", "local_path": str(tmp_path / "storage")}
    svc = ProductionStorageService(config)
    await svc.initialize()
    return svc


def _make_metadata(tenant_id: str = "test-tenant", filename: str = "invoice.pdf"):
    """Create a lightweight metadata object for testing."""
    return _FakeMetadata(tenant_id=tenant_id, filename=filename)


class TestInit:
    @pytest.mark.asyncio
    async def test_initialization(self, storage_service):
        assert storage_service.initialized is True

    @pytest.mark.asyncio
    async def test_creates_directories(self, storage_service):
        base = storage_service.base_path
        assert (base / "documents").exists()
        assert (base / "metadata").exists()
        assert (base / "temp").exists()

    @pytest.mark.asyncio
    async def test_unsupported_backend_raises(self, tmp_path):
        config = {"backend": "unsupported", "local_path": str(tmp_path)}
        svc = ProductionStorageService(config)
        await svc.initialize()
        result = await svc.store_document("doc-1", b"content", _make_metadata())
        assert result.success is False


class TestStoreDocument:
    @pytest.mark.asyncio
    async def test_store_and_verify(self, storage_service):
        content = b"fake PDF content"
        metadata = _make_metadata()

        result = await storage_service.store_document("doc-001", content, metadata)

        assert result.success is True
        assert result.storage_path is not None
        assert Path(result.storage_path).exists()

    @pytest.mark.asyncio
    async def test_metadata_file_created(self, storage_service):
        content = b"data"
        metadata = _make_metadata()

        await storage_service.store_document("doc-002", content, metadata)

        metadata_files = list(
            storage_service.base_path.glob("metadata/**/doc-002.json")
        )
        assert len(metadata_files) == 1

        with metadata_files[0].open() as f:
            meta_dict = json.load(f)
        assert meta_dict["document_id"] == "doc-002"
        assert meta_dict["filename"] == "invoice.pdf"

    @pytest.mark.asyncio
    async def test_not_initialized_raises(self, tmp_path):
        config = {"backend": "local", "local_path": str(tmp_path)}
        svc = ProductionStorageService(config)
        result = await svc.store_document("doc-x", b"data", _make_metadata())
        assert result.success is False


class TestTenantIsolation:
    @pytest.mark.asyncio
    async def test_documents_separated_by_tenant(self, storage_service):
        meta_a = _make_metadata(tenant_id="tenant-a")
        meta_b = _make_metadata(tenant_id="tenant-b")

        await storage_service.store_document("doc-a", b"content-a", meta_a)
        await storage_service.store_document("doc-b", b"content-b", meta_b)

        docs_a = list(storage_service.base_path.glob("documents/tenant-a/*"))
        docs_b = list(storage_service.base_path.glob("documents/tenant-b/*"))
        assert len(docs_a) == 1
        assert len(docs_b) == 1


class TestDeleteDocument:
    @pytest.mark.asyncio
    async def test_delete_existing(self, storage_service):
        await storage_service.store_document("doc-del", b"content", _make_metadata())

        deleted = await storage_service.delete_document("doc-del")
        assert deleted is True

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, storage_service):
        deleted = await storage_service.delete_document("no-such-doc")
        assert deleted is False


class TestStatistics:
    @pytest.mark.asyncio
    async def test_local_stats(self, storage_service):
        await storage_service.store_document("doc-s1", b"hello", _make_metadata())
        stats = await storage_service.get_storage_statistics()
        assert stats["backend"] == "local"
        assert stats["total_documents"] >= 1


class TestHealth:
    @pytest.mark.asyncio
    async def test_healthy_when_initialized(self, storage_service):
        health = await storage_service.get_health()
        assert health["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_not_initialized(self, tmp_path):
        config = {"backend": "local", "local_path": str(tmp_path)}
        svc = ProductionStorageService(config)
        health = await svc.get_health()
        assert health["status"] == "not_initialized"


class TestPathTraversal:
    @pytest.mark.asyncio
    async def test_dotdot_rejected(self, storage_service):
        """Paths containing '..' must be rejected."""
        from shared.core.exceptions import StorageError

        with pytest.raises(StorageError, match="traversal"):
            storage_service._validate_path("../etc/passwd")

    @pytest.mark.asyncio
    async def test_absolute_path_rejected(self, storage_service):
        """Absolute paths must be rejected."""
        from shared.core.exceptions import StorageError

        with pytest.raises(StorageError):
            storage_service._validate_path("/etc/passwd")

    @pytest.mark.asyncio
    async def test_valid_relative_path_allowed(self, storage_service):
        """Normal relative paths within base_path should succeed."""
        # Should not raise
        result = storage_service._validate_path("documents/test-tenant")
        assert result is not None

    @pytest.mark.asyncio
    async def test_store_with_traversal_tenant_fails(self, storage_service):
        """Storing with a tenant_id containing '..' should fail."""
        meta = _make_metadata(tenant_id="../../../etc")
        result = await storage_service.store_document("doc-evil", b"data", meta)
        assert result.success is False
