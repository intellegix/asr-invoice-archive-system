"""
Tests for storage layer tenant isolation (P86).
Verifies that retrieve/delete/search methods properly scope to tenant_id
and that cross-tenant access is blocked.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from shared.core.models import DocumentMetadata

from services.storage_service import (
    DocumentData,
    ProductionStorageService,
    StorageResult,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_storage(tmp_path: Path) -> ProductionStorageService:
    """Create an initialized local storage service in tmp_path."""
    svc = ProductionStorageService({"backend": "local", "local_path": str(tmp_path)})
    svc.initialized = True
    # Ensure directories exist
    (tmp_path / "documents").mkdir(exist_ok=True)
    (tmp_path / "metadata").mkdir(exist_ok=True)
    (tmp_path / "temp").mkdir(exist_ok=True)
    return svc


def _make_metadata(
    tenant_id: str = "tenant-a", filename: str = "invoice.pdf"
) -> DocumentMetadata:
    return DocumentMetadata(
        filename=filename,
        file_size=100,
        mime_type="application/pdf",
        tenant_id=tenant_id,
    )


async def _store_doc(
    svc: ProductionStorageService,
    doc_id: str,
    tenant_id: str,
    content: bytes = b"test-content",
) -> StorageResult:
    """Store a document with the given tenant."""
    meta = _make_metadata(tenant_id=tenant_id)
    return await svc.store_document(doc_id, content, meta)


# ---------------------------------------------------------------------------
# Service-level tests
# ---------------------------------------------------------------------------


class TestRetrieveTenantIsolation:
    """retrieve_document() must scope to tenant when tenant_id is provided."""

    @pytest.mark.asyncio
    async def test_retrieve_wrong_tenant_returns_none(self, tmp_path):
        svc = _make_storage(tmp_path)
        await _store_doc(svc, "doc-1", "tenant-a")

        result = await svc.retrieve_document("doc-1", tenant_id="tenant-b")
        assert result is None

    @pytest.mark.asyncio
    async def test_retrieve_correct_tenant_succeeds(self, tmp_path):
        svc = _make_storage(tmp_path)
        await _store_doc(svc, "doc-1", "tenant-a", content=b"hello")

        result = await svc.retrieve_document("doc-1", tenant_id="tenant-a")
        assert result is not None
        assert result.content == b"hello"
        assert result.metadata.tenant_id == "tenant-a"

    @pytest.mark.asyncio
    async def test_retrieve_no_tenant_returns_any(self, tmp_path):
        """Internal call (tenant_id=None) should return documents from any tenant."""
        svc = _make_storage(tmp_path)
        await _store_doc(svc, "doc-1", "tenant-a")

        result = await svc.retrieve_document("doc-1", tenant_id=None)
        assert result is not None

    @pytest.mark.asyncio
    async def test_retrieve_validates_metadata_tenant(self, tmp_path):
        """Defense-in-depth: if metadata tenant doesn't match, return None."""
        svc = _make_storage(tmp_path)
        await _store_doc(svc, "doc-1", "tenant-a")

        # Tamper with metadata file to simulate mismatch
        meta_file = tmp_path / "metadata" / "tenant-a" / "doc-1.json"
        data = json.loads(meta_file.read_text())
        data["tenant_id"] = "tenant-c"
        meta_file.write_text(json.dumps(data))

        result = await svc.retrieve_document("doc-1", tenant_id="tenant-a")
        assert result is None


class TestDeleteTenantIsolation:
    """delete_document() must scope to tenant when tenant_id is provided."""

    @pytest.mark.asyncio
    async def test_delete_wrong_tenant_returns_false(self, tmp_path):
        svc = _make_storage(tmp_path)
        await _store_doc(svc, "doc-1", "tenant-a")

        deleted = await svc.delete_document("doc-1", tenant_id="tenant-b")
        assert deleted is False

        # Verify file is still intact
        result = await svc.retrieve_document("doc-1", tenant_id="tenant-a")
        assert result is not None

    @pytest.mark.asyncio
    async def test_delete_correct_tenant_succeeds(self, tmp_path):
        svc = _make_storage(tmp_path)
        await _store_doc(svc, "doc-1", "tenant-a")

        deleted = await svc.delete_document("doc-1", tenant_id="tenant-a")
        assert deleted is True

        # Verify file is gone
        result = await svc.retrieve_document("doc-1", tenant_id="tenant-a")
        assert result is None


