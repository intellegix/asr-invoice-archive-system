"""
Unit Tests for Shared API Client
Covers APIClient, response handling, retry logic, error classification
"""

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "production-server"))

from shared.api.client import APIClient, DocumentScannerClient, ProductionServerClient
from shared.core.exceptions import (
    APIError,
    AuthenticationError,
    NetworkError,
    RetryableError,
)
from shared.core.exceptions import ValidationError as ASRValidationError


@pytest.fixture
def client():
    """Create an APIClient for testing."""
    return APIClient(
        base_url="http://localhost:8000",
        api_key="test-key-" + "a" * 30,
        tenant_id="test-tenant",
        timeout=5,
        max_retries=0,
    )


@pytest.fixture
def client_with_retries():
    """Create an APIClient with retries enabled."""
    return APIClient(
        base_url="http://localhost:8000/",
        api_key="test-key-" + "a" * 30,
        tenant_id="test-tenant",
        timeout=5,
        max_retries=2,
    )


class TestAPIClientInit:
    """Tests for APIClient initialization."""

    def test_base_url_trailing_slash_stripped(self, client):
        c = APIClient(
            base_url="http://localhost:8000/",
            api_key="k" * 32,
            tenant_id="t1",
        )
        assert c.base_url == "http://localhost:8000"

    def test_default_headers_set(self, client):
        headers = client.client.headers
        assert "authorization" in {k.lower() for k in headers}

    def test_request_id_format(self, client):
        rid = client._get_request_id()
        assert rid.startswith("req_")
        assert len(rid) > 4


class TestHandleResponseErrors:
    """Tests for _handle_response_errors()."""

    def _make_response(self, status_code, json_data=None, headers=None):
        """Helper to build a mock httpx.Response."""
        content = json.dumps(json_data or {}).encode()
        return httpx.Response(
            status_code=status_code,
            content=content,
            headers=headers or {},
            request=httpx.Request("GET", "http://test/"),
        )

    def test_401_raises_auth_error(self, client):
        resp = self._make_response(401)
        with pytest.raises(AuthenticationError):
            client._handle_response_errors(resp)

    def test_403_raises_auth_error(self, client):
        resp = self._make_response(403)
        with pytest.raises(AuthenticationError):
            client._handle_response_errors(resp)

    def test_404_raises_api_error(self, client):
        resp = self._make_response(404)
        with pytest.raises(APIError):
            client._handle_response_errors(resp)

    def test_422_raises_validation_error(self, client):
        resp = self._make_response(422, {"detail": "bad input"})
        with pytest.raises(ASRValidationError):
            client._handle_response_errors(resp)

    def test_422_invalid_json(self, client):
        resp = httpx.Response(
            status_code=422,
            content=b"not json",
            request=httpx.Request("GET", "http://test/"),
        )
        with pytest.raises(ASRValidationError):
            client._handle_response_errors(resp)

    def test_429_raises_retryable_error(self, client):
        resp = self._make_response(429, headers={"Retry-After": "30"})
        with pytest.raises(RetryableError) as exc_info:
            client._handle_response_errors(resp)
        assert exc_info.value.retry_after == 30

    def test_500_raises_api_error(self, client):
        resp = self._make_response(500, {"message": "Server error"})
        with pytest.raises(APIError):
            client._handle_response_errors(resp)

    def test_200_no_error(self, client):
        resp = self._make_response(200)
        client._handle_response_errors(resp)  # Should not raise


class TestParseResponse:
    """Tests for _parse_response()."""

    @pytest.mark.asyncio
    async def test_returns_json_data(self, client):
        resp = httpx.Response(
            status_code=200,
            content=json.dumps({"status": "ok"}).encode(),
            request=httpx.Request("GET", "http://test/"),
        )
        result = await client._parse_response(resp)
        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_invalid_json_raises(self, client):
        resp = httpx.Response(
            status_code=200,
            content=b"not json at all",
            request=httpx.Request("GET", "http://test/"),
        )
        with pytest.raises(APIError, match="Invalid JSON"):
            await client._parse_response(resp)


class TestMakeRequest:
    """Tests for _make_request() retry and error handling."""

    @pytest.mark.asyncio
    async def test_successful_get(self, client):
        mock_resp = httpx.Response(
            status_code=200,
            content=b'{"ok": true}',
            request=httpx.Request("GET", "http://localhost:8000/health"),
        )
        client.client = AsyncMock()
        client.client.request = AsyncMock(return_value=mock_resp)

        resp = await client._make_request("GET", "/health")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_network_error_no_retries(self, client):
        client.client = AsyncMock()
        client.client.request = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with pytest.raises(NetworkError):
            await client._make_request("GET", "/health")

    @pytest.mark.asyncio
    async def test_json_data_sent(self, client):
        mock_resp = httpx.Response(
            status_code=200,
            content=b'{"ok": true}',
            request=httpx.Request("POST", "http://localhost:8000/api"),
        )
        client.client = AsyncMock()
        client.client.request = AsyncMock(return_value=mock_resp)

        await client._make_request("POST", "/api", data={"key": "value"})
        call_kwargs = client.client.request.call_args
        assert call_kwargs.kwargs.get("json") == {"key": "value"}


class TestContextManager:
    """Tests for async context manager protocol."""

    @pytest.mark.asyncio
    async def test_aenter_aexit(self):
        async with APIClient(
            base_url="http://localhost:8000",
            api_key="k" * 32,
            tenant_id="t1",
        ) as c:
            assert c is not None
            assert isinstance(c, APIClient)


class TestProductionServerClient:
    """Tests for ProductionServerClient subclass."""

    def test_inherits_api_client(self):
        c = ProductionServerClient(
            server_url="http://localhost:8000",
            api_key="k" * 32,
            tenant_id="t1",
            scanner_id="scanner-001",
        )
        assert isinstance(c, APIClient)
        assert c.scanner_id == "scanner-001"


class TestDocumentScannerClient:
    """Tests for DocumentScannerClient subclass."""

    def test_inherits_api_client(self):
        c = DocumentScannerClient(
            base_url="http://localhost:8000",
            api_key="k" * 32,
            tenant_id="t1",
        )
        assert isinstance(c, APIClient)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
