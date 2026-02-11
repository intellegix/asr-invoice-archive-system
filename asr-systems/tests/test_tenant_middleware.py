"""
Unit Tests for Tenant Middleware
Tests X-Tenant-ID extraction, fallback logic, skip paths, and response headers.
"""

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "production-server"))

from middleware.tenant_middleware import DEFAULT_TENANT_ID, TenantMiddleware


def _build_app():
    """Build a minimal FastAPI app with TenantMiddleware for isolated testing."""
    test_app = FastAPI()
    test_app.add_middleware(TenantMiddleware)

    @test_app.get("/health")
    async def health():
        return {"status": "ok"}

    @test_app.get("/docs")
    async def docs():
        return {"docs": True}

    @test_app.get("/")
    async def root():
        return {"root": True}

    @test_app.get("/api/v1/test")
    async def api_endpoint(request: Request):
        tenant_id = getattr(request.state, "tenant_id", None)
        return {"tenant_id": tenant_id}

    @test_app.post("/api/v1/upload")
    async def api_upload(request: Request):
        tenant_id = getattr(request.state, "tenant_id", None)
        return {"tenant_id": tenant_id}

    return test_app


@pytest.fixture(scope="module")
def client():
    app = _build_app()
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Skip-path tests (health, docs, root get default tenant)
# ---------------------------------------------------------------------------


class TestSkipPaths:
    def test_health_gets_default_tenant(self, client):
        """Health endpoint should get the default tenant without any header."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_docs_gets_default_tenant(self, client):
        """Docs endpoint should be skipped by tenant validation."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_root_gets_default_tenant(self, client):
        """Root endpoint should be in the skip list."""
        response = client.get("/")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Header extraction
# ---------------------------------------------------------------------------


class TestHeaderExtraction:
    def test_extracts_tenant_from_header(self, client):
        """X-Tenant-ID header should be extracted and forwarded."""
        response = client.get("/api/v1/test", headers={"X-Tenant-ID": "acme-corp"})
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == "acme-corp"

    def test_response_includes_tenant_header(self, client):
        """Response should echo back X-Tenant-ID for debugging."""
        response = client.get("/api/v1/test", headers={"X-Tenant-ID": "acme-corp"})
        assert response.headers.get("X-Tenant-ID") == "acme-corp"

    def test_different_tenants_get_different_ids(self, client):
        """Two requests with different headers should yield different tenant IDs."""
        resp_a = client.get("/api/v1/test", headers={"X-Tenant-ID": "tenant-a"})
        resp_b = client.get("/api/v1/test", headers={"X-Tenant-ID": "tenant-b"})
        assert resp_a.json()["tenant_id"] == "tenant-a"
        assert resp_b.json()["tenant_id"] == "tenant-b"


# ---------------------------------------------------------------------------
# Fallback logic
# ---------------------------------------------------------------------------


class TestFallback:
    def test_fallback_to_query_param(self, client):
        """When no header is provided, tenant_id query param should be used."""
        response = client.get("/api/v1/test?tenant_id=from-query")
        data = response.json()
        assert data["tenant_id"] == "from-query"

    def test_fallback_to_default_when_no_header_or_query(self, client):
        """When neither header nor query param, default tenant should be used."""
        response = client.get("/api/v1/test")
        data = response.json()
        assert data["tenant_id"] == DEFAULT_TENANT_ID

    def test_empty_header_falls_back_to_default(self, client):
        """An empty X-Tenant-ID header should fall back to default."""
        response = client.get("/api/v1/test", headers={"X-Tenant-ID": ""})
        data = response.json()
        # Empty string is falsy, so middleware should use default
        assert data["tenant_id"] == DEFAULT_TENANT_ID

    def test_long_tenant_id_is_passed_through(self, client):
        """A very long tenant ID should still be passed through (no truncation)."""
        long_id = "t" * 500
        response = client.get("/api/v1/test", headers={"X-Tenant-ID": long_id})
        data = response.json()
        assert data["tenant_id"] == long_id
