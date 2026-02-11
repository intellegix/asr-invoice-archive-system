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
            headers={"Authorization": "Bearer test-key"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_count"] == 79

    def test_gl_accounts_search(self, client):
        response = client.get(
            "/api/v1/gl-accounts?search=fuel",
            headers={"Authorization": "Bearer test-key"},
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
    def test_scanner_discovery(self, client):
        response = client.get("/api/scanner/discovery")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["server_name"] == "ASR Production Server"
        assert "api_endpoints" in data["data"]


class TestNotFoundEndpoint:
    def test_404_handler(self, client):
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
