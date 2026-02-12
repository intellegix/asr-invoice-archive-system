"""
Tests for /auth/login and /auth/me endpoints.
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
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestAuthLogin:
    def test_login_valid_key(self, client):
        response = client.post(
            "/auth/login",
            json={"api_key": "sk-ant-valid-key-1234567890", "tenant_id": "default"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["tenant_id"] == "default"
        assert data["server_version"] == "2.0.0"

    def test_login_empty_key_422(self, client):
        response = client.post(
            "/auth/login",
            json={"api_key": "", "tenant_id": "default"},
        )
        assert response.status_code == 422

    def test_login_short_key_401(self, client):
        response = client.post(
            "/auth/login",
            json={"api_key": "short", "tenant_id": "default"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Invalid API key"

    def test_login_returns_capabilities(self, client):
        response = client.post(
            "/auth/login",
            json={"api_key": "sk-ant-valid-key-1234567890"},
        )
        data = response.json()
        assert data["capabilities"]["gl_accounts"] == 79

    def test_login_default_tenant(self, client):
        response = client.post(
            "/auth/login",
            json={"api_key": "sk-ant-valid-key-1234567890"},
        )
        data = response.json()
        assert data["tenant_id"] == "default"

    def test_login_custom_tenant(self, client):
        response = client.post(
            "/auth/login",
            json={"api_key": "sk-ant-valid-key-1234567890", "tenant_id": "acme-corp"},
        )
        data = response.json()
        assert data["tenant_id"] == "acme-corp"

    def test_login_no_body_422(self, client):
        response = client.post("/auth/login")
        assert response.status_code == 422


class TestAuthMe:
    def test_me_with_token(self, client):
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer sk-ant-valid-key-1234567890"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True

    def test_me_no_token_401(self, client):
        response = client.get("/auth/me")
        assert response.status_code in (401, 403)

    def test_me_returns_tenant(self, client):
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer sk-ant-valid-key-1234567890"},
        )
        data = response.json()
        assert "tenant_id" in data

    def test_me_returns_api_keys_required_flag(self, client):
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer sk-ant-valid-key-1234567890"},
        )
        data = response.json()
        assert isinstance(data["api_keys_required"], bool)
