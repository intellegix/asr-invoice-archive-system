"""
Tests for split health endpoints (/health/live, /health/ready, /health).
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
    # Reset the shutdown flag in case a previous module's TestClient
    # lifespan teardown set it to True (shared singleton app).
    import production_server.api.main as main_module

    main_module._shutting_down = False
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestLivenessProbe:
    """GET /health/live — lightweight liveness check."""

    def test_returns_200(self, client: TestClient):
        response = client.get("/health/live")
        assert response.status_code == 200

    def test_contains_status(self, client: TestClient):
        data = client.get("/health/live").json()
        assert data["status"] == "ok"

    def test_contains_uptime(self, client: TestClient):
        data = client.get("/health/live").json()
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))


class TestReadinessProbe:
    """GET /health/ready — full service readiness."""

    def test_returns_200(self, client: TestClient):
        response = client.get("/health/ready")
        assert response.status_code == 200

    def test_contains_components(self, client: TestClient):
        data = client.get("/health/ready").json()
        assert "components" in data
        assert "overall_status" in data


class TestLegacyHealthEndpoint:
    """GET /health — backwards-compatible alias."""

    def test_returns_200(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200

    def test_same_shape_as_ready(self, client: TestClient):
        ready_data = client.get("/health/ready").json()
        legacy_data = client.get("/health").json()
        assert set(ready_data.keys()) == set(legacy_data.keys())


class TestShutdownFlag:
    """Readiness probe should return 503 during shutdown."""

    def test_ready_returns_503_during_shutdown(self, client: TestClient):
        import production_server.api.main as main_module

        original = main_module._shutting_down
        try:
            main_module._shutting_down = True
            response = client.get("/health/ready")
            assert response.status_code == 503
            assert "shutting_down" in response.json().get("overall_status", "")
        finally:
            main_module._shutting_down = original

    def test_live_still_works_during_shutdown(self, client: TestClient):
        import production_server.api.main as main_module

        original = main_module._shutting_down
        try:
            main_module._shutting_down = True
            response = client.get("/health/live")
            assert response.status_code == 200
        finally:
            main_module._shutting_down = original
