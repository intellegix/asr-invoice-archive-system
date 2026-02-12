"""
Tests for CSRF double-submit cookie middleware.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from production_server.middleware.csrf_middleware import (
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
    CSRFMiddleware,
)


def _make_app(enabled: bool = True) -> FastAPI:
    app = FastAPI()
    app.add_middleware(CSRFMiddleware, enabled=enabled)

    @app.get("/")
    async def root():
        return {"ok": True}

    @app.post("/api/v1/documents/upload")
    async def upload():
        return {"uploaded": True}

    @app.get("/health")
    async def health():
        return {"healthy": True}

    @app.post("/auth/login")
    async def login():
        return {"authenticated": True}

    return app


class TestCSRFMiddleware:
    """CSRF middleware tests."""

    def test_get_request_sets_csrf_cookie(self) -> None:
        """GET requests should receive a csrf_token cookie."""
        client = TestClient(_make_app())
        resp = client.get("/")
        assert resp.status_code == 200
        assert CSRF_COOKIE_NAME in resp.cookies

    def test_post_without_csrf_token_returns_403(self) -> None:
        """POST without X-CSRF-Token header should be rejected."""
        client = TestClient(_make_app())
        resp = client.post("/api/v1/documents/upload")
        assert resp.status_code == 403
        assert "CSRF" in resp.json()["message"]

    def test_post_with_valid_csrf_token_succeeds(self) -> None:
        """POST with matching cookie + header should succeed."""
        client = TestClient(_make_app())
        # First GET to obtain the cookie
        get_resp = client.get("/")
        csrf_token = get_resp.cookies[CSRF_COOKIE_NAME]

        # POST with matching header
        resp = client.post(
            "/api/v1/documents/upload",
            headers={CSRF_HEADER_NAME: csrf_token},
            cookies={CSRF_COOKIE_NAME: csrf_token},
        )
        assert resp.status_code == 200

    def test_post_with_mismatched_token_returns_403(self) -> None:
        """POST with mismatched cookie/header should be rejected."""
        client = TestClient(_make_app())
        get_resp = client.get("/")
        csrf_token = get_resp.cookies[CSRF_COOKIE_NAME]

        resp = client.post(
            "/api/v1/documents/upload",
            headers={CSRF_HEADER_NAME: "wrong-token"},
            cookies={CSRF_COOKIE_NAME: csrf_token},
        )
        assert resp.status_code == 403

    def test_exempt_path_skips_csrf(self) -> None:
        """POST to /auth/login should bypass CSRF validation."""
        client = TestClient(_make_app())
        resp = client.post("/auth/login")
        assert resp.status_code == 200

    def test_health_exempt(self) -> None:
        """GET to /health should not require CSRF."""
        client = TestClient(_make_app())
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_disabled_middleware_allows_all(self) -> None:
        """When disabled, POST without CSRF header should succeed."""
        client = TestClient(_make_app(enabled=False))
        resp = client.post("/api/v1/documents/upload")
        assert resp.status_code == 200
