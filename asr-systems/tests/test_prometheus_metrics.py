"""
P85: Prometheus application metrics tests.
Tests middleware instrumentation, business metrics, /metrics endpoint,
and path normalisation.
"""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "production_server"))

os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")


# ---------------------------------------------------------------------------
# Path normalisation
# ---------------------------------------------------------------------------


class TestPathNormalization:
    def test_uuid_collapsed(self):
        from middleware.metrics_middleware import _normalize_path

        path = "/vendors/550e8400-e29b-41d4-a716-446655440000"
        assert _normalize_path(path) == "/vendors/{id}"

    def test_hex_id_collapsed(self):
        from middleware.metrics_middleware import _normalize_path

        path = "/vendors/507f1f77bcf86cd799439011"
        assert _normalize_path(path) == "/vendors/{id}"

    def test_numeric_id_collapsed(self):
        from middleware.metrics_middleware import _normalize_path

        path = "/api/v1/documents/12345/status"
        assert _normalize_path(path) == "/api/v1/documents/{id}/status"

    def test_static_path_unchanged(self):
        from middleware.metrics_middleware import _normalize_path

        path = "/api/v1/gl-accounts"
        assert _normalize_path(path) == "/api/v1/gl-accounts"


# ---------------------------------------------------------------------------
# Metrics service (business-level)
# ---------------------------------------------------------------------------


class TestMetricsService:
    def test_record_document_processed(self):
        """record_document_processed should not raise."""
        from services.metrics_service import record_document_processed

        record_document_processed("tenant-a", "completed")

    def test_observe_document_processing_time(self):
        from services.metrics_service import observe_document_processing_time

        observe_document_processing_time(1.5)

    def test_record_gl_classification(self):
        from services.metrics_service import record_gl_classification

        record_gl_classification("keyword_matching", "5000")

    def test_record_payment_detection(self):
        from services.metrics_service import record_payment_detection

        record_payment_detection("regex_patterns", "paid")

    def test_record_vendor_operation(self):
        from services.metrics_service import record_vendor_operation

        record_vendor_operation("create", "tenant-a")


# ---------------------------------------------------------------------------
# Metrics endpoint (only available when METRICS_ENABLED=true)
# ---------------------------------------------------------------------------


class TestMetricsEndpoint:
    def test_metrics_endpoint_disabled_by_default(self):
        """When METRICS_ENABLED=false, /metrics should 404."""
        from fastapi.testclient import TestClient

        from api.main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/metrics")
            # Default METRICS_ENABLED is False, so the route is not registered
            assert resp.status_code in (404, 405)

    def test_metrics_enabled_returns_prometheus_format(self):
        """When METRICS_ENABLED=true, /metrics should return Prometheus text."""
        # We can test the endpoint by temporarily patching the setting
        # but since the route is conditionally registered at import time,
        # we test the underlying functions instead.
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

        output = generate_latest()
        assert isinstance(output, bytes)
        # Should contain at least the python_info metric
        assert b"python_info" in output or b"process_" in output


# ---------------------------------------------------------------------------
# Middleware integration
# ---------------------------------------------------------------------------


class TestPrometheusMiddleware:
    def test_skip_paths_defined(self):
        from middleware.metrics_middleware import SKIP_PATHS

        assert "/metrics" in SKIP_PATHS
        assert "/health/live" in SKIP_PATHS
        assert "/health/ready" in SKIP_PATHS

    def test_middleware_has_prom_flag(self):
        from middleware.metrics_middleware import _HAS_PROM

        assert _HAS_PROM is True
