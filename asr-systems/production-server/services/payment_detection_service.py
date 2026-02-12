"""
ASR Production Server - Payment Detection Service
Sophisticated 5-method consensus system for payment status detection:
1. Claude Vision Analysis
2. Claude Text Analysis
3. Regex Pattern Matching
4. Keywords Detection
5. Amount Analysis
"""

import asyncio
import logging
import re
import statistics
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from shared.core.constants import CONFIDENCE_THRESHOLDS, PAYMENT_INDICATORS
from shared.core.exceptions import CLAUDEAPIError, PaymentDetectionError

# Import shared components
from shared.core.models import (
    PaymentConsensusResult,
    PaymentDetectionMethod,
    PaymentStatus,
)

logger = logging.getLogger(__name__)


@dataclass
class MethodResult:
    """Result from individual detection method"""

    method: PaymentDetectionMethod
    payment_status: PaymentStatus
    confidence: float
    reasoning: str
    details: Dict[str, Any]
    processing_time: float


class PaymentDetectionService:
    """
    Sophisticated payment detection service using 5-method consensus
    """

    def __init__(self, claude_config: Dict[str, Any], enabled_methods: List[str]):
        self.claude_config = claude_config
        self.enabled_methods = [
            PaymentDetectionMethod(method) for method in enabled_methods
        ]
        self.initialized = False

        # Pattern compilations for efficiency
        self.paid_patterns = []
        self.unpaid_patterns = []
        self.partial_patterns = []
        self.void_patterns = []

        # Claude client (will be initialized if available)
        self.claude_client = None

    async def initialize(self):
        """Initialize payment detection service"""
        try:
            logger.info("Initializing Payment Detection Service...")

            # Compile regex patterns for efficiency
            self._compile_patterns()

            # Initialize Claude AI client if available
            if self.claude_config.get("enabled") and self.claude_config.get("api_key"):
                await self._initialize_claude_client()

            self.initialized = True

            logger.info(f"✅ Payment Detection Service initialized:")
            logger.info(f"   • {len(self.enabled_methods)} detection methods enabled")
            logger.info(f"   • Claude AI: {'✅' if self.claude_client else '❌'}")
            logger.info(f"   • Pattern matching: ✅")
            logger.info(f"   • Keyword detection: ✅")
            logger.info(f"   • Amount analysis: ✅")

        except Exception as e:
            logger.error(f"Failed to initialize Payment Detection Service: {e}")
            raise PaymentDetectionError(
                f"Payment detection service initialization failed: {e}"
            )

    def _compile_patterns(self):
        """Compile regex patterns for payment detection"""
        # Paid patterns
        paid_keywords = PAYMENT_INDICATORS["PAID_KEYWORDS"]
        self.paid_patterns = [
            re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
            for keyword in paid_keywords
        ]

        # Additional sophisticated paid patterns
        self.paid_patterns.extend(
            [
                re.compile(
                    r"\b(?:balance|amount)\s+(?:due|owed)?\s*:?\s*\$?0+\.?0*\b",
                    re.IGNORECASE,
                ),
                re.compile(r"\bzero\s+balance\b", re.IGNORECASE),
                re.compile(r"\bpaid\s+in\s+full\b", re.IGNORECASE),
                re.compile(r"\bcheck\s+#?\d+\b", re.IGNORECASE),
                re.compile(r"\bref\s*#?\s*\d+\b", re.IGNORECASE),
            ]
        )

        # Unpaid patterns
        unpaid_keywords = PAYMENT_INDICATORS["UNPAID_KEYWORDS"]
        self.unpaid_patterns = [
            re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
            for keyword in unpaid_keywords
        ]

        # Additional sophisticated unpaid patterns
        self.unpaid_patterns.extend(
            [
                re.compile(
                    r"\b(?:balance|amount)\s+(?:due|owed)\s*:?\s*\$?[1-9]\d*(?:\.\d{2})?\b",
                    re.IGNORECASE,
                ),
                re.compile(
                    r"\btotal\s+due\s*:?\s*\$?[1-9]\d*(?:\.\d{2})?\b", re.IGNORECASE
                ),
                re.compile(r"\bdue\s+date\b", re.IGNORECASE),
                re.compile(r"\bplease\s+remit\b", re.IGNORECASE),
            ]
        )

        # Partial payment patterns
        partial_keywords = PAYMENT_INDICATORS["PARTIAL_KEYWORDS"]
        self.partial_patterns = [
            re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
            for keyword in partial_keywords
        ]

        # Void patterns
        void_keywords = PAYMENT_INDICATORS["VOID_KEYWORDS"]
        self.void_patterns = [
            re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
            for keyword in void_keywords
        ]

    async def _initialize_claude_client(self):
        """Initialize Claude AI client"""
        try:
            import anthropic

            self.claude_client = anthropic.AsyncAnthropic(
                api_key=self.claude_config["api_key"]
            )
            logger.info("✅ Claude AI client initialized")
        except ImportError:
            logger.warning(
                "❌ Anthropic library not available, Claude AI methods disabled"
            )
            # Remove Claude methods from enabled methods
            self.enabled_methods = [
                method
                for method in self.enabled_methods
                if method
                not in [
                    PaymentDetectionMethod.CLAUDE_VISION,
                    PaymentDetectionMethod.CLAUDE_TEXT,
                ]
            ]
        except Exception as e:
            logger.error(f"Failed to initialize Claude client: {e}")
            self.claude_client = None

    def get_enabled_methods(self) -> List[PaymentDetectionMethod]:
        """Get list of enabled detection methods"""
        return self.enabled_methods.copy()

    async def detect_payment_status(
        self,
        document_text: str,
        document_image: Optional[bytes] = None,
        amount_info: Optional[Dict[str, Any]] = None,
    ) -> PaymentConsensusResult:
        """
        Detect payment status using sophisticated 5-method consensus

        Args:
            document_text: Extracted text from document
            document_image: Document image for vision analysis (optional)
            amount_info: Amount information from document (optional)

        Returns:
            PaymentConsensusResult with consensus decision and confidence
        """
        if not self.initialized:
            raise PaymentDetectionError("Payment detection service not initialized")

        try:
            logger.debug("Starting sophisticated payment detection consensus...")

            # Run all enabled detection methods
            method_results = []

            for method in self.enabled_methods:
                try:
                    start_time = time.perf_counter()

                    if (
                        method == PaymentDetectionMethod.CLAUDE_VISION
                        and document_image
                    ):
                        result = await self._detect_claude_vision(
                            document_image, document_text
                        )
                    elif method == PaymentDetectionMethod.CLAUDE_TEXT:
                        result = await self._detect_claude_text(document_text)
                    elif method == PaymentDetectionMethod.REGEX_PATTERNS:
                        result = await self._detect_regex_patterns(document_text)
                    elif method == PaymentDetectionMethod.KEYWORD_MATCHING:
                        result = await self._detect_keywords(document_text)
                    elif method == PaymentDetectionMethod.AMOUNT_ANALYSIS:
                        result = await self._detect_amount_analysis(
                            document_text, amount_info
                        )
                    else:
                        continue  # Skip unavailable methods

                    processing_time = time.perf_counter() - start_time
                    result.processing_time = processing_time
                    method_results.append(result)

                    logger.debug(
                        f"Method {method.value}: {result.payment_status.value} (confidence: {result.confidence:.2f})"
                    )

                except Exception as e:
                    logger.warning(f"Method {method.value} failed: {e}")
                    continue

            # Calculate consensus
            consensus = self._calculate_consensus(method_results)

            logger.info(
                f"Payment detection consensus: {consensus.payment_status.value} (confidence: {consensus.confidence:.2f})"
            )

            return consensus

        except Exception as e:
            logger.error(f"Payment detection error: {e}")
            raise PaymentDetectionError(f"Failed to detect payment status: {e}")

    async def _detect_claude_vision(
        self, document_image: bytes, document_text: str
    ) -> MethodResult:
        """Detect payment status using Claude Vision"""
        if not self.claude_client:
            raise PaymentDetectionError("Claude client not available")

        try:
            # Convert image to base64
            import base64

            image_data = base64.b64encode(document_image).decode("utf-8")

            # Create vision analysis prompt
            prompt = """
            Analyze this document image for payment status indicators. Look for:
            1. Stamps or markings indicating "PAID"
            2. Balance amounts (zero balance = paid)
            3. Payment method references (check numbers, card transactions)
            4. Due dates and payment terms
            5. Any visual indicators of payment status

            Respond with:
            - PAID: if the document shows payment has been completed
            - UNPAID: if the document shows an outstanding balance
            - PARTIAL: if partial payment is indicated
            - VOID: if the document is void/cancelled
            - UNKNOWN: if payment status cannot be determined

            Include your confidence (0.0-1.0) and reasoning.
            """

            response = await self.claude_client.messages.create(
                model=self.claude_config["model"],
                max_tokens=1000,
                temperature=self.claude_config["temperature"],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_data,
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )

            # Parse Claude response
            response_text = response.content[0].text
            payment_status, confidence, reasoning = self._parse_claude_response(
                response_text
            )

            return MethodResult(
                method=PaymentDetectionMethod.CLAUDE_VISION,
                payment_status=payment_status,
                confidence=confidence,
                reasoning=reasoning,
                details={"claude_response": response_text},
                processing_time=0.0,
            )

        except Exception as e:
            logger.error(f"Claude Vision detection failed: {e}")
            raise CLAUDEAPIError(f"Claude Vision analysis failed: {e}")

    async def _detect_claude_text(self, document_text: str) -> MethodResult:
        """Detect payment status using Claude Text analysis"""
        if not self.claude_client:
            raise PaymentDetectionError("Claude client not available")

        try:
            prompt = f"""
            Analyze this document text for payment status indicators:

            {document_text}

            Determine the payment status based on:
            1. Explicit payment references (paid, check numbers, etc.)
            2. Balance amounts (zero balance typically means paid)
            3. Payment terms and due dates
            4. Context clues about payment completion

            Respond with:
            - PAID: if payment has been completed
            - UNPAID: if there's an outstanding balance
            - PARTIAL: if partial payment is indicated
            - VOID: if document is void/cancelled
            - UNKNOWN: if status cannot be determined

            Include confidence (0.0-1.0) and detailed reasoning.
            """

            response = await self.claude_client.messages.create(
                model=self.claude_config["model"],
                max_tokens=1000,
                temperature=self.claude_config["temperature"],
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text
            payment_status, confidence, reasoning = self._parse_claude_response(
                response_text
            )

            return MethodResult(
                method=PaymentDetectionMethod.CLAUDE_TEXT,
                payment_status=payment_status,
                confidence=confidence,
                reasoning=reasoning,
                details={"claude_response": response_text},
                processing_time=0.0,
            )

        except Exception as e:
            logger.error(f"Claude Text detection failed: {e}")
            raise CLAUDEAPIError(f"Claude Text analysis failed: {e}")

    async def _detect_regex_patterns(self, document_text: str) -> MethodResult:
        """Detect payment status using regex patterns"""
        paid_matches = sum(
            1 for pattern in self.paid_patterns if pattern.search(document_text)
        )
        unpaid_matches = sum(
            1 for pattern in self.unpaid_patterns if pattern.search(document_text)
        )
        partial_matches = sum(
            1 for pattern in self.partial_patterns if pattern.search(document_text)
        )
        void_matches = sum(
            1 for pattern in self.void_patterns if pattern.search(document_text)
        )

        # Determine status based on pattern matches
        max_matches = max(paid_matches, unpaid_matches, partial_matches, void_matches)

        if max_matches == 0:
            payment_status = PaymentStatus.UNKNOWN
            confidence = 0.3
            reasoning = "No payment indicator patterns found"
        elif void_matches == max_matches:
            payment_status = PaymentStatus.VOID
            confidence = min(0.9, 0.7 + (void_matches * 0.1))
            reasoning = f"Void patterns detected: {void_matches} matches"
        elif paid_matches == max_matches:
            payment_status = PaymentStatus.PAID
            confidence = min(0.9, 0.6 + (paid_matches * 0.1))
            reasoning = f"Paid patterns detected: {paid_matches} matches"
        elif partial_matches == max_matches:
            payment_status = PaymentStatus.PARTIAL
            confidence = min(0.8, 0.6 + (partial_matches * 0.1))
            reasoning = f"Partial payment patterns detected: {partial_matches} matches"
        else:
            payment_status = PaymentStatus.UNPAID
            confidence = min(0.8, 0.5 + (unpaid_matches * 0.1))
            reasoning = f"Unpaid patterns detected: {unpaid_matches} matches"

        return MethodResult(
            method=PaymentDetectionMethod.REGEX_PATTERNS,
            payment_status=payment_status,
            confidence=confidence,
            reasoning=reasoning,
            details={
                "paid_matches": paid_matches,
                "unpaid_matches": unpaid_matches,
                "partial_matches": partial_matches,
                "void_matches": void_matches,
            },
            processing_time=0.0,
        )

    async def _detect_keywords(self, document_text: str) -> MethodResult:
        """Detect payment status using keyword analysis"""
        text_lower = document_text.lower()

        # Count keyword categories
        paid_score = sum(
            1
            for keyword in PAYMENT_INDICATORS["PAID_KEYWORDS"]
            if keyword.lower() in text_lower
        )
        unpaid_score = sum(
            1
            for keyword in PAYMENT_INDICATORS["UNPAID_KEYWORDS"]
            if keyword.lower() in text_lower
        )
        partial_score = sum(
            1
            for keyword in PAYMENT_INDICATORS["PARTIAL_KEYWORDS"]
            if keyword.lower() in text_lower
        )
        void_score = sum(
            1
            for keyword in PAYMENT_INDICATORS["VOID_KEYWORDS"]
            if keyword.lower() in text_lower
        )

        # Determine status based on keyword scores
        max_score = max(paid_score, unpaid_score, partial_score, void_score)

        if max_score == 0:
            payment_status = PaymentStatus.UNKNOWN
            confidence = 0.2
            reasoning = "No payment keywords found"
        elif void_score == max_score:
            payment_status = PaymentStatus.VOID
            confidence = min(0.8, 0.5 + (void_score * 0.15))
            reasoning = f"Void keywords found: {void_score} matches"
        elif paid_score == max_score:
            payment_status = PaymentStatus.PAID
            confidence = min(0.8, 0.5 + (paid_score * 0.15))
            reasoning = f"Paid keywords found: {paid_score} matches"
        elif partial_score == max_score:
            payment_status = PaymentStatus.PARTIAL
            confidence = min(0.7, 0.5 + (partial_score * 0.15))
            reasoning = f"Partial payment keywords found: {partial_score} matches"
        else:
            payment_status = PaymentStatus.UNPAID
            confidence = min(0.7, 0.4 + (unpaid_score * 0.15))
            reasoning = f"Unpaid keywords found: {unpaid_score} matches"

        return MethodResult(
            method=PaymentDetectionMethod.KEYWORD_MATCHING,
            payment_status=payment_status,
            confidence=confidence,
            reasoning=reasoning,
            details={
                "paid_score": paid_score,
                "unpaid_score": unpaid_score,
                "partial_score": partial_score,
                "void_score": void_score,
            },
            processing_time=0.0,
        )

    async def _detect_amount_analysis(
        self, document_text: str, amount_info: Optional[Dict[str, Any]]
    ) -> MethodResult:
        """Detect payment status using amount analysis"""
        # Look for amount patterns in text
        amount_patterns = [
            r"(?:balance|amount)\s+(?:due|owed)?\s*:?\s*\$?([\d,]+\.?\d*)",
            r"total\s+(?:due|amount)?\s*:?\s*\$?([\d,]+\.?\d*)",
            r"(?:payment|paid)\s+(?:amount)?\s*:?\s*\$?([\d,]+\.?\d*)",
        ]

        amounts_found = []
        zero_balance_found = False

        for pattern in amount_patterns:
            matches = re.findall(pattern, document_text, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.replace(",", ""))
                    amounts_found.append(amount)
                    if amount == 0:
                        zero_balance_found = True
                except ValueError:
                    continue

        # Analysis based on amounts found
        if zero_balance_found:
            payment_status = PaymentStatus.PAID
            confidence = 0.8
            reasoning = "Zero balance amount found, indicating payment completion"
        elif amount_info and amount_info.get("amount_due"):
            # Use provided amount info if available
            amount_due = amount_info["amount_due"]
            if amount_due == 0:
                payment_status = PaymentStatus.PAID
                confidence = 0.9
                reasoning = "Amount due is zero"
            else:
                payment_status = PaymentStatus.UNPAID
                confidence = 0.7
                reasoning = f"Amount due: ${amount_due:.2f}"
        elif amounts_found:
            # Analyze found amounts
            avg_amount = statistics.mean(amounts_found)
            if avg_amount == 0:
                payment_status = PaymentStatus.PAID
                confidence = 0.7
                reasoning = "Average amount is zero, likely paid"
            else:
                payment_status = PaymentStatus.UNPAID
                confidence = 0.6
                reasoning = f"Non-zero amounts found (avg: ${avg_amount:.2f})"
        else:
            payment_status = PaymentStatus.UNKNOWN
            confidence = 0.1
            reasoning = "No amount information found for analysis"

        return MethodResult(
            method=PaymentDetectionMethod.AMOUNT_ANALYSIS,
            payment_status=payment_status,
            confidence=confidence,
            reasoning=reasoning,
            details={
                "amounts_found": amounts_found,
                "zero_balance_found": zero_balance_found,
                "amount_info": amount_info,
            },
            processing_time=0.0,
        )

    def _parse_claude_response(
        self, response_text: str
    ) -> Tuple[PaymentStatus, float, str]:
        """Parse Claude AI response for payment status"""
        response_lower = response_text.lower()

        # Extract status
        if "paid" in response_lower and "unpaid" not in response_lower:
            status = PaymentStatus.PAID
        elif "void" in response_lower or "cancelled" in response_lower:
            status = PaymentStatus.VOID
        elif "partial" in response_lower:
            status = PaymentStatus.PARTIAL
        elif "unpaid" in response_lower or "due" in response_lower:
            status = PaymentStatus.UNPAID
        else:
            status = PaymentStatus.UNKNOWN

        # Extract confidence
        confidence_match = re.search(r"confidence[:\s]+([0-9.]+)", response_lower)
        if confidence_match:
            confidence = float(confidence_match.group(1))
            if confidence > 1.0:  # Handle percentage format
                confidence = confidence / 100.0
        else:
            confidence = 0.6  # Default confidence

        return status, confidence, response_text

    def _calculate_consensus(
        self, method_results: List[MethodResult]
    ) -> PaymentConsensusResult:
        """Calculate consensus from multiple detection methods"""
        if not method_results:
            return PaymentConsensusResult(
                payment_status=PaymentStatus.UNKNOWN,
                confidence=0.0,
                methods_used=[],
                method_results={},
                quality_score=0.0,
                consensus_reached=False,
            )

        # Group results by status
        status_groups = {}
        for result in method_results:
            status = result.payment_status
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(result)

        # Calculate weighted scores for each status
        status_scores = {}
        for status, results in status_groups.items():
            # Weight by confidence and number of methods
            total_confidence = sum(r.confidence for r in results)
            method_count = len(results)
            status_scores[status] = total_confidence * method_count

        # Determine consensus status
        consensus_status = max(status_scores.items(), key=lambda x: x[1])[0]
        consensus_results = status_groups[consensus_status]

        # Calculate consensus confidence
        consensus_confidence = statistics.mean(
            [r.confidence for r in consensus_results]
        )

        # Boost confidence if multiple methods agree
        if len(consensus_results) > 1:
            agreement_boost = min(0.2, 0.1 * (len(consensus_results) - 1))
            consensus_confidence = min(1.0, consensus_confidence + agreement_boost)

        # Calculate quality score based on method diversity and confidence
        method_diversity = len(method_results) / len(self.enabled_methods)
        avg_confidence = statistics.mean([r.confidence for r in method_results])
        quality_score = (method_diversity * 0.4) + (avg_confidence * 0.6)

        # Consensus is reached if confidence is above threshold
        consensus_threshold = CONFIDENCE_THRESHOLDS.get("PAYMENT_DETECTION_MIN", 0.6)
        consensus_reached = consensus_confidence >= consensus_threshold

        # Prepare method results dict
        method_results_dict = {
            result.method.value: {
                "status": result.payment_status.value,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "processing_time": result.processing_time,
                "details": result.details,
            }
            for result in method_results
        }

        return PaymentConsensusResult(
            payment_status=consensus_status,
            confidence=consensus_confidence,
            methods_used=[r.method for r in method_results],
            method_results=method_results_dict,
            quality_score=quality_score,
            consensus_reached=consensus_reached,
        )

    async def cleanup(self):
        """Cleanup payment detection service"""
        logger.info("Cleaning up Payment Detection Service...")
        if self.claude_client:
            # Close Claude client if needed
            pass
        self.initialized = False
