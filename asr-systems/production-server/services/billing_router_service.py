"""
ASR Production Server - Billing Router Service
Sophisticated routing to 4 billing destinations with comprehensive audit trails:
1. Open Payable (unpaid vendor invoices)
2. Closed Payable (paid vendor invoices)
3. Open Receivable (unpaid customer invoices)
4. Closed Receivable (paid customer invoices)
"""

from __future__ import annotations

import logging
import asyncio
from typing import TYPE_CHECKING, Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

# Import shared components
from shared.core.models import (
    BillingDestination, PaymentStatus, RoutingDecision, AuditTrailEntry,
    PaymentConsensusResult
)
from shared.core.constants import BILLING_DESTINATION_RULES, CONFIDENCE_THRESHOLDS
from shared.core.exceptions import RoutingError, ValidationError

if TYPE_CHECKING:
    from .audit_trail_service import AuditTrailService

logger = logging.getLogger(__name__)


@dataclass
class RoutingAnalysis:
    """Analysis result for routing decision"""
    destination: BillingDestination
    confidence: float
    reasoning: str
    factors: Dict[str, Any]
    fallback_used: bool = False


@dataclass
class DocumentContext:
    """Document context for routing analysis"""
    document_id: str
    document_type: Optional[str] = None
    vendor_name: Optional[str] = None
    customer_name: Optional[str] = None
    amount: Optional[float] = None
    payment_consensus: Optional[PaymentConsensusResult] = None
    gl_account: Optional[str] = None
    tenant_id: str = ""


