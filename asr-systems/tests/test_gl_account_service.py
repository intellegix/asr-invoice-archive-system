"""
Unit Tests for GL Account Service
Comprehensive testing of 79 QuickBooks GL accounts and classification methods
"""

import asyncio
import sys
from pathlib import Path

import pytest

# Add shared modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "production-server"))

from production_server.services.gl_account_service import GLAccountService
from shared.core.exceptions import ClassificationError


class TestGLAccountService:
    """Comprehensive test suite for GL Account Service"""

    @pytest.fixture
    async def gl_service(self):
        """Initialize GL Account Service for testing"""
        service = GLAccountService()
        await service.initialize()
        return service

    @pytest.mark.asyncio
    async def test_service_initialization(self, gl_service):
        """Test GL Account Service initialization"""
        assert gl_service.initialized is True
        assert len(gl_service.gl_accounts) == 79
        assert len(gl_service.keyword_index) > 0
        assert len(gl_service.category_index) == 5

    @pytest.mark.asyncio
    async def test_all_79_accounts_loaded(self, gl_service):
        """Test that all 79 GL accounts are properly loaded"""
        accounts = gl_service.get_all_accounts()
        assert len(accounts) == 79

        # Verify account structure
        for account in accounts:
            assert "code" in account
            assert "name" in account
            assert "category" in account
            assert "keywords" in account
            assert "active" in account

    @pytest.mark.asyncio
    async def test_vendor_classification(self, gl_service):
        """Test vendor-specific classification"""
        result = await gl_service.classify_document_text(
            "Invoice from Home Depot for construction materials",
            vendor_name="Home Depot",
        )

        assert result.gl_account_code == "5000"
        assert result.confidence > 0.8
        assert result.classification_method == "vendor_mapping"

    @pytest.mark.asyncio
    async def test_keyword_classification(self, gl_service):
        """Test keyword-based classification"""
        test_cases = [
            ("lumber plywood construction materials", "5000"),
            ("gasoline fuel for trucks", "6900"),
            ("electric bill utility payment", "6600"),
            ("legal fees attorney consultation", "5700"),
            ("insurance premium coverage", "5500"),
            ("office rent monthly payment", "4400"),
        ]

        for text, expected_code in test_cases:
            result = await gl_service.classify_document_text(text)
            assert result.gl_account_code == expected_code
            assert result.confidence > 0.6

    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, gl_service):
        """Test classification performance"""
        import time

        test_text = "Home Depot construction materials lumber plywood supplies"
        start_time = time.time()
        result = await gl_service.classify_document_text(test_text)
        end_time = time.time()

        classification_time = end_time - start_time
        assert classification_time < 1.0

    @pytest.mark.asyncio
    async def test_concurrent_classification(self, gl_service):
        """Test concurrent classification requests"""
        test_texts = [
            "Home Depot materials",
            "SDGE electric bill",
            "Shell gasoline fuel",
            "Legal attorney fees",
            "Insurance premium",
        ]

        tasks = [gl_service.classify_document_text(text) for text in test_texts]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        for result in results:
            assert result.confidence > 0.5


class TestGLVendorDBIntegration:
    """Tests for vendor DB lookup in GL classification."""

    @pytest.fixture
    async def gl_service_with_vendor(self):
        """GL service backed by a mock vendor service."""
        from unittest.mock import AsyncMock

        mock_vs = AsyncMock()
        mock_vs.match_vendor = AsyncMock(return_value=None)
        service = GLAccountService(vendor_service=mock_vs)
        await service.initialize()
        return service, mock_vs

    @pytest.mark.asyncio
    async def test_db_vendor_match_returns_gl(self, gl_service_with_vendor):
        """When VendorService returns a vendor with default_gl_account, use it."""
        service, mock_vs = gl_service_with_vendor
        mock_vs.match_vendor.return_value = {
            "id": "v1",
            "name": "ACME Lumber",
            "default_gl_account": "5000",
        }
        result = await service.classify_document_text(
            "invoice for lumber", vendor_name="ACME Lumber", tenant_id="t1"
        )
        assert result.gl_account_code == "5000"
        assert result.confidence >= 0.95  # May be boosted by multi-method agreement
        assert result.classification_method == "vendor_database"
        mock_vs.match_vendor.assert_called_once_with("ACME Lumber", "t1")

    @pytest.mark.asyncio
    async def test_db_vendor_no_gl_falls_back(self, gl_service_with_vendor):
        """Vendor found but no default_gl_account → fall back to hardcoded."""
        service, mock_vs = gl_service_with_vendor
        mock_vs.match_vendor.return_value = {
            "id": "v2",
            "name": "Home Depot",
            "default_gl_account": None,
        }
        result = await service.classify_document_text(
            "invoice for materials", vendor_name="Home Depot"
        )
        assert result.gl_account_code == "5000"
        assert result.classification_method == "vendor_mapping"

    @pytest.mark.asyncio
    async def test_db_vendor_not_found_falls_back(self, gl_service_with_vendor):
        """Vendor not in DB → fall back to hardcoded mapping."""
        service, mock_vs = gl_service_with_vendor
        mock_vs.match_vendor.return_value = None
        result = await service.classify_document_text(
            "SDGE electric", vendor_name="SDGE"
        )
        assert result.gl_account_code == "6600"
        assert result.classification_method == "vendor_mapping"

    @pytest.mark.asyncio
    async def test_no_vendor_service_falls_back(self):
        """With no vendor_service, classification uses hardcoded only."""
        service = GLAccountService()
        await service.initialize()
        result = await service.classify_document_text(
            "materials", vendor_name="Home Depot"
        )
        assert result.gl_account_code == "5000"
        assert result.classification_method == "vendor_mapping"

    @pytest.mark.asyncio
    async def test_db_error_falls_back(self, gl_service_with_vendor):
        """If VendorService raises, fall back gracefully to hardcoded."""
        service, mock_vs = gl_service_with_vendor
        mock_vs.match_vendor.side_effect = RuntimeError("DB down")
        result = await service.classify_document_text(
            "invoice", vendor_name="Home Depot"
        )
        assert result.gl_account_code == "5000"
        assert result.classification_method == "vendor_mapping"

    @pytest.mark.asyncio
    async def test_tenant_isolation_in_gl_classification(self, gl_service_with_vendor):
        """tenant_id is passed through to match_vendor."""
        service, mock_vs = gl_service_with_vendor
        mock_vs.match_vendor.return_value = None
        await service.classify_document_text(
            "invoice for pipes", vendor_name="Ferguson", tenant_id="tenant-x"
        )
        mock_vs.match_vendor.assert_called_once_with("Ferguson", "tenant-x")

    @pytest.mark.asyncio
    async def test_vendor_db_match_logged(self, gl_service_with_vendor, caplog):
        """Vendor DB match should produce a structured log entry."""
        import logging

        service, mock_vs = gl_service_with_vendor
        mock_vs.match_vendor.return_value = {
            "id": "v-log",
            "name": "Logged Vendor",
            "default_gl_account": "6600",
        }
        with caplog.at_level(logging.INFO):
            await service.classify_document_text(
                "test text", vendor_name="Logged Vendor", tenant_id="t1"
            )
        assert any("Vendor DB match" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_hardcoded_match_logged(self, caplog):
        """Hardcoded vendor match should produce a structured log entry."""
        import logging

        service = GLAccountService()
        await service.initialize()
        with caplog.at_level(logging.INFO):
            await service.classify_document_text("invoice", vendor_name="Home Depot")
        assert any("Vendor hardcoded match" in r.message for r in caplog.records)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
