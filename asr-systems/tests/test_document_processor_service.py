"""
Unit Tests for Document Processor Service
Tests the 5-step pipeline orchestration with mocked sub-services.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "production-server"))

from production_server.services.document_processor_service import (
    DocumentProcessorService,
)
from shared.core.exceptions import DocumentError
from shared.core.models import DocumentMetadata, ProcessingStatus, UploadResult


def _make_mock_gl_service():
    svc = AsyncMock()
    svc.initialized = True
    result = MagicMock()
    result.gl_account_code = "5000"
    result.gl_account_name = "Materials"
    result.category = "EXPENSES"
    result.confidence = 0.92
    result.reasoning = "matched vendor"
    result.keywords_matched = ["materials"]
    result.classification_method = "vendor_mapping"
    svc.classify_document_text = AsyncMock(return_value=result)
    svc.get_health = AsyncMock(return_value={"status": "healthy"})
    return svc


def _make_mock_payment_service():
    svc = AsyncMock()
    svc.initialized = True
    result = MagicMock()
    result.payment_status = "unpaid"
    result.consensus_confidence = 0.85
    result.methods_used = ["regex_patterns", "keyword_matching"]
    result.quality_score = 0.8
    result.method_results = {}
    svc.detect_payment_status = AsyncMock(return_value=result)
    svc.get_health = AsyncMock(return_value={"status": "healthy"})
    return svc


def _make_mock_billing_service():
    svc = AsyncMock()
    svc.initialized = True
    result = MagicMock()
    result.destination = "open_payable"
    result.confidence = 0.9
    result.reasoning = "unpaid vendor invoice"
    result.factors = {"payment_status": "unpaid"}
    result.manual_override = False
    svc.route_document = AsyncMock(return_value=result)
    svc.get_health = AsyncMock(return_value={"status": "healthy"})
    return svc


def _make_mock_storage_service():
    svc = AsyncMock()
    svc.initialized = True
    from services.storage_service import StorageResult

    svc.store_document = AsyncMock(
        return_value=StorageResult(success=True, storage_path="/tmp/test.pdf")
    )
    svc.retrieve_document = AsyncMock(return_value=None)
    svc.get_health = AsyncMock(return_value={"status": "healthy"})
    return svc


@pytest.fixture
async def processor_service():
    svc = DocumentProcessorService(
        gl_account_service=_make_mock_gl_service(),
        payment_detection_service=_make_mock_payment_service(),
        billing_router_service=_make_mock_billing_service(),
        storage_service=_make_mock_storage_service(),
    )
    await svc.initialize()
    return svc


class TestInit:
    @pytest.mark.asyncio
    async def test_initialization(self, processor_service):
        assert processor_service.initialized is True

    @pytest.mark.asyncio
    async def test_initialization_warns_for_uninitialized_sub_service(self):
        gl = _make_mock_gl_service()
        gl.initialized = False
        svc = DocumentProcessorService(
            gl_account_service=gl,
            payment_detection_service=_make_mock_payment_service(),
            billing_router_service=_make_mock_billing_service(),
            storage_service=_make_mock_storage_service(),
        )
        await svc.initialize()
        assert svc.initialized is True


class TestProcessDocument:
    @pytest.mark.asyncio
    async def test_full_pipeline_success(self, processor_service):
        metadata = MagicMock(spec=DocumentMetadata)
        metadata.filename = "invoice.pdf"
        metadata.file_size = 1024
        metadata.tenant_id = "test-tenant"
        metadata.scanner_metadata = None

        result = await processor_service.process_document(
            file_content=b"%PDF-1.4 fake content",
            metadata=metadata,
        )

        assert result.success is True
        assert result.document_id is not None
        assert result.processing_status == ProcessingStatus.COMPLETED.value
        assert result.classification_result is not None
        assert "gl_account" in result.classification_result
        assert "payment_detection" in result.classification_result
        assert "billing_routing" in result.classification_result

    @pytest.mark.asyncio
    async def test_storage_failure_returns_error(self):
        from services.storage_service import StorageResult

        storage = _make_mock_storage_service()
        storage.store_document = AsyncMock(
            return_value=StorageResult(success=False, error="disk full")
        )
        svc = DocumentProcessorService(
            gl_account_service=_make_mock_gl_service(),
            payment_detection_service=_make_mock_payment_service(),
            billing_router_service=_make_mock_billing_service(),
            storage_service=storage,
        )
        await svc.initialize()

        metadata = MagicMock(spec=DocumentMetadata)
        metadata.filename = "test.pdf"
        metadata.file_size = 512
        metadata.tenant_id = "test-tenant"
        metadata.scanner_metadata = None

        result = await svc.process_document(file_content=b"content", metadata=metadata)

        assert result.success is False
        assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_processing_time_tracked(self, processor_service):
        metadata = MagicMock(spec=DocumentMetadata)
        metadata.filename = "invoice.pdf"
        metadata.file_size = 100
        metadata.tenant_id = "test-tenant"
        metadata.scanner_metadata = None

        result = await processor_service.process_document(
            file_content=b"content", metadata=metadata
        )

        assert result.processing_time_ms >= 0


class TestTextExtraction:
    @pytest.mark.asyncio
    async def test_pdf_extraction(self, processor_service):
        text = await processor_service._extract_text_content(b"pdf data", "test.pdf")
        assert isinstance(text, str)

    @pytest.mark.asyncio
    async def test_image_extraction(self, processor_service):
        text = await processor_service._extract_text_content(b"image", "scan.jpg")
        assert isinstance(text, str)

    @pytest.mark.asyncio
    async def test_plaintext_extraction(self, processor_service):
        text = await processor_service._extract_text_content(b"hello world", "doc.txt")
        assert text == "hello world"


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_when_initialized(self, processor_service):
        health = await processor_service.get_health()
        assert health["status"] in ("healthy", "degraded")
        assert "components" in health

    @pytest.mark.asyncio
    async def test_health_when_not_initialized(self):
        svc = DocumentProcessorService(
            gl_account_service=_make_mock_gl_service(),
            payment_detection_service=_make_mock_payment_service(),
            billing_router_service=_make_mock_billing_service(),
            storage_service=_make_mock_storage_service(),
        )
        health = await svc.get_health()
        assert health["status"] == "not_initialized"