class BillingRouterService:
    """
    Sophisticated billing router service with 4-destination routing and audit trails
    """

    def __init__(
        self,
        enabled_destinations: List[str],
        confidence_threshold: float,
        audit_trail_service: Optional[AuditTrailService] = None,
    ):
        self.enabled_destinations = [BillingDestination(dest) for dest in enabled_destinations]
        self.confidence_threshold = confidence_threshold
        self.audit_trail_service = audit_trail_service
        self.routing_rules = self._load_routing_rules()
        self.routing_stats = {}
        self.initialized = False

    async def initialize(self):
        """Initialize billing router service"""
        try:
            logger.info("Initializing Billing Router Service...")

            # Validate destinations
            self._validate_destinations()

            # Initialize routing statistics
            self._initialize_stats()

            self.initialized = True

            logger.info(f"✅ Billing Router Service initialized:")
            logger.info(f"   • {len(self.enabled_destinations)} destinations enabled")
            logger.info(f"   • Confidence threshold: {self.confidence_threshold}")
            logger.info(f"   • Audit trails: ✅")
            logger.info(f"   • Routing rules: {len(self.routing_rules)} configured")

        except Exception as e:
            logger.error(f"Failed to initialize Billing Router Service: {e}")
            raise RoutingError(f"Billing router service initialization failed: {e}")

    def _load_routing_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load and enhance routing rules"""
        rules = BILLING_DESTINATION_RULES.copy()

        # Add enhanced routing logic
        enhanced_rules = {
            BillingDestination.OPEN_PAYABLE: {
                "description": "Unpaid vendor invoices and bills",
                "criteria": {
                    "payment_status": [PaymentStatus.UNPAID, PaymentStatus.UNKNOWN],
                    "document_type": ["vendor_invoice", "bill", "purchase_order", "expense"],
                    "gl_account_categories": ["EXPENSES"],
                    "keywords": ["invoice", "bill", "due", "payment terms", "vendor", "supplier"],
                    "amount_threshold": 0.01  # Minimum amount to be considered
                },
                "priority": 1
            },
            BillingDestination.CLOSED_PAYABLE: {
                "description": "Paid vendor invoices and bills",
                "criteria": {
                    "payment_status": [PaymentStatus.PAID, PaymentStatus.VOID],
                    "document_type": ["vendor_invoice", "bill", "receipt", "paid_invoice"],
                    "gl_account_categories": ["EXPENSES"],
                    "keywords": ["paid", "receipt", "check", "payment received", "settled"],
                    "amount_threshold": 0.0
                },
                "priority": 2
            },
            BillingDestination.OPEN_RECEIVABLE: {
                "description": "Unpaid customer invoices",
                "criteria": {
                    "payment_status": [PaymentStatus.UNPAID, PaymentStatus.UNKNOWN],
                    "document_type": ["customer_invoice", "sales_invoice", "ar_invoice"],
                    "gl_account_categories": ["REVENUE", "ASSETS"],
                    "keywords": ["customer", "sales", "invoice", "receivable", "due from"],
                    "amount_threshold": 0.01
                },
                "priority": 3
            },
            BillingDestination.CLOSED_RECEIVABLE: {
                "description": "Paid customer invoices",
                "criteria": {
                    "payment_status": [PaymentStatus.PAID, PaymentStatus.VOID],
                    "document_type": ["customer_invoice", "sales_invoice", "paid_invoice"],
                    "gl_account_categories": ["REVENUE", "ASSETS"],
                    "keywords": ["customer payment", "payment received", "deposit", "cash receipt"],
                    "amount_threshold": 0.0
                },
                "priority": 4
            }
        }

        return enhanced_rules

    def _validate_destinations(self):
        """Validate that all required destinations are enabled"""
        required_destinations = {
            BillingDestination.OPEN_PAYABLE,
            BillingDestination.CLOSED_PAYABLE,
            BillingDestination.OPEN_RECEIVABLE,
            BillingDestination.CLOSED_RECEIVABLE
        }

        enabled_set = set(self.enabled_destinations)

        if not required_destinations.issubset(enabled_set):
            missing = required_destinations - enabled_set
            raise RoutingError(f"Required destinations not enabled: {[d.value for d in missing]}")

    def _initialize_stats(self):
        """Initialize routing statistics tracking"""
        for destination in self.enabled_destinations:
            self.routing_stats[destination] = {
                "total_routed": 0,
                "avg_confidence": 0.0,
                "last_routed": None,
                "manual_overrides": 0
            }

    def get_available_destinations(self) -> List[str]:
        """Get list of available routing destinations"""
        return [dest.value for dest in self.enabled_destinations]

    async def route_document(
        self,
        context: DocumentContext,
        user_override: Optional[BillingDestination] = None,
        user_id: Optional[str] = None
    ) -> RoutingDecision:
        """
        Route document to appropriate billing destination with comprehensive analysis

        Args:
            context: Document context with payment status and metadata
            user_override: Manual override destination (if any)
            user_id: User making manual override (if applicable)

        Returns:
            RoutingDecision with destination, confidence, and audit trail
        """
        if not self.initialized:
            raise RoutingError("Billing router service not initialized")

        try:
            logger.debug(f"Routing document {context.document_id}...")

            # Handle manual override
            if user_override:
                return await self._handle_manual_override(context, user_override, user_id)

            # Perform sophisticated routing analysis
            analysis = await self._analyze_routing_options(context)

            # Validate routing confidence
            if analysis.confidence < self.confidence_threshold:
                logger.warning(f"Routing confidence {analysis.confidence:.2f} below threshold {self.confidence_threshold}")
                # Route to manual review or default destination
                analysis = await self._handle_low_confidence_routing(context, analysis)

            # Create routing decision
            decision = RoutingDecision(
                document_id=context.document_id,
                destination=analysis.destination,
                confidence=analysis.confidence,
                reasoning=analysis.reasoning,
                factors=analysis.factors,
                manual_override=False
            )

            # Update statistics
            await self._update_routing_stats(analysis.destination, analysis.confidence)

            # Create audit trail
            await self._create_audit_trail(context, decision, analysis)

            logger.info(f"Document {context.document_id} routed to {analysis.destination.value} "
                       f"(confidence: {analysis.confidence:.2f})")

            return decision

        except Exception as e:
            logger.error(f"Routing error for document {context.document_id}: {e}")
            raise RoutingError(f"Failed to route document: {e}")

    async def _analyze_routing_options(self, context: DocumentContext) -> RoutingAnalysis:
        """Analyze all routing options and select the best match"""
        destination_scores = {}

        for destination in self.enabled_destinations:
            score = await self._calculate_destination_score(context, destination)
            destination_scores[destination] = score

        # Select best destination
        best_destination = max(destination_scores.items(), key=lambda x: x[1]["total_score"])
        destination = best_destination[0]
        score_data = best_destination[1]

        return RoutingAnalysis(
            destination=destination,
            confidence=score_data["confidence"],
            reasoning=score_data["reasoning"],
            factors=score_data["factors"],
            fallback_used=False
        )

    async def _calculate_destination_score(
        self,
        context: DocumentContext,
        destination: BillingDestination
    ) -> Dict[str, Any]:
        """Calculate score for a specific destination"""
        rules = self.routing_rules.get(destination, {})
        criteria = rules.get("criteria", {})

        factors = {}
        total_score = 0.0
        reasoning_parts = []

        # 1. Payment status matching (40% weight)
        payment_score = self._score_payment_status(context, criteria, factors)
        total_score += payment_score * 0.4
        if payment_score > 0:
            reasoning_parts.append(f"Payment status match ({payment_score:.2f})")

        # 2. Document type matching (25% weight)
        doc_type_score = self._score_document_type(context, criteria, factors)
        total_score += doc_type_score * 0.25
        if doc_type_score > 0:
            reasoning_parts.append(f"Document type match ({doc_type_score:.2f})")

        # 3. GL account category matching (20% weight)
        gl_score = self._score_gl_account(context, criteria, factors)
        total_score += gl_score * 0.20
        if gl_score > 0:
            reasoning_parts.append(f"GL account match ({gl_score:.2f})")

        # 4. Keyword matching (10% weight)
        keyword_score = self._score_keywords(context, criteria, factors)
        total_score += keyword_score * 0.10
        if keyword_score > 0:
            reasoning_parts.append(f"Keyword match ({keyword_score:.2f})")

        # 5. Amount validation (5% weight)
        amount_score = self._score_amount(context, criteria, factors)
        total_score += amount_score * 0.05
        if amount_score > 0:
            reasoning_parts.append(f"Amount validation ({amount_score:.2f})")

        # Calculate confidence based on score and quality
        confidence = min(0.95, total_score)

        # Boost confidence based on payment consensus quality
        if context.payment_consensus and context.payment_consensus.consensus_reached:
            confidence_boost = min(0.1, context.payment_consensus.quality_score * 0.1)
            confidence = min(0.95, confidence + confidence_boost)
            reasoning_parts.append(f"Payment consensus boost (+{confidence_boost:.2f})")

        reasoning = f"Destination: {destination.value}. " + "; ".join(reasoning_parts)

        return {
            "total_score": total_score,
            "confidence": confidence,
            "reasoning": reasoning,
            "factors": factors
        }

    def _score_payment_status(self, context: DocumentContext, criteria: Dict, factors: Dict) -> float:
        """Score based on payment status matching"""
        if not context.payment_consensus:
            factors["payment_status"] = "not_available"
            return 0.1

        payment_status = context.payment_consensus.payment_status
        expected_statuses = criteria.get("payment_status", [])

        factors["payment_status"] = payment_status.value
        factors["expected_payment_status"] = [s.value for s in expected_statuses]

        if payment_status in expected_statuses:
            # Score based on payment consensus confidence
            base_score = 0.8
            consensus_quality = context.payment_consensus.quality_score
            return min(1.0, base_score + (consensus_quality * 0.2))
        else:
            return 0.2  # Partial score for having payment info

    def _score_document_type(self, context: DocumentContext, criteria: Dict, factors: Dict) -> float:
        """Score based on document type matching"""
        if not context.document_type:
            factors["document_type"] = "not_detected"
            return 0.3  # Neutral score

        doc_type = context.document_type.lower()
        expected_types = [dt.lower() for dt in criteria.get("document_type", [])]

        factors["document_type"] = doc_type
        factors["expected_document_types"] = expected_types

        # Exact match
        if doc_type in expected_types:
            return 1.0

        # Partial matches
        for expected_type in expected_types:
            if expected_type in doc_type or doc_type in expected_type:
                return 0.7

        return 0.1

    def _score_gl_account(self, context: DocumentContext, criteria: Dict, factors: Dict) -> float:
        """Score based on GL account category matching"""
        if not context.gl_account:
            factors["gl_account"] = "not_available"
            return 0.3

        # Get GL account category from the account code
        gl_category = self._get_gl_account_category(context.gl_account)
        expected_categories = criteria.get("gl_account_categories", [])

        factors["gl_account_category"] = gl_category
        factors["expected_gl_categories"] = expected_categories

        if gl_category in expected_categories:
            return 0.9
        else:
            return 0.2

    def _score_keywords(self, context: DocumentContext, criteria: Dict, factors: Dict) -> float:
        """Score based on keyword presence in document context"""
        keywords = criteria.get("keywords", [])
        if not keywords:
            return 0.5

        # Check for keywords in various context fields
        text_to_check = []
        if context.vendor_name:
            text_to_check.append(context.vendor_name.lower())
        if context.customer_name:
            text_to_check.append(context.customer_name.lower())

        combined_text = " ".join(text_to_check)
        matched_keywords = []

        for keyword in keywords:
            if keyword.lower() in combined_text:
                matched_keywords.append(keyword)

        factors["matched_keywords"] = matched_keywords
        factors["keyword_match_ratio"] = len(matched_keywords) / len(keywords) if keywords else 0

        if matched_keywords:
            return min(1.0, len(matched_keywords) / len(keywords) + 0.3)
        else:
            return 0.3

    def _score_amount(self, context: DocumentContext, criteria: Dict, factors: Dict) -> float:
        """Score based on amount validation"""
        if not context.amount:
            factors["amount"] = "not_available"
            return 0.5

        amount_threshold = criteria.get("amount_threshold", 0.0)
        factors["amount"] = context.amount
        factors["amount_threshold"] = amount_threshold

        if context.amount >= amount_threshold:
            return 1.0
        else:
            return 0.3

    def _get_gl_account_category(self, gl_account: str) -> str:
        """Get category for GL account code"""
        # Simple mapping based on account code ranges
        if gl_account.startswith("1"):
            return "ASSETS"
        elif gl_account.startswith("2"):
            return "LIABILITIES"
        elif gl_account.startswith("3"):
            return "EQUITY"
        elif gl_account.startswith("4"):
            return "REVENUE"
        elif gl_account.startswith("5") or gl_account.startswith("6") or gl_account.startswith("7"):
            return "EXPENSES"
        else:
            return "UNKNOWN"

    async def _handle_low_confidence_routing(
        self,
        context: DocumentContext,
        original_analysis: RoutingAnalysis
    ) -> RoutingAnalysis:
        """Handle routing when confidence is below threshold"""
        logger.warning(f"Low confidence routing for document {context.document_id}")

        # Default routing based on payment status
        if context.payment_consensus:
            payment_status = context.payment_consensus.payment_status

            if payment_status == PaymentStatus.PAID:
                # Default to closed payable for paid documents
                destination = BillingDestination.CLOSED_PAYABLE
            else:
                # Default to open payable for unpaid documents
                destination = BillingDestination.OPEN_PAYABLE
        else:
            # Ultimate fallback to open payable
            destination = BillingDestination.OPEN_PAYABLE

        return RoutingAnalysis(
            destination=destination,
            confidence=max(0.5, original_analysis.confidence),  # Minimum confidence for fallback
            reasoning=f"Fallback routing due to low confidence. {original_analysis.reasoning}",
            factors=original_analysis.factors,
            fallback_used=True
        )

    async def _handle_manual_override(
        self,
        context: DocumentContext,
        destination: BillingDestination,
        user_id: Optional[str]
    ) -> RoutingDecision:
        """Handle manual routing override by user"""
        if destination not in self.enabled_destinations:
            raise RoutingError(f"Invalid destination: {destination.value}")

        decision = RoutingDecision(
            document_id=context.document_id,
            destination=destination,
            confidence=1.0,  # Manual override has full confidence
            reasoning=f"Manual override by user {user_id or 'unknown'}",
            factors={"manual_override": True, "user_id": user_id},
            manual_override=True
        )

        # Update override statistics
        self.routing_stats[destination]["manual_overrides"] += 1

        logger.info(f"Manual override: Document {context.document_id} routed to {destination.value}")

        return decision

    async def _update_routing_stats(self, destination: BillingDestination, confidence: float):
        """Update routing statistics"""
        stats = self.routing_stats[destination]
        stats["total_routed"] += 1
        stats["last_routed"] = datetime.now(timezone.utc)

        # Update average confidence
        current_avg = stats["avg_confidence"]
        total_routed = stats["total_routed"]
        new_avg = ((current_avg * (total_routed - 1)) + confidence) / total_routed
        stats["avg_confidence"] = new_avg

    async def _create_audit_trail(
        self,
        context: DocumentContext,
        decision: RoutingDecision,
        analysis: RoutingAnalysis
    ):
        """Create comprehensive audit trail entry"""
        audit_entry = AuditTrailEntry(
            document_id=context.document_id,
            event_type="billing_routing",
            event_data={
                "destination": decision.destination.value,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning,
                "factors": decision.factors,
                "routing_analysis": {
                    "fallback_used": analysis.fallback_used,
                    "confidence_threshold": self.confidence_threshold,
                    "payment_consensus": context.payment_consensus.dict() if context.payment_consensus else None
                },
                "document_context": {
                    "vendor_name": context.vendor_name,
                    "customer_name": context.customer_name,
                    "amount": context.amount,
                    "gl_account": context.gl_account,
                    "document_type": context.document_type
                }
            },
            system_component="billing_router_service",
            tenant_id=context.tenant_id
        )

        if self.audit_trail_service:
            await self.audit_trail_service.record(audit_entry)
        else:
            logger.debug(f"Audit trail created for document {context.document_id}")

    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing statistics for monitoring"""
        return {
            "destinations": dict(self.routing_stats),
            "total_routed": sum(stats["total_routed"] for stats in self.routing_stats.values()),
            "confidence_threshold": self.confidence_threshold,
            "enabled_destinations": [dest.value for dest in self.enabled_destinations]
        }

    async def cleanup(self):
        """Cleanup billing router service"""
        logger.info("Cleaning up Billing Router Service...")
        self.routing_stats.clear()
        self.initialized = False