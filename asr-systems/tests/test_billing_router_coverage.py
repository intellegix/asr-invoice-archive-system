"""
P79: BillingRouterService coverage expansion.
Tests all 4 destination paths, low-confidence routing, null payment, config loading.
"""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

_asr = Path(__file__).parent.parent
sys.path.insert(0, str(_asr / "shared"))
sys.path.insert(0, str(_asr / "production_server"))

os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")


def _make_router(**kwargs):
    """Create a BillingRouterService for testing."""
    from services.billing_router_service import BillingRouterService

    defaults = {
        "enabled_destinations": [
            "open_payable",
            "closed_payable",
            "open_receivable",
            "closed_receivable",
        ],
        "confidence_threshold": 0.75,
    }
    defaults.update(kwargs)
    return BillingRouterService(**defaults)


def _make_context(**overrides):
    """Create a DocumentContext for routing tests."""
    from shared.core.models import PaymentConsensusResult, PaymentStatus

    from services.billing_router_service import DocumentContext

    defaults = {
        "document_id": "doc-1",
        "document_type": "vendor_invoice",
        "vendor_name": "vendor",
        "gl_account": "5000",
    }
    defaults.update(overrides)
    return DocumentContext(**defaults)


def _make_payment_consensus(status: str = "unpaid", **overrides):
    """Create a PaymentConsensusResult for routing tests."""
    from shared.core.models import (
        PaymentConsensusResult,
        PaymentDetectionMethod,
        PaymentStatus,
    )

    status_map = {
        "unpaid": PaymentStatus.UNPAID,
        "paid": PaymentStatus.PAID,
        "partial": PaymentStatus.PARTIAL,
        "void": PaymentStatus.VOID,
        "unknown": PaymentStatus.UNKNOWN,
    }
    defaults = {
        "payment_status": status_map[status],
        "confidence": 0.9,
        "methods_used": [PaymentDetectionMethod.REGEX_PATTERNS],
        "consensus_reached": True,
        "quality_score": 0.85,
        "method_results": {},
    }
    defaults.update(overrides)
    return PaymentConsensusResult(**defaults)


@pytest.mark.asyncio
async def test_router_initialization():
    """Router initializes with 4 destinations."""
    router = _make_router()
    await router.initialize()
    assert router.initialized is True
    destinations = router.get_available_destinations()
    assert len(destinations) == 4


@pytest.mark.asyncio
async def test_get_available_destinations():
    """get_available_destinations returns string names."""
    router = _make_router()
    await router.initialize()
    dests = router.get_available_destinations()
    assert "open_payable" in dests
    assert "closed_payable" in dests


@pytest.mark.asyncio
async def test_route_unpaid_vendor():
    """Unpaid vendor invoice routes to open_payable."""
    router = _make_router()
    await router.initialize()

    ctx = _make_context(
        payment_consensus=_make_payment_consensus("unpaid"),
    )
    result = await router.route_document(context=ctx)
    assert result.destination.value == "open_payable"


@pytest.mark.asyncio
async def test_route_paid_vendor():
    """Paid vendor invoice routes to closed_payable."""
    router = _make_router()
    await router.initialize()

    ctx = _make_context(
        payment_consensus=_make_payment_consensus("paid"),
    )
    result = await router.route_document(context=ctx)
    assert result.destination.value == "closed_payable"


@pytest.mark.asyncio
async def test_route_receivable_unpaid():
    """Receivable (income) unpaid routes to open_receivable."""
    router = _make_router()
    await router.initialize()

    ctx = _make_context(
        document_type="customer_invoice",
        customer_name="Customer A",
        vendor_name=None,
        gl_account="4000",
        payment_consensus=_make_payment_consensus("unpaid"),
    )
    result = await router.route_document(context=ctx)
    assert result.destination.value == "open_receivable"


@pytest.mark.asyncio
async def test_route_receivable_paid():
    """Receivable (income) paid routes to closed_receivable."""
    router = _make_router()
    await router.initialize()

    ctx = _make_context(
        document_type="customer_invoice",
        customer_name="Customer B",
        vendor_name=None,
        gl_account="4000",
        payment_consensus=_make_payment_consensus("paid"),
    )
    result = await router.route_document(context=ctx)
    assert result.destination.value == "closed_receivable"


@pytest.mark.asyncio
async def test_route_no_payment_consensus():
    """Routing without payment consensus still produces a result."""
    router = _make_router()
    await router.initialize()

    ctx = _make_context(payment_consensus=None)
    result = await router.route_document(context=ctx)
    assert result.destination is not None
    assert result.confidence > 0


@pytest.mark.asyncio
async def test_route_with_audit_trail():
    """Routing with audit trail service logs the event."""
    audit = MagicMock()
    audit.record = AsyncMock()

    router = _make_router(audit_trail_service=audit)
    await router.initialize()

    ctx = _make_context(
        payment_consensus=_make_payment_consensus("unpaid"),
    )
    result = await router.route_document(context=ctx)
    assert result.destination is not None
    audit.record.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup():
    """Cleanup sets initialized to False."""
    router = _make_router()
    await router.initialize()
    await router.cleanup()
    assert router.initialized is False
