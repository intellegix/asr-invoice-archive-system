"""
Tests for request logging middleware — correlation IDs, headers, and log behavior.
"""

import sys
import uuid
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.responses import JSONResponse

# ---------------------------------------------------------------------------
# Minimal FastAPI app fixture with the middleware under test
# ---------------------------------------------------------------------------


sys.path.insert(0, str(Path(__file__).parent.parent / "production_server"))

from middleware.request_logging_middleware import (
    RequestLoggingMiddleware,
    _get_client_ip,
)


def _create_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware, log_format="text")

    @app.get("/ping")
    async def ping():
        return {"ok": True}

    @app.get("/health/live")
    async def health_live():
        return {"status": "ok"}

    @app.get("/fail")
    async def fail():
        raise RuntimeError("boom")

    @app.get("/check-request-id")
    async def check_request_id(request: Request):
        return {"request_id": getattr(request.state, "request_id", None)}

    return app


@pytest.fixture
def client():
    return TestClient(_create_test_app(), raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCorrelationIdGeneration:
    """Middleware generates a new UUID when no X-Request-ID header is provided."""

    def test_generates_request_id(self, client: TestClient):
        response = client.get("/ping")
        request_id = response.headers.get("X-Request-ID")
        assert request_id is not None
        # Must be a valid UUID4
        uuid.UUID(request_id, version=4)

    def test_each_request_gets_unique_id(self, client: TestClient):
        ids = {client.get("/ping").headers["X-Request-ID"] for _ in range(5)}
        assert len(ids) == 5


class TestCorrelationIdPropagation:
    """Middleware respects a caller-supplied X-Request-ID."""

    def test_propagates_caller_id(self, client: TestClient):
        caller_id = "my-trace-id-123"
        response = client.get("/ping", headers={"X-Request-ID": caller_id})
        assert response.headers["X-Request-ID"] == caller_id

    def test_request_state_contains_id(self, client: TestClient):
        caller_id = "state-check-456"
        response = client.get("/check-request-id", headers={"X-Request-ID": caller_id})
        assert response.json()["request_id"] == caller_id


class TestResponseHeaders:
    """Middleware always adds response-time and request-id headers."""

    def test_response_time_header(self, client: TestClient):
        response = client.get("/ping")
        response_time = response.headers.get("X-Response-Time")
        assert response_time is not None
        assert response_time.endswith("ms")

    def test_error_returns_500(self, client: TestClient):
        response = client.get("/fail")
        assert response.status_code == 500


class TestHealthCheckSkip:
    """Health-check paths should still get an X-Request-ID but skip detailed logging."""

    def test_health_live_has_request_id(self, client: TestClient):
        response = client.get("/health/live")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers


class TestGetClientIp:
    """Unit tests for _get_client_ip helper."""

    def test_forwarded_for(self):
        """X-Forwarded-For should take priority."""

        class FakeRequest:
            headers = {"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}
            client = None

        assert _get_client_ip(FakeRequest()) == "1.2.3.4"

    def test_direct_client(self):
        """Falls back to client.host."""

        class FakeClient:
            host = "10.0.0.1"

        class FakeRequest:
            headers = {}
            client = FakeClient()

        assert _get_client_ip(FakeRequest()) == "10.0.0.1"

    def test_no_client(self):
        class FakeRequest:
            headers = {}
            client = None

        assert _get_client_ip(FakeRequest()) == "unknown"
