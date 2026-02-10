"""
Unit Tests for Billing Router Service
Tests routing to 4 destinations, scoring, fallback, and statistics.
"""

import pytest

from services.billing_router_service import BillingRouterService, DocumentContext
from shared.core.models import BillingDestination, PaymentStatus


ALL_DESTINATIONS = [
    "open_payable",
    "closed_payable",
    "open_receivable",
    "closed_receivable",
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def router():
    service = BillingRouterService(ALL_DESTINATIONS, confidence_threshold=0.75)
    await service.initialize()
    return service


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

class TestInit:
    @pytest.mark.asyncio
    async def test_initialization(self, router):
        assert router.initialized is True

    @pytest.mark.asyncio
    async def test_available_destinations(self, router):
        dests = router.get_available_destinations()
        assert len(dests) == 4
        assert "open_payable" in dests


# ---------------------------------------------------------------------------
# Routing to each destination
# ---------------------------------------------------------------------------

class TestRouting:
    @pytest.mark.asyncio
    async def test_route_open_payable(self, router, make_context):
        ctx = make_context(
            document_type="vendor_invoice",
            payment_status=PaymentStatus.UNPAID,
            gl_account="5000",
        )
        decision = await router.route_document(ctx)
        assert decision.destination == BillingDestination.OPEN_PAYABLE

    @pytest.mark.asyncio
    async def test_route_closed_payable(self, router, make_context):
        ctx = make_context(
            document_type="vendor_invoice",
            payment_status=PaymentStatus.PAID,
            gl_account="5000",
        )
        decision = await router.route_document(ctx)
        assert decision.destination == BillingDestination.CLOSED_PAYABLE

    @pytest.mark.asyncio
    async def test_route_open_receivable(self, router, make_context):
        ctx = make_context(
            document_type="customer_invoice",
            payment_status=PaymentStatus.UNPAID,
            gl_account="4000",
            vendor_name=None,
        )
        ctx.customer_name = "Test Customer"
        decision = await router.route_document(ctx)
        assert decision.destination == BillingDestination.OPEN_RECEIVABLE

    @pytest.mark.asyncio
    async def test_route_closed_receivable(self, router, make_context):
        ctx = make_context(
            document_type="customer_invoice",
            payment_status=PaymentStatus.PAID,
            gl_account="4000",
            vendor_name=None,
        )
        ctx.customer_name = "Test Customer"
        decision = await router.route_document(ctx)
        assert decision.destination == BillingDestination.CLOSED_RECEIVABLE


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

class TestScoring:
    @pytest.mark.asyncio
    async def test_payment_status_scoring(self, router, make_context):
        """Matching payment status should produce higher total score."""
        ctx_match = make_context(payment_status=PaymentStatus.UNPAID, gl_account="5000")
        ctx_mismatch = make_context(payment_status=PaymentStatus.PAID, gl_account="5000")

        score_match = await router._calculate_destination_score(
            ctx_match, BillingDestination.OPEN_PAYABLE
        )
        score_mismatch = await router._calculate_destination_score(
            ctx_mismatch, BillingDestination.OPEN_PAYABLE
        )
        assert score_match["total_score"] > score_mismatch["total_score"]

    @pytest.mark.asyncio
    async def test_gl_account_category_mapping(self, router, make_context):
        """Expense GL account should score higher for payable destinations."""
        ctx_expense = make_context(gl_account="5000")
        ctx_revenue = make_context(gl_account="4000")

        score_exp = await router._calculate_destination_score(
            ctx_expense, BillingDestination.OPEN_PAYABLE
        )
        score_rev = await router._calculate_destination_score(
            ctx_revenue, BillingDestination.OPEN_PAYABLE
        )
        assert score_exp["factors"]["gl_account_category"] == "EXPENSES"
        assert score_rev["factors"]["gl_account_category"] == "REVENUE"


# ---------------------------------------------------------------------------
# Fallback routing
# ---------------------------------------------------------------------------

class TestFallback:
    @pytest.mark.asyncio
    async def test_low_confidence_triggers_fallback(self, router, make_context):
        """Documents with no clear signals get fallback routing."""
        ctx = make_context(
            document_type=None,
            payment_status=PaymentStatus.UNKNOWN,
            gl_account=None,
            amount=None,
            vendor_name=None,
            confidence=0.3,
            quality_score=0.2,
        )
        decision = await router.route_document(ctx)
        # Fallback should still produce a valid destination
        assert decision.destination in [
            BillingDestination.OPEN_PAYABLE,
            BillingDestination.CLOSED_PAYABLE,
            BillingDestination.OPEN_RECEIVABLE,
            BillingDestination.CLOSED_RECEIVABLE,
        ]
        assert decision.confidence >= 0.5  # minimum fallback confidence

    @pytest.mark.asyncio
    async def test_fallback_respects_payment_status(self, router, make_context):
        """Paid documents in fallback should go to closed destinations."""
        ctx = make_context(
            document_type=None,
            payment_status=PaymentStatus.PAID,
            gl_account=None,
            amount=None,
            vendor_name=None,
            confidence=0.3,
            quality_score=0.2,
        )
        decision = await router.route_document(ctx)
        # With PAID status, fallback defaults to CLOSED_PAYABLE
        assert decision.destination in [
            BillingDestination.CLOSED_PAYABLE,
            BillingDestination.CLOSED_RECEIVABLE,
        ]


# ---------------------------------------------------------------------------
# Statistics and override
# ---------------------------------------------------------------------------

class TestStats:
    @pytest.mark.asyncio
    async def test_manual_override(self, router, make_context):
        ctx = make_context()
        decision = await router.route_document(
            ctx,
            user_override=BillingDestination.CLOSED_RECEIVABLE,
            user_id="admin",
        )
        assert decision.destination == BillingDestination.CLOSED_RECEIVABLE
        assert decision.manual_override is True
        assert decision.confidence == 1.0

    @pytest.mark.asyncio
    async def test_routing_statistics_update(self, router, make_context):
        ctx = make_context(
            document_type="vendor_invoice",
            payment_status=PaymentStatus.UNPAID,
            gl_account="5000",
        )
        await router.route_document(ctx)
        stats = router.get_routing_statistics()
        assert stats["total_routed"] >= 1
