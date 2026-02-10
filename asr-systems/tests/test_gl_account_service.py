"""
Unit Tests for GL Account Service
Comprehensive testing of 69 QuickBooks GL accounts and classification methods
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
        assert len(gl_service.gl_accounts) == 69
        assert len(gl_service.keyword_index) > 0
        assert len(gl_service.category_index) == 5

    @pytest.mark.asyncio
    async def test_all_79_accounts_loaded(self, gl_service):
        """Test that all 79 GL accounts are properly loaded"""
        accounts = gl_service.get_all_accounts()
        assert len(accounts) == 69

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
        assert result.classification_method == "pattern_matching"

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


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
