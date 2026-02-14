"""
ASR Production Server - Dashboard Metrics API
Aggregates storage data into dashboard-friendly shapes consumed by the frontend.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["System"])


class DashboardService:
    """Queries the local storage layer and returns aggregated metrics."""

    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _iter_metadata(self) -> List[Dict[str, Any]]:
        """Yield all metadata dicts from disk."""
        results: List[Dict[str, Any]] = []
        metadata_dir = self.base_path / "metadata"
        if not metadata_dir.exists():
            return results
        for meta_file in metadata_dir.glob("**/*.json"):
            try:
                with meta_file.open("r") as f:
                    results.append(json.load(f))
            except Exception:
                continue
        return results

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_kpis(self) -> Dict[str, Any]:
        """Return dashboard KPI metrics."""
        docs = self._iter_metadata()
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total = len(docs)
        this_month = sum(
            1
            for d in docs
            if d.get("stored_at")
            and datetime.fromisoformat(d["stored_at"]) >= month_start
        )

        return {
            "totalDocuments": total,
            "documentsThisMonth": this_month,
            "documentsTrend": {
                "value": this_month,
                "direction": "up" if this_month > 0 else "down",
                "period": "month",
                "isPositive": this_month > 0,
            },
            "paymentAccuracy": 0,
            "paymentAccuracyTrend": {
                "value": 0,
                "direction": "up",
                "period": "month",
                "isPositive": True,
            },
            "glAccountsUsed": 0,
            "totalGLAccounts": 79,
            "classificationAccuracy": 0,
            "totalAmountProcessed": 0,
            "averageProcessingTime": 0,
            "manualReviewRate": 0,
            "processingTimeTrend": {
                "value": 0,
                "direction": "up",
                "period": "month",
                "isPositive": True,
            },
            "openPayable": 0,
            "closedPayable": 0,
            "openReceivable": 0,
            "closedReceivable": 0,
            "recentDocuments": [
                {
                    "id": d.get("document_id", ""),
                    "filename": d.get("filename", ""),
                    "vendor": "",
                    "amount": 0,
                    "status": "unknown",
                    "glAccount": "",
                    "confidence": 0,
                    "processedAt": d.get("stored_at", ""),
                    "billingDestination": "open_payable",
                }
                for d in sorted(
                    docs,
                    key=lambda x: x.get("stored_at", ""),
                    reverse=True,
                )[:10]
            ],
        }

    def get_trends(self, period: str = "30d") -> Dict[str, Any]:
        """Return document trend data for the requested period."""
        days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)
        now = datetime.utcnow()
        start = now - timedelta(days=days)
        docs = self._iter_metadata()

        buckets: Dict[str, int] = defaultdict(int)
        for d in docs:
            stored = d.get("stored_at")
            if not stored:
                continue
            dt = datetime.fromisoformat(stored)
            if dt >= start:
                buckets[dt.strftime("%Y-%m-%d")] += 1

        documents = []
        for i in range(days):
            day = (start + timedelta(days=i + 1)).strftime("%Y-%m-%d")
            total = buckets.get(day, 0)
            documents.append(
                {"date": day, "total": total, "classified": total, "manualReview": 0}
            )

        return {
            "period": period,
            "documents": documents,
            "amounts": [],
            "accuracy": [],
        }

    def get_payment_status_distribution(self) -> Dict[str, Any]:
        """Return payment status distribution."""
        docs = self._iter_metadata()
        total = max(len(docs), 1)
        return {
            "distribution": [
                {
                    "status": "unknown",
                    "count": len(docs),
                    "percentage": round(len(docs) / total * 100, 1),
                    "totalAmount": 0,
                }
            ],
            "trends": [],
        }

    def get_gl_account_usage(self) -> Dict[str, Any]:
        """Return GL account usage statistics."""
        return {"accounts": [], "categories": []}

    def get_vendor_metrics(self) -> Dict[str, Any]:
        """Return vendor analytics."""
        return {"topVendors": [], "vendorGrowth": []}

    def get_executive_summary(self) -> Dict[str, Any]:
        """Return executive summary."""
        docs = self._iter_metadata()
        return {
            "totalDocumentsProcessed": len(docs),
            "totalValueProcessed": 0,
            "averageProcessingTime": 0,
            "overallAccuracy": 0,
            "paymentDetectionAccuracy": 0,
            "glClassificationAccuracy": 0,
            "manualReviewRate": 0,
            "monthlyGrowth": {"documents": 0, "value": 0, "vendors": 0},
            "topGLAccounts": [],
            "topVendors": [],
            "alerts": [],
        }

    def get_processing_accuracy(self) -> Dict[str, Any]:
        """Return processing accuracy data."""
        return {
            "overall": {"accuracy": 0, "confidenceScores": []},
            "methods": [],
            "trends": [],
        }

    def get_billing_destination_metrics(self) -> Dict[str, Any]:
        """Return billing destination analytics."""
        return {
            "destinations": [],
            "routing": {
                "automaticRouting": 0,
                "manualOverrides": 0,
                "routingAccuracy": 0,
            },
            "trends": [],
        }


# ------------------------------------------------------------------
# Module-level service (set by register_dashboard_routes)
# ------------------------------------------------------------------
_service: Optional[DashboardService] = None


def register_dashboard_routes(app: Any, base_path: Path) -> None:
    """Register dashboard routes on the FastAPI app."""
    global _service
    _service = DashboardService(base_path)
    app.include_router(router)


# ------------------------------------------------------------------
# Route definitions — match what MetricsService.ts calls
# ------------------------------------------------------------------


@router.get("/metrics/kpis")
async def get_kpis() -> Dict[str, Any]:
    if _service is None:
        return {}
    return _service.get_kpis()


@router.get("/metrics/trends")
async def get_trends(period: str = "30d") -> Dict[str, Any]:
    if _service is None:
        return {}
    return _service.get_trends(period)


@router.get("/metrics/payment-status")
async def get_payment_status() -> Dict[str, Any]:
    if _service is None:
        return {}
    return _service.get_payment_status_distribution()


@router.get("/metrics/gl-accounts")
async def get_gl_accounts() -> Dict[str, Any]:
    if _service is None:
        return {}
    return _service.get_gl_account_usage()


@router.get("/metrics/vendors")
async def get_vendor_metrics() -> Dict[str, Any]:
    if _service is None:
        return {}
    return _service.get_vendor_metrics()


@router.get("/metrics/executive")
async def get_executive_summary() -> Dict[str, Any]:
    if _service is None:
        return {}
    return _service.get_executive_summary()


@router.get("/metrics/accuracy")
async def get_processing_accuracy() -> Dict[str, Any]:
    if _service is None:
        return {}
    return _service.get_processing_accuracy()


@router.get("/metrics/billing-destinations")
async def get_billing_destinations() -> Dict[str, Any]:
    if _service is None:
        return {}
    return _service.get_billing_destination_metrics()


@router.get("/metrics/aging")
async def get_aging() -> Dict[str, Any]:
    if _service is None:
        return {}
    return {"buckets": [], "summary": {}}
