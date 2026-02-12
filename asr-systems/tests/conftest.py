"""
Shared test fixtures for ASR Production Server tests.
Handles the hyphenated-directory import problem via importlib.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Optional

import pytest

# ---------------------------------------------------------------------------
# Path setup — mirrors start_server.py
# ---------------------------------------------------------------------------
_root = Path(__file__).resolve().parent.parent  # asr-systems/
_shared = _root / "shared"
_prod_server = _root / "production-server"

# Add shared + production-server to sys.path so absolute imports work
for p in (_shared, _prod_server, _root):
    _p = str(p)
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _register_package(dotted_name: str, directory: Path) -> None:
    """Register a directory as a Python package in sys.modules."""
    init = directory / "__init__.py"
    if not init.exists():
        return
    spec = importlib.util.spec_from_file_location(
        dotted_name,
        str(init),
        submodule_search_locations=[str(directory)],
    )
    if spec is None:
        return
    mod = importlib.util.module_from_spec(spec)
    sys.modules[dotted_name] = mod


# Register production_server as a package so "from production_server.*" works
_register_package("production_server", _prod_server)
for sub in ("config", "api", "services", "middleware", "models", "utils"):
    sub_dir = _prod_server / sub
    if sub_dir.exists():
        _register_package(f"production_server.{sub}", sub_dir)


# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------
from shared.core.models import BillingDestination  # noqa: E402
from shared.core.models import (
    DocumentMetadata,
    PaymentConsensusResult,
    PaymentDetectionMethod,
    PaymentStatus,
)


@pytest.fixture
def make_consensus():
    """Factory: build a PaymentConsensusResult with sensible defaults."""

    def _make(
        status: PaymentStatus = PaymentStatus.PAID,
        confidence: float = 0.85,
        consensus_reached: bool = True,
        quality_score: float = 0.8,
    ) -> PaymentConsensusResult:
        return PaymentConsensusResult(
            payment_status=status,
            confidence=confidence,
            methods_used=[PaymentDetectionMethod.REGEX_PATTERNS],
            method_results={},
            quality_score=quality_score,
            consensus_reached=consensus_reached,
        )

    return _make


@pytest.fixture
def make_context():
    """Factory: build a DocumentContext for billing router tests."""
    from services.billing_router_service import DocumentContext

    def _make(
        document_type: Optional[str] = "vendor_invoice",
        payment_status: PaymentStatus = PaymentStatus.UNPAID,
        gl_account: Optional[str] = "5000",
        amount: Optional[float] = 1500.00,
        vendor_name: Optional[str] = "Test Vendor",
        tenant_id: str = "test-tenant",
        consensus_reached: bool = True,
        confidence: float = 0.85,
        quality_score: float = 0.8,
    ) -> DocumentContext:
        consensus = PaymentConsensusResult(
            payment_status=payment_status,
            confidence=confidence,
            methods_used=[PaymentDetectionMethod.REGEX_PATTERNS],
            method_results={},
            quality_score=quality_score,
            consensus_reached=consensus_reached,
        )
        return DocumentContext(
            document_id="test-doc-001",
            document_type=document_type,
            vendor_name=vendor_name,
            amount=amount,
            payment_consensus=consensus,
            gl_account=gl_account,
            tenant_id=tenant_id,
        )

    return _make
