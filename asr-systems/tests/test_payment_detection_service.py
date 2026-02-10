"""
Unit Tests for Payment Detection Service
Tests the 3 deterministic methods (regex, keywords, amount) + consensus.
Claude API methods are excluded — no network calls.
"""

import pytest
from shared.core.models import PaymentDetectionMethod, PaymentStatus

from services.payment_detection_service import MethodResult, PaymentDetectionService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def pds():
    """Payment Detection Service with only deterministic methods enabled."""
    service = PaymentDetectionService(
        claude_config={"enabled": False, "api_key": None},
        enabled_methods=[
            "regex_patterns",
            "keyword_matching",
            "amount_analysis",
        ],
    )
    await service.initialize()
    return service


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestInit:
    @pytest.mark.asyncio
    async def test_initialization(self, pds):
        assert pds.initialized is True

    @pytest.mark.asyncio
    async def test_enabled_methods(self, pds):
        methods = pds.get_enabled_methods()
        assert PaymentDetectionMethod.REGEX_PATTERNS in methods
        assert PaymentDetectionMethod.KEYWORD_MATCHING in methods
        assert PaymentDetectionMethod.AMOUNT_ANALYSIS in methods
        assert PaymentDetectionMethod.CLAUDE_VISION not in methods


# ---------------------------------------------------------------------------
# Regex pattern detection
# ---------------------------------------------------------------------------


class TestRegex:
    @pytest.mark.asyncio
    async def test_detect_paid(self, pds):
        result = await pds._detect_regex_patterns("PAID IN FULL check #12345")
        assert result.payment_status == PaymentStatus.PAID
        assert result.confidence >= 0.6

    @pytest.mark.asyncio
    async def test_detect_unpaid(self, pds):
        result = await pds._detect_regex_patterns("Balance due: $1,250.00 please remit")
        assert result.payment_status == PaymentStatus.UNPAID
        assert result.confidence >= 0.5

    @pytest.mark.asyncio
    async def test_detect_void(self, pds):
        result = await pds._detect_regex_patterns("VOID VOID VOID cancelled invoice")
        assert result.payment_status == PaymentStatus.VOID
        assert result.confidence >= 0.7


# ---------------------------------------------------------------------------
# Keyword detection
# ---------------------------------------------------------------------------


class TestKeywords:
    @pytest.mark.asyncio
    async def test_detect_paid(self, pds):
        result = await pds._detect_keywords("payment received settled cleared check")
        assert result.payment_status == PaymentStatus.PAID
        assert result.confidence >= 0.5

    @pytest.mark.asyncio
    async def test_detect_unpaid(self, pds):
        result = await pds._detect_keywords("outstanding balance due overdue past due")
        assert result.payment_status == PaymentStatus.UNPAID
        assert result.confidence >= 0.4

    @pytest.mark.asyncio
    async def test_detect_unknown(self, pds):
        result = await pds._detect_keywords(
            "some random text with no payment indicators"
        )
        assert result.payment_status == PaymentStatus.UNKNOWN
        assert result.confidence <= 0.3


# ---------------------------------------------------------------------------
# Amount analysis
# ---------------------------------------------------------------------------


class TestAmountAnalysis:
    @pytest.mark.asyncio
    async def test_zero_balance_is_paid(self, pds):
        result = await pds._detect_amount_analysis("Balance due: $0.00", None)
        assert result.payment_status == PaymentStatus.PAID
        assert result.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_nonzero_amount_is_unpaid(self, pds):
        result = await pds._detect_amount_analysis("Total due: $4,500.00", None)
        assert result.payment_status == PaymentStatus.UNPAID
        assert result.confidence >= 0.5

    @pytest.mark.asyncio
    async def test_amount_info_unpaid(self, pds):
        """amount_info with nonzero amount_due should return UNPAID."""
        result = await pds._detect_amount_analysis(
            "invoice text",
            {"amount_due": 500.00},
        )
        assert result.payment_status == PaymentStatus.UNPAID
        assert result.confidence >= 0.6


# ---------------------------------------------------------------------------
# Consensus
# ---------------------------------------------------------------------------


class TestConsensus:
    def test_agreement_boosts_confidence(self, pds):
        results = [
            MethodResult(
                method=PaymentDetectionMethod.REGEX_PATTERNS,
                payment_status=PaymentStatus.PAID,
                confidence=0.7,
                reasoning="test",
                details={},
                processing_time=0.0,
            ),
            MethodResult(
                method=PaymentDetectionMethod.KEYWORD_MATCHING,
                payment_status=PaymentStatus.PAID,
                confidence=0.7,
                reasoning="test",
                details={},
                processing_time=0.0,
            ),
        ]
        consensus = pds._calculate_consensus(results)
        assert consensus.payment_status == PaymentStatus.PAID
        # Agreement boost: mean(0.7, 0.7) + 0.1 = ~0.8
        assert consensus.confidence == pytest.approx(0.8, abs=0.01)

    def test_disagreement_resolves_to_majority(self, pds):
        results = [
            MethodResult(
                method=PaymentDetectionMethod.REGEX_PATTERNS,
                payment_status=PaymentStatus.PAID,
                confidence=0.8,
                reasoning="",
                details={},
                processing_time=0.0,
            ),
            MethodResult(
                method=PaymentDetectionMethod.KEYWORD_MATCHING,
                payment_status=PaymentStatus.PAID,
                confidence=0.7,
                reasoning="",
                details={},
                processing_time=0.0,
            ),
            MethodResult(
                method=PaymentDetectionMethod.AMOUNT_ANALYSIS,
                payment_status=PaymentStatus.UNPAID,
                confidence=0.6,
                reasoning="",
                details={},
                processing_time=0.0,
            ),
        ]
        consensus = pds._calculate_consensus(results)
        assert consensus.payment_status == PaymentStatus.PAID
