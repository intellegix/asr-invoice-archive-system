"""
Unit Tests for Service Error Scenarios
Tests edge cases and error handling across GL Account, Payment Detection,
Billing Router, Document Processor, and Storage services.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "production_server"))

from shared.core.exceptions import (
    ClassificationError,
    PaymentDetectionError,
    RoutingError,
    StorageError,
)
from shared.core.models import (
    BillingDestination,
    PaymentConsensusResult,
    PaymentDetectionMethod,
    PaymentStatus,
)

from services.billing_router_service import BillingRouterService, DocumentContext
from services.document_processor_service import DocumentProcessorService
from services.gl_account_service import GLAccountService
from services.payment_detection_service import PaymentDetectionService
from services.storage_service import ProductionStorageService


class _FakeMetadata:
    """Lightweight metadata stub matching the attributes storage_service accesses.

    The Pydantic DocumentMetadata model uses ``mime_type`` but storage_service
    reads ``content_type`` via getattr.  This stub exposes both so that
    store/retrieve round-trips work.
    """

    def __init__(self, tenant_id="test", filename="test.pdf"):
        self.filename = filename
        self.file_size = 100
        self.mime_type = "application/pdf"
        self.content_type = "application/pdf"
        self.tenant_id = tenant_id
        self.upload_source = "test"
        self.scanner_id = None
        self.scanner_metadata = {}


ALL_DESTINATIONS = [
    "open_payable",
    "closed_payable",
    "open_receivable",
    "closed_receivable",
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def gl_service():
    service = GLAccountService()
    await service.initialize()
    return service


@pytest.fixture
async def payment_service():
    """Payment detection with only non-Claude methods (no API key needed)."""
    methods = ["regex_patterns", "keyword_matching", "amount_analysis"]
    config = {"api_key": None, "model": "test", "temperature": 0.1, "enabled": False}
    service = PaymentDetectionService(config, methods)
    await service.initialize()
    return service


@pytest.fixture
async def router():
    service = BillingRouterService(ALL_DESTINATIONS, confidence_threshold=0.75)
    await service.initialize()
    return service


@pytest.fixture
def storage_service(tmp_path):
    config = {"backend": "local", "local_path": str(tmp_path / "storage")}
    return ProductionStorageService(config)


# ---------------------------------------------------------------------------
# GL Account Service — error / edge cases
# ---------------------------------------------------------------------------


class TestGLAccountErrors:
    @pytest.mark.asyncio
    async def test_empty_text_returns_default(self, gl_service):
        """Empty document text should return default GL account (miscellaneous)."""
        result = await gl_service.classify_document_text("")
        assert result.gl_account_code == "7700"
        assert result.confidence <= 0.4

    @pytest.mark.asyncio
    async def test_no_keyword_match_returns_default(self, gl_service):
        """Text with no matching keywords should fall back to default."""
        result = await gl_service.classify_document_text("xyzzyx nonsensical gibberish")
        assert result.gl_account_code is not None
        # Confidence should be low for a no-match
        assert result.confidence <= 0.5

    @pytest.mark.asyncio
    async def test_none_text_raises_error(self, gl_service):
        """Passing None as document text should raise an error."""
        with pytest.raises(Exception):
            await gl_service.classify_document_text(None)

    @pytest.mark.asyncio
    async def test_uninitialized_service_raises_error(self):
        """Using service before initialize should raise ClassificationError."""
        service = GLAccountService()
        with pytest.raises(ClassificationError):
            await service.classify_document_text("invoice for lumber")

    @pytest.mark.asyncio
    async def test_get_all_accounts_before_init_raises(self):
        """get_all_accounts should raise when not initialized."""
        service = GLAccountService()
        with pytest.raises(ClassificationError):
            service.get_all_accounts()


# ---------------------------------------------------------------------------
# Payment Detection Service — error / edge cases
# ---------------------------------------------------------------------------


class TestPaymentDetectionErrors:
    @pytest.mark.asyncio
    async def test_empty_text_returns_unknown(self, payment_service):
        """Empty document text should return UNKNOWN status."""
        result = await payment_service.detect_payment_status("")
        assert result.payment_status == PaymentStatus.UNKNOWN

    @pytest.mark.asyncio
    async def test_random_text_low_confidence(self, payment_service):
        """Random garbage text should yield low confidence."""
        result = await payment_service.detect_payment_status(
            "zyxwvu nopaymentinfo here 12345"
        )
        assert result.confidence < 0.7

    @pytest.mark.asyncio
    async def test_no_methods_returns_unknown(self):
        """If all methods produce no results, consensus should be UNKNOWN."""
        methods = ["regex_patterns", "keyword_matching", "amount_analysis"]
        config = {"api_key": None, "model": "t", "temperature": 0.1, "enabled": False}
        service = PaymentDetectionService(config, methods)
        await service.initialize()

        result = await service.detect_payment_status("xyzzy nothing here")
        assert result.payment_status == PaymentStatus.UNKNOWN

    @pytest.mark.asyncio
    async def test_uninitialized_raises_error(self):
        """Using payment detection before init should raise."""
        methods = ["regex_patterns", "keyword_matching", "amount_analysis"]
        config = {"api_key": None, "model": "t", "temperature": 0.1, "enabled": False}
        service = PaymentDetectionService(config, methods)
        with pytest.raises(PaymentDetectionError):
            await service.detect_payment_status("test text")

    @pytest.mark.asyncio
    async def test_conflicting_signals_produces_result(self, payment_service):
        """Text with both paid and unpaid signals should still produce a result."""
        mixed_text = (
            "PAID in full. Check #12345. "
            "Amount due: $500.00. Please remit. Balance owed: $500."
        )
        result = await payment_service.detect_payment_status(mixed_text)
        # Should still produce *some* consensus
        assert result.payment_status in [
            PaymentStatus.PAID,
            PaymentStatus.UNPAID,
            PaymentStatus.UNKNOWN,
        ]
        assert result.confidence > 0.0


# ---------------------------------------------------------------------------
# Billing Router Service — error / edge cases
# ---------------------------------------------------------------------------


class TestBillingRouterErrors:
    @pytest.mark.asyncio
    async def test_missing_payment_consensus(self, router):
        """Document with no payment consensus should still route (fallback)."""
        ctx = DocumentContext(
            document_id="test-001",
            document_type="vendor_invoice",
            payment_consensus=None,
            gl_account="5000",
            tenant_id="test",
        )
        decision = await router.route_document(ctx)
        assert decision.destination in [
            BillingDestination.OPEN_PAYABLE,
            BillingDestination.CLOSED_PAYABLE,
            BillingDestination.OPEN_RECEIVABLE,
            BillingDestination.CLOSED_RECEIVABLE,
        ]

    @pytest.mark.asyncio
    async def test_missing_gl_account(self, router, make_consensus):
        """Document with no GL account should still route."""
        consensus = make_consensus(status=PaymentStatus.UNPAID)
        ctx = DocumentContext(
            document_id="test-002",
            document_type="vendor_invoice",
            payment_consensus=consensus,
            gl_account=None,
            tenant_id="test",
        )
        decision = await router.route_document(ctx)
        assert decision.destination is not None

    @pytest.mark.asyncio
    async def test_empty_context_routes_with_fallback(self, router):
        """Completely empty context should still produce a valid decision."""
        ctx = DocumentContext(
            document_id="test-003",
            document_type=None,
            payment_consensus=None,
            gl_account=None,
            amount=None,
            vendor_name=None,
            tenant_id="test",
        )
        decision = await router.route_document(ctx)
        assert decision.destination is not None
        assert decision.confidence >= 0.0

    @pytest.mark.asyncio
    async def test_uninitialized_router_raises(self):
        """Routing before initialization should raise RoutingError."""
        service = BillingRouterService(ALL_DESTINATIONS, confidence_threshold=0.75)
        ctx = DocumentContext(document_id="t", tenant_id="t")
        with pytest.raises(RoutingError):
            await service.route_document(ctx)


# ---------------------------------------------------------------------------
# Storage Service — error / edge cases
# ---------------------------------------------------------------------------


class TestStorageErrors:
    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_document(self, storage_service):
        """Retrieving a non-existent document should return None."""
        await storage_service.initialize()
        result = await storage_service.retrieve_document("does-not-exist-12345")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(self, storage_service):
        """Deleting a non-existent document should return False."""
        await storage_service.initialize()
        result = await storage_service.delete_document("does-not-exist-12345")
        assert result is False

    @pytest.mark.asyncio
    async def test_store_before_init_raises(self, storage_service):
        """Storing a document before initialization should raise StorageError."""
        metadata = _FakeMetadata()
        result = await storage_service.store_document("doc-1", b"content", metadata)
        # store_document catches the exception and returns success=False
        assert result.success is False

    @pytest.mark.asyncio
    async def test_unsupported_backend_raises(self):
        """An unsupported storage backend should cause store to fail."""
        config = {"backend": "nonexistent_backend", "local_path": "/tmp/test"}
        service = ProductionStorageService(config)
        service.initialized = True  # Force past init check
        metadata = _FakeMetadata()
        result = await service.store_document("doc-1", b"content", metadata)
        assert result.success is False
        assert "unsupported" in result.error.lower()


# ---------------------------------------------------------------------------
# Document Processor Service — error / edge cases
# ---------------------------------------------------------------------------


class TestDocumentProcessorErrors:
    @pytest.mark.asyncio
    async def test_storage_failure_returns_error_result(self):
        """If storage fails, the processor should return an error UploadResult."""
        mock_gl = MagicMock(spec=GLAccountService)
        mock_gl.initialized = True
        mock_payment = MagicMock(spec=PaymentDetectionService)
        mock_payment.initialized = True
        mock_router = MagicMock(spec=BillingRouterService)
        mock_router.initialized = True
        mock_storage = AsyncMock(spec=ProductionStorageService)
        mock_storage.initialized = True

        from services.storage_service import StorageResult

        mock_storage.store_document = AsyncMock(
            return_value=StorageResult(success=False, error="Disk full")
        )

        processor = DocumentProcessorService(
            gl_account_service=mock_gl,
            payment_detection_service=mock_payment,
            billing_router_service=mock_router,
            storage_service=mock_storage,
        )
        await processor.initialize()

        metadata = _FakeMetadata()
        result = await processor.process_document(
            file_content=b"test content", metadata=metadata
        )
        assert result.success is False
        assert "storage" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_uninitialized_processor_health(self):
        """Health check on uninitialized processor should report not_initialized."""
        mock_gl = MagicMock(spec=GLAccountService)
        mock_payment = MagicMock(spec=PaymentDetectionService)
        mock_router = MagicMock(spec=BillingRouterService)
        mock_storage = MagicMock(spec=ProductionStorageService)

        processor = DocumentProcessorService(
            gl_account_service=mock_gl,
            payment_detection_service=mock_payment,
            billing_router_service=mock_router,
            storage_service=mock_storage,
        )
        health = await processor.get_health()
        assert health["status"] == "not_initialized"

    @pytest.mark.asyncio
    async def test_text_extraction_handles_unknown_extension(self):
        """Unknown file extensions should attempt UTF-8 decode."""
        mock_gl = MagicMock(spec=GLAccountService)
        mock_gl.initialized = True
        mock_payment = MagicMock(spec=PaymentDetectionService)
        mock_payment.initialized = True
        mock_router = MagicMock(spec=BillingRouterService)
        mock_router.initialized = True
        mock_storage = MagicMock(spec=ProductionStorageService)
        mock_storage.initialized = True

        processor = DocumentProcessorService(
            gl_account_service=mock_gl,
            payment_detection_service=mock_payment,
            billing_router_service=mock_router,
            storage_service=mock_storage,
        )
        await processor.initialize()

        text = await processor._extract_text_content(b"hello world", "file.txt")
        assert text == "hello world"

    @pytest.mark.asyncio
    async def test_binary_file_extraction_returns_empty(self):
        """Binary content with no valid extension should return empty string."""
        mock_gl = MagicMock(spec=GLAccountService)
        mock_gl.initialized = True
        mock_payment = MagicMock(spec=PaymentDetectionService)
        mock_payment.initialized = True
        mock_router = MagicMock(spec=BillingRouterService)
        mock_router.initialized = True
        mock_storage = MagicMock(spec=ProductionStorageService)
        mock_storage.initialized = True

        processor = DocumentProcessorService(
            gl_account_service=mock_gl,
            payment_detection_service=mock_payment,
            billing_router_service=mock_router,
            storage_service=mock_storage,
        )
        await processor.initialize()

        # Invalid UTF-8 bytes with an unknown extension
        text = await processor._extract_text_content(
            b"\x80\x81\x82\xff\xfe", "file.xyz"
        )
        assert text == ""