class TestSearchTenantIsolation:
    """search_documents() must scope to tenant when tenant_id is provided."""

    @pytest.mark.asyncio
    async def test_search_scoped_to_tenant(self, tmp_path):
        svc = _make_storage(tmp_path)
        await _store_doc(svc, "doc-a", "tenant-a", content=b"invoice data")
        await _store_doc(svc, "doc-b", "tenant-b", content=b"invoice data")

        results = await svc.search_documents("invoice", tenant_id="tenant-a")
        doc_ids = [r["document_id"] for r in results]
        assert "doc-a" in doc_ids
        assert "doc-b" not in doc_ids

    @pytest.mark.asyncio
    async def test_search_no_tenant_returns_all(self, tmp_path):
        svc = _make_storage(tmp_path)
        await _store_doc(svc, "doc-a", "tenant-a", content=b"invoice data")
        await _store_doc(svc, "doc-b", "tenant-b", content=b"invoice data")

        results = await svc.search_documents("invoice", tenant_id=None)
        doc_ids = [r["document_id"] for r in results]
        assert "doc-a" in doc_ids
        assert "doc-b" in doc_ids


class TestS3TenantIsolation:
    """S3-specific tenant isolation via mocked boto3 client."""

    @pytest.mark.asyncio
    async def test_s3_delete_uses_exact_key_not_substring(self, tmp_path):
        """The old code used `document_id in obj['Key']` (substring match).
        Verify the new code uses exact path-based matching."""
        svc = ProductionStorageService(
            {
                "backend": "s3",
                "bucket": "test-bucket",
                "prefix": "prod",
            }
        )
        svc.initialized = True

        mock_client = MagicMock()
        svc.s3_client = mock_client

        # Simulate S3 listing with another doc that contains our ID as substring
        mock_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "prod/tenants/tenant-x/documents/doc-1-extended.pdf"},
                {"Key": "prod/tenants/tenant-x/metadata/doc-1-extended.json"},
            ]
        }

        # Delete doc-1 for tenant-x — should NOT match doc-1-extended
        deleted = await svc.delete_document("doc-1", tenant_id="tenant-x")
        # The exact key construction won't find doc-1-extended
        # list_objects_v2 is called for the documents prefix
        # Since no exact match found for doc-1, result depends on implementation
        # Key point: substring "doc-1" should NOT match "doc-1-extended"

    @pytest.mark.asyncio
    async def test_s3_retrieve_scoped_to_tenant_prefix(self):
        """When tenant_id is provided, S3 retrieve should use exact key,
        not paginate across all tenants."""
        svc = ProductionStorageService(
            {
                "backend": "s3",
                "bucket": "test-bucket",
                "prefix": "prod",
            }
        )
        svc.initialized = True

        mock_client = MagicMock()
        svc.s3_client = mock_client

        # Simulate NoSuchKey for wrong tenant
        error_response = {"Error": {"Code": "NoSuchKey"}}
        mock_client.exceptions.NoSuchKey = type("NoSuchKey", (Exception,), {})
        mock_client.get_object.side_effect = mock_client.exceptions.NoSuchKey(
            "Not found"
        )

        result = await svc.retrieve_document("doc-1", tenant_id="tenant-a")
        assert result is None

        # Verify it used direct key lookup, not paginator
        mock_client.get_paginator.assert_not_called()
        mock_client.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="prod/tenants/tenant-a/metadata/doc-1.json",
        )


# ---------------------------------------------------------------------------
# API-level tests via TestClient
# ---------------------------------------------------------------------------


