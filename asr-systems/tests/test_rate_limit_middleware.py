"""
Unit Tests for Rate Limit Middleware
Tests sliding window rate limiting, client ID extraction, 429 responses,
rate limit headers, and per-client isolation.
"""

import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "production-server"))

from middleware.rate_limit_middleware import RateLimitMiddleware


def _build_app(calls=5, period=60):
    """Build a minimal FastAPI app with RateLimitMiddleware."""
    test_app = FastAPI()
    test_app.add_middleware(RateLimitMiddleware, calls=calls, period=period)

    @test_app.get("/health")
    async def health():
        return {"status": "ok"}

    @test_app.get("/")
    async def root():
        return {"root": True}

    @test_app.get("/api/v1/test")
    async def api_get(request: Request):
        return {"method": "GET"}

    @test_app.post("/api/v1/test")
    async def api_post(request: Request):
        return {"method": "POST"}

    return test_app


# ---------------------------------------------------------------------------
# Skip-path tests
# ---------------------------------------------------------------------------


class TestSkipPaths:
    def test_health_skips_rate_limiting(self):
        """Health endpoint should never be rate limited."""
        app = _build_app(calls=1, period=60)
        with TestClient(app) as client:
            for _ in range(10):
                resp = client.get("/health")
                assert resp.status_code == 200

    def test_root_skips_rate_limiting(self):
        """Root endpoint should never be rate limited."""
        app = _build_app(calls=1, period=60)
        with TestClient(app) as client:
            for _ in range(10):
                resp = client.get("/")
                assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Rate limit headers
# ---------------------------------------------------------------------------


class TestRateLimitHeaders:
    def test_limit_header_present(self):
        """X-RateLimit-Limit header should be set on API responses."""
        app = _build_app(calls=10, period=60)
        with TestClient(app) as client:
            resp = client.get("/api/v1/test")
            assert resp.status_code == 200
            assert "X-RateLimit-Limit" in resp.headers
            assert resp.headers["X-RateLimit-Limit"] == "10"

    def test_remaining_header_present(self):
        """X-RateLimit-Remaining header should be present and accurate."""
        app = _build_app(calls=10, period=60)
        with TestClient(app) as client:
            resp = client.get("/api/v1/test")
            assert "X-RateLimit-Remaining" in resp.headers
            remaining = int(resp.headers["X-RateLimit-Remaining"])
            assert remaining == 9  # 10 allowed - 1 used

    def test_remaining_decrements(self):
        """X-RateLimit-Remaining should decrement with each request."""
        app = _build_app(calls=5, period=60)
        with TestClient(app) as client:
            remainders = []
            for _ in range(3):
                resp = client.get("/api/v1/test")
                remainders.append(int(resp.headers["X-RateLimit-Remaining"]))
            # Should be 4, 3, 2
            assert remainders == [4, 3, 2]

    def test_rate_limit_applies_to_get(self):
        """GET endpoints should be subject to rate limiting."""
        app = _build_app(calls=2, period=60)
        with TestClient(app) as client:
            resp1 = client.get("/api/v1/test")
            assert resp1.status_code == 200
            resp2 = client.get("/api/v1/test")
            assert resp2.status_code == 200
            resp3 = client.get("/api/v1/test")
            assert resp3.status_code == 429

    def test_rate_limit_applies_to_post(self):
        """POST endpoints should also be subject to rate limiting."""
        app = _build_app(calls=2, period=60)
        with TestClient(app) as client:
            resp1 = client.post("/api/v1/test")
            assert resp1.status_code == 200
            resp2 = client.post("/api/v1/test")
            assert resp2.status_code == 200
            resp3 = client.post("/api/v1/test")
            assert resp3.status_code == 429


# ---------------------------------------------------------------------------
# 429 Too Many Requests
# ---------------------------------------------------------------------------


class TestRateLimitExceeded:
    def test_returns_429_when_limit_exceeded(self):
        """Should return 429 after the call limit is reached."""
        app = _build_app(calls=2, period=60)
        with TestClient(app) as client:
            client.get("/api/v1/test")
            client.get("/api/v1/test")
            resp = client.get("/api/v1/test")
            assert resp.status_code == 429

    def test_429_includes_retry_after(self):
        """429 response should include Retry-After header."""
        app = _build_app(calls=1, period=30)
        with TestClient(app) as client:
            client.get("/api/v1/test")
            resp = client.get("/api/v1/test")
            assert resp.status_code == 429
            assert "Retry-After" in resp.headers
            assert resp.headers["Retry-After"] == "30"

    def test_429_includes_rate_limit_headers(self):
        """429 response should include X-RateLimit-Limit and Remaining=0."""
        app = _build_app(calls=1, period=60)
        with TestClient(app) as client:
            client.get("/api/v1/test")
            resp = client.get("/api/v1/test")
            assert resp.status_code == 429
            assert resp.headers["X-RateLimit-Limit"] == "1"
            assert resp.headers["X-RateLimit-Remaining"] == "0"

    def test_429_body_includes_error_message(self):
        """429 response body should include a descriptive error message."""
        app = _build_app(calls=1, period=60)
        with TestClient(app) as client:
            client.get("/api/v1/test")
            resp = client.get("/api/v1/test")
            body = resp.json()
            assert "message" in body
            assert "rate limit" in body["message"].lower()


