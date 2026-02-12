"""
Tests for Dashboard Metrics API endpoints.
Validates the /metrics/* routes return correct shapes and status codes.
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


class TestMetricsKPIs:
    def test_kpis_returns_200(self, client: TestClient) -> None:
        response = client.get("/metrics/kpis")
        assert response.status_code == 200

    def test_kpis_has_required_fields(self, client: TestClient) -> None:
        data = client.get("/metrics/kpis").json()
        assert "totalDocuments" in data
        assert "documentsThisMonth" in data
        assert "recentDocuments" in data
        assert isinstance(data["totalDocuments"], int)
        assert isinstance(data["recentDocuments"], list)

    def test_kpis_total_gl_accounts(self, client: TestClient) -> None:
        data = client.get("/metrics/kpis").json()
        assert data["totalGLAccounts"] == 79


class TestMetricsTrends:
    def test_trends_returns_200(self, client: TestClient) -> None:
        response = client.get("/metrics/trends")
        assert response.status_code == 200

    def test_trends_default_30d(self, client: TestClient) -> None:
        data = client.get("/metrics/trends").json()
        assert data["period"] == "30d"
        assert len(data["documents"]) == 30

    def test_trends_7d(self, client: TestClient) -> None:
        data = client.get("/metrics/trends?period=7d").json()
        assert data["period"] == "7d"
        assert len(data["documents"]) == 7

    def test_trends_document_shape(self, client: TestClient) -> None:
        data = client.get("/metrics/trends").json()
        doc = data["documents"][0]
        assert "date" in doc
        assert "total" in doc
        assert "classified" in doc
        assert "manualReview" in doc


class TestMetricsPaymentStatus:
    def test_payment_status_returns_200(self, client: TestClient) -> None:
        response = client.get("/metrics/payment-status")
        assert response.status_code == 200

    def test_payment_status_has_distribution(self, client: TestClient) -> None:
        data = client.get("/metrics/payment-status").json()
        assert "distribution" in data
        assert isinstance(data["distribution"], list)


class TestMetricsGLAccounts:
    def test_gl_accounts_returns_200(self, client: TestClient) -> None:
        response = client.get("/metrics/gl-accounts")
        assert response.status_code == 200

    def test_gl_accounts_shape(self, client: TestClient) -> None:
        data = client.get("/metrics/gl-accounts").json()
        assert "accounts" in data
        assert isinstance(data["accounts"], list)


class TestMetricsVendors:
    def test_vendors_returns_200(self, client: TestClient) -> None:
        response = client.get("/metrics/vendors")
        assert response.status_code == 200


class TestMetricsExecutive:
    def test_executive_returns_200(self, client: TestClient) -> None:
        response = client.get("/metrics/executive")
        assert response.status_code == 200

    def test_executive_has_total(self, client: TestClient) -> None:
        data = client.get("/metrics/executive").json()
        assert "totalDocumentsProcessed" in data


class TestMetricsAccuracy:
    def test_accuracy_returns_200(self, client: TestClient) -> None:
        response = client.get("/metrics/accuracy")
        assert response.status_code == 200


class TestMetricsBillingDestinations:
    def test_billing_destinations_returns_200(self, client: TestClient) -> None:
        response = client.get("/metrics/billing-destinations")
        assert response.status_code == 200


class TestMetricsAging:
    def test_aging_returns_200(self, client: TestClient) -> None:
        response = client.get("/metrics/aging")
        assert response.status_code == 200
