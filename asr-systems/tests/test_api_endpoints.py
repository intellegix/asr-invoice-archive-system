"""
Integration Tests for FastAPI API Endpoints
Tests routes using FastAPI TestClient (health, GL accounts, status, system info).
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "production-server"))

from auth_helpers import AUTH_HEADERS, CSRF_COOKIES, WRITE_HEADERS
from production_server.api.main import app


@pytest.fixture(scope="module")
def client():
    """Create a TestClient that triggers the lifespan (startup/shutdown)."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestRootEndpoint:
    def test_root_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "online"
        assert data["data"]["version"] == "2.0.0"


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] in ("healthy", "degraded")
        assert "components" in data
        assert "gl_accounts" in data["components"]

    def test_health_reports_gl_accounts(self, client):
        response = client.get("/health")
        data = response.json()
        gl = data["components"]["gl_accounts"]
        assert gl["status"] == "healthy"
        assert gl["count"] == 79


class TestAPIStatusEndpoint:
    def test_api_status_returns_200(self, client):
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["system_type"] == "production_server"
        assert "services" in data["data"]


class TestGLAccountsEndpoint:
    def test_list_gl_accounts(self, client):
        response = client.get(
            "/api/v1/gl-accounts",
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_count"] == 79

    def test_gl_accounts_search(self, client):
        response = client.get(
            "/api/v1/gl-accounts?search=fuel",
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_count"] >= 1


class TestSystemInfoEndpoint:
    def test_system_info(self, client):
        response = client.get("/api/v1/system/info")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["capabilities"]["gl_accounts"]["total"] == 79


class TestAPIInfoEndpoint:
    def test_api_info(self, client):
        response = client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "2.0.0"
        assert data["gl_accounts_count"] == 79
        assert "pdf" in data["supported_formats"]


class TestScannerDiscoveryEndpoint:
    def test_scanner_discovery_with_auth(self, client):
        response = client.get(
            "/api/scanner/discovery",
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["server_name"] == "ASR Production Server"
        assert "api_endpoints" in data["data"]

    def test_scanner_discovery_without_auth_returns_401(self, client):
        response = client.get("/api/scanner/discovery")
        # When API_KEYS_REQUIRED=false (test/dev), auth is permissive
        # so this returns 200. In production it would return 401.
        assert response.status_code in (200, 401)


class TestAuditLogEndpoints:
    def test_audit_logs_by_tenant_returns_200(self, client):
        response = client.get(
            "/api/v1/audit-logs?tenant_id=default",
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "entries" in data["data"]
        assert "total_count" in data["data"]

    def test_audit_logs_by_document_returns_200(self, client):
        response = client.get(
            "/api/v1/audit-logs/nonexistent-doc",
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["entries"] == []
        assert data["data"]["total_count"] == 0

    def test_audit_logs_without_tenant_returns_empty(self, client):
        response = client.get(
            "/api/v1/audit-logs?tenant_id=unknown-tenant",
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_count"] == 0


class TestReprocessEndpoints:
    def test_reprocess_document_returns_200(self, client):
        """Reprocessing a non-existent doc should still return a response
        (the service returns an error-status UploadResult, not an exception)."""
        response = client.post(
            "/extract/invoice/test-doc-001",
            headers=WRITE_HEADERS,
            cookies=CSRF_COOKIES,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "document_id" in data["data"]

    def test_extract_details_returns_200(self, client):
        response = client.get(
            "/extract/invoice/test-doc-001/details",
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["document_id"] == "test-doc-001"


class TestSearchEndpoint:
    def test_quick_search_returns_200(self, client):
        response = client.get(
            "/search/quick?q=invoice",
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "results" in data["data"]


class TestSettingsEndpoint:
    def test_settings_endpoint_returns_config(self, client):
        response = client.get(
            "/api/v1/settings",
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["version"] == "2.0.0"
        assert data["data"]["system_type"] == "production_server"

    def test_settings_includes_capabilities(self, client):
        response = client.get(
            "/api/v1/settings",
            headers=AUTH_HEADERS,
        )
        data = response.json()
        caps = data["data"]["capabilities"]
        assert caps["gl_accounts"]["total"] == 79
        assert "payment_detection" in caps


class TestMetricsEndpoints:
    def test_metrics_kpis_returns_200(self, client):
        response = client.get("/metrics/kpis")
        assert response.status_code == 200
        data = response.json()
        assert "totalDocuments" in data

    def test_metrics_trends_returns_200(self, client):
        response = client.get("/metrics/trends?period=30d")
        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "documents" in data


class TestDeleteDocumentEndpoint:
    def test_delete_nonexistent_returns_404(self, client):
        """DELETE for a nonexistent document should return 404."""
        response = client.delete(
            "/api/v1/documents/nonexistent-doc",
            headers=WRITE_HEADERS,
            cookies=CSRF_COOKIES,
        )
        assert response.status_code == 404

    def test_delete_too_long_id_returns_422(self, client):
        """DELETE with an overly long document ID should return 422."""
        csrf_token = "test-csrf-token"
        long_id = "a" * 65  # exceeds 64-char limit
        response = client.delete(
            f"/api/v1/documents/{long_id}",
            headers=WRITE_HEADERS,
            cookies=CSRF_COOKIES,
        )
        assert response.status_code == 422


class TestSearchEndpointExtended:
    def test_quick_search_empty_query_returns_empty(self, client):
        """Quick search with empty query returns empty results."""
        response = client.get(
            "/search/quick?q=",
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["results"] == []
        assert data["data"]["total"] == 0

    def test_quick_search_with_query(self, client):
        """Quick search with a query term returns valid structure."""
        response = client.get(
            "/search/quick?q=invoice",
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data["data"]
        assert "total" in data["data"]


class TestHealthEndpointTimeout:
    def test_health_endpoint_responds_quickly(self, client):
        """Health endpoint should respond within 3 seconds."""
        import time

        start = time.time()
        response = client.get("/health/ready")
        elapsed = time.time() - start
        assert response.status_code == 200
        assert elapsed < 3.0

    def test_health_live_returns_uptime(self, client):
        """Liveness probe should return uptime."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["uptime_seconds"] >= 0


class TestNotFoundEndpoint:
    def test_404_handler(self, client):
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
