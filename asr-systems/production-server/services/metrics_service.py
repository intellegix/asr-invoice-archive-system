"""
ASR Production Server - Business-Level Prometheus Metrics
Application-specific counters and histograms for document processing,
GL classification, payment detection, and vendor operations.
"""

try:
    from prometheus_client import REGISTRY, Counter, Histogram

    _HAS_PROM = True
except ImportError:
    _HAS_PROM = False


def _get_or_create(cls, name, doc, labels=None):
    """Return existing collector or create new one (avoids duplicate on dual-import)."""
    existing = REGISTRY._names_to_collectors.get(name) if _HAS_PROM else None
    if existing is not None:
        return existing
    return cls(name, doc, labels) if labels else cls(name, doc)


# ---- Document processing ----

if _HAS_PROM:
    asr_documents_processed_total = _get_or_create(
        Counter,
        "asr_documents_processed_total",
        "Total documents processed",
        ["tenant_id", "status"],
    )
    asr_document_processing_seconds = _get_or_create(
        Histogram,
        "asr_document_processing_seconds",
        "Document processing duration in seconds",
    )

    # ---- GL classification ----
    asr_gl_classifications_total = _get_or_create(
        Counter,
        "asr_gl_classifications_total",
        "Total GL classifications performed",
        ["method", "gl_code"],
    )

    # ---- Payment detection ----
    asr_payment_detections_total = _get_or_create(
        Counter,
        "asr_payment_detections_total",
        "Total payment detections performed",
        ["method", "status"],
    )

    # ---- Vendor operations ----
    asr_vendor_operations_total = _get_or_create(
        Counter,
        "asr_vendor_operations_total",
        "Total vendor CRUD operations",
        ["operation", "tenant_id"],
    )


def record_document_processed(tenant_id: str, status: str) -> None:
    if _HAS_PROM:
        asr_documents_processed_total.labels(tenant_id=tenant_id, status=status).inc()


def observe_document_processing_time(duration: float) -> None:
    if _HAS_PROM:
        asr_document_processing_seconds.observe(duration)


def record_gl_classification(method: str, gl_code: str) -> None:
    if _HAS_PROM:
        asr_gl_classifications_total.labels(method=method, gl_code=gl_code).inc()


def record_payment_detection(method: str, status: str) -> None:
    if _HAS_PROM:
        asr_payment_detections_total.labels(method=method, status=status).inc()


def record_vendor_operation(operation: str, tenant_id: str) -> None:
    if _HAS_PROM:
        asr_vendor_operations_total.labels(
            operation=operation, tenant_id=tenant_id
        ).inc()