# ---------------------------------------------------------------------------
# Client ID extraction
# ---------------------------------------------------------------------------


class TestClientIDExtraction:
    def test_bearer_token_as_client_id(self):
        """Bearer token should be used to derive client ID."""
        app = _build_app(calls=2, period=60)
        with TestClient(app) as client:
            # Client A uses a different token from the default IP-based client
            for _ in range(2):
                resp = client.get(
                    "/api/v1/test",
                    headers={"Authorization": "Bearer tokenAAAAAAAAAA"},
                )
                assert resp.status_code == 200
            # Token A exhausted, but IP-based client still has quota
            resp_ip = client.get("/api/v1/test")
            assert resp_ip.status_code == 200

    def test_x_forwarded_for_as_client_id(self):
        """X-Forwarded-For header should be used when no Bearer token."""
        app = _build_app(calls=2, period=60)
        with TestClient(app) as client:
            for _ in range(2):
                resp = client.get(
                    "/api/v1/test",
                    headers={"X-Forwarded-For": "203.0.113.50"},
                )
                assert resp.status_code == 200
            # Forwarded IP exhausted
            resp = client.get(
                "/api/v1/test",
                headers={"X-Forwarded-For": "203.0.113.50"},
            )
            assert resp.status_code == 429

    def test_different_clients_have_separate_limits(self):
        """Requests from different clients should not share rate limits."""
        app = _build_app(calls=1, period=60)
        with TestClient(app) as client:
            resp_a = client.get(
                "/api/v1/test",
                headers={"Authorization": "Bearer clientAtoken1"},
            )
            assert resp_a.status_code == 200

            resp_b = client.get(
                "/api/v1/test",
                headers={"Authorization": "Bearer clientBtoken2"},
            )
            assert resp_b.status_code == 200


# ---------------------------------------------------------------------------
# Window cleanup / reset
# ---------------------------------------------------------------------------


class TestWindowReset:
    def test_rate_limit_resets_after_window(self):
        """Rate limit should reset after the sliding window expires."""
        app = _build_app(calls=2, period=1)
        middleware = None
        for m in app.user_middleware:
            if m.cls is RateLimitMiddleware:
                middleware = m
                break

        with TestClient(app) as client:
            client.get("/api/v1/test")
            client.get("/api/v1/test")
            resp = client.get("/api/v1/test")
            assert resp.status_code == 429

            # Wait for the 1-second window to expire
            time.sleep(1.1)

            resp = client.get("/api/v1/test")
            assert resp.status_code == 200

    def test_old_requests_cleaned_from_window(self):
        """Old timestamps outside the window should be pruned."""
        app = _build_app(calls=3, period=1)
        with TestClient(app) as client:
            # Make 2 requests
            client.get("/api/v1/test")
            client.get("/api/v1/test")

            # Wait for window to expire
            time.sleep(1.1)

            # These should succeed because old entries are cleaned
            resp1 = client.get("/api/v1/test")
            assert resp1.status_code == 200
            remaining = int(resp1.headers["X-RateLimit-Remaining"])
            assert remaining == 2  # Full quota available again


# ---------------------------------------------------------------------------
# Memory management (P12)
# ---------------------------------------------------------------------------


class TestMemoryManagement:
    def test_cleanup_evicts_expired_entries(self):
        """_cleanup() should remove client entries whose timestamps are all expired."""
        middleware = RateLimitMiddleware(app=None, calls=100, period=1)
        backend = middleware._backend
        # Manually insert expired entries
        old_time = time.time() - 10
        backend.clients["ip:expired-1"] = [old_time]
        backend.clients["ip:expired-2"] = [old_time]
        backend.clients["ip:fresh"] = [time.time()]

        backend._cleanup()

        assert "ip:expired-1" not in backend.clients
        assert "ip:expired-2" not in backend.clients
        assert "ip:fresh" in backend.clients

    def test_max_client_cap_enforced(self):
        """LRU eviction should keep tracked clients at or below MAX_TRACKED_CLIENTS."""
        from middleware.rate_limit_middleware import MAX_TRACKED_CLIENTS

        middleware = RateLimitMiddleware(app=None, calls=100, period=60)
        backend = middleware._backend
        now = time.time()
        for i in range(MAX_TRACKED_CLIENTS + 500):
            backend.clients[f"ip:{i}"] = [now]

        backend._cleanup()

        assert len(backend.clients) <= MAX_TRACKED_CLIENTS

    def test_amortized_cleanup_triggers(self):
        """Cleanup should trigger every 100 requests."""
        middleware = RateLimitMiddleware(app=None, calls=1000, period=1)
        backend = middleware._backend
        old_time = time.time() - 10
        backend.clients["ip:stale"] = [old_time]

        # Force counter to 99 so next call triggers cleanup
        backend._cleanup_counter = 99

        backend.is_rate_limited("ip:trigger")

        # After cleanup, stale entry should be gone
        assert "ip:stale" not in backend.clients
