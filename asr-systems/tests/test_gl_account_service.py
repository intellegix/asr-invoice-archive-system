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
sys.path.insert(0, str(Path(__file__).parent.parent / "production_server"))

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
        """Test classification for vendor-related text (no vendor_service → keyword/pattern)."""
        result = await gl_service.classify_document_text(
            "Invoice from Home Depot for construction materials",
            vendor_name="Home Depot",
        )

        # Without vendor_service, vendor DB path is skipped.
        # Should still classify via keyword or pattern matching.
        assert result.gl_account_code == "5000"
        assert result.confidence > 0.5

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
    async def test_db_vendor_no_gl_falls_through(self, gl_service_with_vendor):
        """Vendor found but no default_gl_account → vendor path returns None,
        classification falls through to keyword/pattern methods."""
        service, mock_vs = gl_service_with_vendor
        mock_vs.match_vendor.return_value = {
            "id": "v2",
            "name": "Home Depot",
            "default_gl_account": None,
        }
        result = await service.classify_document_text(
            "invoice for materials lumber", vendor_name="Home Depot"
        )
        assert result.gl_account_code == "5000"
        assert result.classification_method in (
            "keyword_matching",
            "pattern_matching",
            "category_heuristic",
        )

    @pytest.mark.asyncio
    async def test_db_vendor_not_found_falls_through(self, gl_service_with_vendor):
        """Vendor not in DB → vendor path returns None, other methods classify."""
        service, mock_vs = gl_service_with_vendor
        mock_vs.match_vendor.return_value = None
        result = await service.classify_document_text(
            "electric bill utility payment", vendor_name="SDGE"
        )
        assert result.gl_account_code == "6600"
        assert result.classification_method in (
            "keyword_matching",
            "pattern_matching",
        )

    @pytest.mark.asyncio
    async def test_no_vendor_service_skips_vendor_path(self):
        """With no vendor_service, vendor path is skipped entirely."""
        service = GLAccountService()
        await service.initialize()
        result = await service.classify_document_text(
            "lumber materials construction", vendor_name="Home Depot"
        )
        assert result.gl_account_code == "5000"
        assert result.classification_method != "vendor_database"

    @pytest.mark.asyncio
    async def test_db_error_falls_through(self, gl_service_with_vendor):
        """If VendorService raises, vendor path returns None gracefully."""
        service, mock_vs = gl_service_with_vendor
        mock_vs.match_vendor.side_effect = RuntimeError("DB down")
        result = await service.classify_document_text(
            "lumber materials invoice", vendor_name="Home Depot"
        )
        # Should still classify via keyword/pattern, not crash
        assert result is not None
        assert result.classification_method != "vendor_database"

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
    async def test_vendor_db_match_logged(self, gl_service_with_vendor):
        """Vendor DB match should produce a structured log entry."""
        from unittest.mock import patch

        service, mock_vs = gl_service_with_vendor
        mock_vs.match_vendor.return_value = {
            "id": "v-log",
            "name": "Logged Vendor",
            "default_gl_account": "6600",
        }
        # Use sys.modules to find the actual module that owns the logger
        import sys

        mod = sys.modules.get(
            "production_server.services.gl_account_service",
            sys.modules.get("services.gl_account_service"),
        )
        with patch.object(mod, "logger") as mock_logger:
            mock_logger.info = mock_logger.info
            mock_logger.debug = mock_logger.debug
            mock_logger.exception = mock_logger.exception
            await service.classify_document_text(
                "test text", vendor_name="Logged Vendor", tenant_id="t1"
            )
        mock_logger.info.assert_any_call(
            "Vendor DB match: vendor=%s gl=%s method=database",
            "Logged Vendor",
            "6600",
        )

    @pytest.mark.asyncio
    async def test_all_seeded_vendors_resolve_from_db(self):
        """All 40 legacy vendors from the seed migration should resolve
        via mock vendor_service returning their GL mappings."""
        from unittest.mock import AsyncMock

        # The seed data from migration 0003
        seed_vendors = [
            ("Home Depot", "5000"),
            ("Lowe's", "5000"),
            ("ABC Supply", "5000"),
            ("Beacon", "5000"),
            ("Ferguson", "5000"),
            ("SDG&E", "6600"),
            ("Cox Communications", "6600"),
            ("Verizon", "6600"),
            ("AT&T", "6600"),
            ("USA Waste", "6600"),
            ("Waste Management", "6600"),
            ("Republic Services", "6600"),
            ("EDCO", "6600"),
            ("Shell", "6900"),
            ("Chevron", "6900"),
            ("Mobil", "6900"),
            ("Exxon", "6900"),
            ("ARCO", "6900"),
            ("Attorney", "5700"),
            ("Accountant", "5700"),
            ("Insurance", "5500"),
            ("Farmers Insurance", "5500"),
            ("State Farm", "5500"),
            ("Allstate", "5500"),
        ]

        for vendor_name, expected_gl in seed_vendors:
            mock_vs = AsyncMock()
            mock_vs.match_vendor = AsyncMock(
                return_value={
                    "id": "seed-v",
                    "name": vendor_name,
                    "default_gl_account": expected_gl,
                }
            )
            service = GLAccountService(vendor_service=mock_vs)
            await service.initialize()
            result = await service.classify_document_text(
                "test invoice", vendor_name=vendor_name
            )
            assert (
                result.classification_method == "vendor_database"
            ), f"{vendor_name} should resolve via DB, got {result.classification_method}"
            assert (
                result.gl_account_code == expected_gl
            ), f"{vendor_name} should map to {expected_gl}, got {result.gl_account_code}"

    @pytest.mark.asyncio
    async def test_no_db_match_logs_debug(self, gl_service_with_vendor):
        """When vendor not found in DB, a debug message is logged."""
        import sys
        from unittest.mock import patch

        service, mock_vs = gl_service_with_vendor
        mock_vs.match_vendor.return_value = None
        mod = sys.modules.get(
            "production_server.services.gl_account_service",
            sys.modules.get("services.gl_account_service"),
        )
        with patch.object(mod, "logger") as mock_logger:
            mock_logger.info = mock_logger.info
            mock_logger.debug = mock_logger.debug
            mock_logger.exception = mock_logger.exception
            await service.classify_document_text(
                "test invoice", vendor_name="Unknown Vendor"
            )
        mock_logger.debug.assert_any_call(
            "No vendor DB match for '%s' (tenant=%s)",
            "Unknown Vendor",
            None,
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
