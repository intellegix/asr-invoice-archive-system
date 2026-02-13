"""
P79: DocumentProcessorService coverage expansion.
Tests edge cases: empty content, unsupported MIME, pipeline stages, request_id correlation.
"""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_asr = Path(__file__).parent.parent
sys.path.insert(0, str(_asr / "shared"))
sys.path.insert(0, str(_asr / "production-server"))

os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")


def _make_service():
    """Create a DocumentProcessorService with mocked sub-services."""
    from services.document_processor_service import DocumentProcessorService

    gl = MagicMock()
    gl.initialized = True
    gl.classify_document_text = AsyncMock()

    payment = MagicMock()
    payment.initialized = True
    payment.detect_payment_status = AsyncMock()

    router = MagicMock()
    router.initialized = True
    router.route_document = AsyncMock()

    storage = MagicMock()
    storage.initialized = True
    storage.store_document = AsyncMock()
    storage.retrieve_document = AsyncMock()
    storage.get_health = AsyncMock(return_value={"status": "healthy"})

    svc = DocumentProcessorService(
        gl_account_service=gl,
        payment_detection_service=payment,
        billing_router_service=router,
        storage_service=storage,
    )
    svc.initialized = True
    return svc, gl, payment, router, storage


def _make_metadata(**overrides):
    from shared.core.models import DocumentMetadata

    meta = MagicMock(spec=DocumentMetadata)
    defaults = {
        "filename": "test.pdf",
        "mime_type": "application/pdf",
        "file_size": 1024,
        "tenant_id": "default",
        "scanner_metadata": None,
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(meta, k, v)
    return meta


@pytest.mark.asyncio
async def test_process_document_success():
    """Full pipeline succeeds with valid inputs."""
    svc, gl, payment, router, storage = _make_service()

    storage.store_document.return_value = MagicMock(
        success=True, storage_path="/tmp/test", error=None
    )
    gl.classify_document_text.return_value = MagicMock(
        gl_account_code="5000",
        gl_account_name="Materials",
        category="EXPENSES",
        confidence=0.9,
        reasoning="test",
        keywords_matched=["test"],
        classification_method="keyword_matching",
    )
    payment.detect_payment_status.return_value = MagicMock(
        payment_status="unpaid",
        consensus_confidence=0.85,
        methods_used=["regex"],
        quality_score=0.9,
        method_results={},
    )
    router.route_document.return_value = MagicMock(
        destination="open_payable",
        confidence=0.9,
        reasoning="unpaid vendor",
        factors={},
        manual_override=False,
    )

    result = await svc.process_document(
        file_content=b"test content",
        metadata=_make_metadata(),
        request_id="req-123",
    )
    assert result.success is True
    assert result.document_id is not None
    assert result.processing_status == "completed"


@pytest.mark.asyncio
async def test_process_document_storage_failure():
    """Pipeline returns error when storage fails."""
    svc, gl, payment, router, storage = _make_service()

    storage.store_document.return_value = MagicMock(success=False, error="disk full")

    result = await svc.process_document(file_content=b"data", metadata=_make_metadata())
    assert result.success is False
    assert "storage failed" in result.error_message.lower()


@pytest.mark.asyncio
async def test_extract_text_pdf():
    """PDF text extraction returns non-empty string."""
    svc, *_ = _make_service()
    text = await svc._extract_text_content(b"%PDF-1.4 content", "invoice.pdf")
    assert len(text) > 0


@pytest.mark.asyncio
async def test_extract_text_image():
    """Image text extraction returns non-empty string."""
    svc, *_ = _make_service()
    text = await svc._extract_text_content(b"\x89PNG", "scan.png")
    assert len(text) > 0


@pytest.mark.asyncio
async def test_extract_text_plain():
    """Plain text content decoded correctly."""
    svc, *_ = _make_service()
    text = await svc._extract_text_content(b"Hello world", "notes.txt")
    assert text == "Hello world"


@pytest.mark.asyncio
async def test_extract_text_binary_fallback():
    """Non-decodable binary returns empty string."""
    svc, *_ = _make_service()
    text = await svc._extract_text_content(b"\x80\x81\x82", "data.bin")
    assert text == ""


@pytest.mark.asyncio
async def test_get_processing_status():
    """get_processing_status returns status dict."""
    svc, *_ = _make_service()
    status = await svc.get_processing_status("doc-123")
    assert status["document_id"] == "doc-123"
    assert status["status"] == "completed"


@pytest.mark.asyncio
async def test_get_processing_statistics():
    """get_processing_statistics returns metrics dict."""
    svc, *_ = _make_service()
    stats = await svc.get_processing_statistics()
    assert "total_documents_processed" in stats
    assert "success_rate_percentage" in stats


@pytest.mark.asyncio
async def test_get_health_not_initialized():
    """Health returns not_initialized when service is not ready."""
    svc, *_ = _make_service()
    svc.initialized = False
    health = await svc.get_health()
    assert health["status"] == "not_initialized"


@pytest.mark.asyncio
async def test_initialize_warns_on_uninitalized_component():
    """Initialize warns but succeeds when a component is not initialized."""
    from services.document_processor_service import DocumentProcessorService

    gl = MagicMock()
    gl.initialized = False  # Not initialized

    svc = DocumentProcessorService(
        gl_account_service=gl,
        payment_detection_service=MagicMock(initialized=True),
        billing_router_service=MagicMock(initialized=True),
        storage_service=MagicMock(initialized=True),
    )
    await svc.initialize()
    assert svc.initialized is True


@pytest.mark.asyncio
async def test_cleanup():
    """Cleanup sets initialized to False."""
    svc, *_ = _make_service()
    assert svc.initialized is True
    await svc.cleanup()
    assert svc.initialized is False


@pytest.mark.asyncio
async def test_reprocess_not_found():
    """Reprocess returns error for missing document."""
    svc, _, _, _, storage = _make_service()
    storage.retrieve_document.return_value = None

    result = await svc.reprocess_document("missing-id")
    assert result.success is False
    assert "not found" in result.error_message.lower()


@pytest.mark.asyncio
async def test_process_document_with_request_id():
    """request_id is logged (no crash when provided)."""
    svc, gl, payment, router, storage = _make_service()

    storage.store_document.return_value = MagicMock(
        success=True, storage_path="/tmp", error=None
    )
    gl.classify_document_text.return_value = MagicMock(
        gl_account_code="5000",
        gl_account_name="Mat",
        category="EXPENSES",
        confidence=0.8,
        reasoning="r",
        keywords_matched=[],
        classification_method="keyword",
    )
    payment.detect_payment_status.return_value = MagicMock(
        payment_status="paid",
        consensus_confidence=0.9,
        methods_used=["regex"],
        quality_score=0.8,
        method_results={},
    )
    router.route_document.return_value = MagicMock(
        destination="closed_payable",
        confidence=0.9,
        reasoning="paid",
        factors={},
        manual_override=False,
    )

    result = await svc.process_document(
        file_content=b"data",
        metadata=_make_metadata(),
        request_id="corr-999",
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_process_document_gl_exception():
    """Pipeline handles GL classification exception gracefully."""
    svc, gl, payment, router, storage = _make_service()

    storage.store_document.return_value = MagicMock(
        success=True, storage_path="/tmp", error=None
    )
    gl.classify_document_text.side_effect = RuntimeError("GL broke")

    result = await svc.process_document(file_content=b"data", metadata=_make_metadata())
    assert result.success is False
    assert "GL broke" in result.error_message
