"""
Integration Tests for Vendor CRUD Endpoints
Tests the /vendors routes using FastAPI TestClient.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "production-server"))

from production_server.api.main import app

AUTH_HEADERS = {"Authorization": "Bearer test-key"}
CSRF_TOKEN = "test-csrf-token"
WRITE_HEADERS = {
    "Authorization": "Bearer test-key",
    "x-csrf-token": CSRF_TOKEN,
}
CSRF_COOKIES = {"csrf_token": CSRF_TOKEN}


@pytest.fixture(scope="module")
def client():
    """Create a TestClient that triggers the lifespan (startup/shutdown)."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def _create_vendor(client, name: str = "Test Vendor", **extra):
    """Helper to create a vendor and return its data."""
    payload = {"name": name, "tenant_id": "default", **extra}
    resp = client.post(
        "/vendors", json=payload, headers=WRITE_HEADERS, cookies=CSRF_COOKIES
    )
    assert resp.status_code == 201
    return resp.json()


class TestListVendors:
    def test_list_vendors_returns_200(self, client):
        response = client.get("/vendors", headers=AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_vendors_contains_created(self, client):
        vendor = _create_vendor(client, "ListCheck Vendor")
        response = client.get("/vendors", headers=AUTH_HEADERS)
        data = response.json()
        ids = [v["id"] for v in data]
        assert vendor["id"] in ids


class TestCreateVendor:
    def test_create_vendor_returns_201(self, client):
        data = _create_vendor(client, "Acme Corp")
        assert data["name"] == "Acme Corp"
        assert "id" in data
        assert data["tenant_id"] == "default"
        assert data["document_count"] == 0

    def test_create_vendor_with_optional_fields(self, client):
        data = _create_vendor(
            client,
            "BuildRight Inc",
            display_name="BuildRight",
            contact_info={"email": "info@buildright.com", "phone": "555-1234"},
            notes="Preferred lumber vendor",
            tags=["lumber", "construction"],
        )
        assert data["display_name"] == "BuildRight"
        assert data["contact_info"]["email"] == "info@buildright.com"
        assert data["notes"] == "Preferred lumber vendor"
        assert "lumber" in data["tags"]

    def test_create_vendor_validation_empty_name(self, client):
        payload = {"name": "", "tenant_id": "default"}
        response = client.post(
            "/vendors", json=payload, headers=WRITE_HEADERS, cookies=CSRF_COOKIES
        )
        assert response.status_code == 422


class TestGetVendor:
    def test_get_vendor_returns_200(self, client):
        vendor = _create_vendor(client, "GetMe Vendor")
        response = client.get(f"/vendors/{vendor['id']}", headers=AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "GetMe Vendor"
        assert data["id"] == vendor["id"]

    def test_get_vendor_not_found(self, client):
        response = client.get("/vendors/nonexistent-id", headers=AUTH_HEADERS)
        assert response.status_code == 404


class TestUpdateVendor:
    def test_update_vendor_returns_200(self, client):
        vendor = _create_vendor(client, "UpdateMe")
        response = client.put(
            f"/vendors/{vendor['id']}",
            json={"name": "Updated Name", "notes": "Updated notes"},
            headers=WRITE_HEADERS,
            cookies=CSRF_COOKIES,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["notes"] == "Updated notes"

    def test_update_vendor_not_found(self, client):
        response = client.put(
            "/vendors/nonexistent-id",
            json={"name": "Nope"},
            headers=WRITE_HEADERS,
            cookies=CSRF_COOKIES,
        )
        assert response.status_code == 404


class TestDeleteVendor:
    def test_delete_vendor_returns_200(self, client):
        vendor = _create_vendor(client, "DeleteMe")
        response = client.delete(
            f"/vendors/{vendor['id']}",
            headers=WRITE_HEADERS,
            cookies=CSRF_COOKIES,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify it's gone
        get_resp = client.get(f"/vendors/{vendor['id']}", headers=AUTH_HEADERS)
        assert get_resp.status_code == 404

    def test_delete_vendor_not_found(self, client):
        response = client.delete(
            "/vendors/nonexistent-id",
            headers=WRITE_HEADERS,
            cookies=CSRF_COOKIES,
        )
        assert response.status_code == 404


class TestVendorStats:
    def test_get_vendor_stats_returns_200(self, client):
        vendor = _create_vendor(client, "StatsVendor")
        response = client.get(
            f"/vendors/{vendor['id']}/stats", headers=AUTH_HEADERS
        )
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "payments" in data
        assert "trends" in data
        assert data["documents"]["total"] == 0

    def test_get_vendor_stats_not_found(self, client):
        response = client.get(
            "/vendors/nonexistent-id/stats", headers=AUTH_HEADERS
        )
        assert response.status_code == 404