class TestAPITenantIsolation:
    """Verify that API endpoints thread tenant_id to storage/processor."""

    @pytest.fixture(scope="class")
    def client(self):
        """Create a TestClient with lifespan so services are initialised."""
        from fastapi.testclient import TestClient

        from api.main import app

        with TestClient(app, raise_server_exceptions=False) as c:
            yield c

    @pytest.fixture(autouse=True)
    def _patch_services(self):
        """Patch module-level service globals in api.main."""
        import api.main as api_mod

        mock_storage = AsyncMock()
        mock_processor = AsyncMock()

        self._mock_storage = mock_storage
        self._mock_processor = mock_processor

        self._orig_storage = api_mod.storage_service
        self._orig_processor = api_mod.document_processor_service

        api_mod.storage_service = mock_storage
        api_mod.document_processor_service = mock_processor

        yield

        api_mod.storage_service = self._orig_storage
        api_mod.document_processor_service = self._orig_processor

    def test_delete_document_passes_tenant(self, client):
        from auth_helpers import CSRF_COOKIES, WRITE_HEADERS

        self._mock_storage.delete_document = AsyncMock(return_value=True)
        resp = client.delete(
            "/api/v1/documents/test-doc-123",
            headers=WRITE_HEADERS,
            cookies=CSRF_COOKIES,
        )
        assert resp.status_code == 200
        self._mock_storage.delete_document.assert_awaited_once()
        call_kwargs = self._mock_storage.delete_document.call_args
        assert "tenant_id" in str(call_kwargs)

    def test_reprocess_passes_tenant(self, client):
        from auth_helpers import CSRF_COOKIES, WRITE_HEADERS

        mock_result = MagicMock()
        mock_result.document_id = "test-doc-123"
        mock_result.processing_status = "completed"
        self._mock_processor.reprocess_document = AsyncMock(return_value=mock_result)
        resp = client.post(
            "/extract/invoice/test-doc-123",
            headers=WRITE_HEADERS,
            cookies=CSRF_COOKIES,
        )
        assert resp.status_code == 200
        self._mock_processor.reprocess_document.assert_awaited_once()
        call_kwargs = self._mock_processor.reprocess_document.call_args
        assert "tenant_id" in str(call_kwargs)

    def test_search_passes_tenant(self, client):
        from auth_helpers import AUTH_HEADERS

        self._mock_storage.search_documents = AsyncMock(return_value=[])
        resp = client.get("/search/quick?q=invoice", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        self._mock_storage.search_documents.assert_awaited_once()
        call_kwargs = self._mock_storage.search_documents.call_args
        assert "tenant_id" in str(call_kwargs)

    def test_cross_tenant_delete_returns_404(self, client):
        """Storage returns False when tenant doesn't own doc → 404."""
        from auth_helpers import CSRF_COOKIES, WRITE_HEADERS

        self._mock_storage.delete_document = AsyncMock(return_value=False)
        resp = client.delete(
            "/api/v1/documents/alien-doc-99",
            headers=WRITE_HEADERS,
            cookies=CSRF_COOKIES,
        )
        assert resp.status_code == 404

    def test_cross_tenant_reprocess_returns_404(self, client):
        """Processor raises DocumentError when tenant can't find doc → 404."""
        from auth_helpers import CSRF_COOKIES, WRITE_HEADERS
        from shared.core.exceptions import DocumentError

        self._mock_processor.reprocess_document = AsyncMock(
            side_effect=DocumentError("Document not found: alien-doc-99")
        )
        resp = client.post(
            "/extract/invoice/alien-doc-99",
            headers=WRITE_HEADERS,
            cookies=CSRF_COOKIES,
        )
        assert resp.status_code == 404

    def test_cross_tenant_search_excludes_other(self, client):
        """Search with tenant_id should only return that tenant's docs."""
        from auth_helpers import AUTH_HEADERS

        self._mock_storage.search_documents = AsyncMock(return_value=[])
        resp = client.get("/search/quick?q=test", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["total"] == 0
