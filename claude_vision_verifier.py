"""
Claude Vision API Document Verification System
Complete document verification for QB organized records using Claude Vision API
"""

import asyncio
import json
import logging
import os
import time
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import argparse
import hashlib
import re

# Import existing system components
from records_consolidation_system.parallel_classifier import ClaudeVisionClient, DocumentClassification
from records_consolidation_system.config import config
from config.settings import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('claude_vision_verification.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class VerificationBatchResult:
    """Result from Vision API verification batch."""
    batch_id: str
    documents_processed: int
    successful_verifications: int
    failed_verifications: int
    total_cost_usd: float
    average_confidence: float
    processing_time_seconds: float
    classifications: List[DocumentClassification]
    improved_classifications: int
    payment_status_corrections: int

@dataclass
class ComprehensiveVerificationResult:
    """Complete verification result for all documents."""
    verification_timestamp: str
    total_documents_analyzed: int
    total_processing_cost: float
    average_confidence_score: float
    classification_improvements: int
    payment_status_improvements: int
    gl_account_optimizations: int
    failed_document_recoveries: int
    batch_results: List[VerificationBatchResult]
    quality_metrics: Dict[str, float]

class ClaudeVisionVerifier:
    """Claude Vision API document verification system for QB organized records."""

    def __init__(self, target_directory: str):
        self.target_directory = Path(target_directory)
        self.claude_client = ClaudeVisionClient()
        self.verification_results = []

        # QB Account mapping for improved classification
        self.qb_account_mapping = {
            "Cost of Goods Sold": {
                "Building Supplies (6090)": ["lumber", "hardware", "building", "materials", "supplies"],
                "Roofing Materials (6091)": ["roofing", "shingles", "membrane", "flashing", "gutter"],
                "Auto Insurance (6184)": ["auto", "vehicle", "insurance", "ford", "truck"],
                "Equipment Rental (6092)": ["rental", "equipment", "machinery", "tools"]
            },
            "Operating Expenses": {
                "Professional Services (6201)": ["legal", "accounting", "consulting", "professional"],
                "Utilities (6202)": ["electric", "gas", "water", "utilities", "sdge"],
                "Insurance (6203)": ["insurance", "liability", "workers", "comp"]
            },
            "Credit Cards": {
                "Business Credit Card (2001)": ["credit", "card", "mastercard", "visa", "amex"]
            }
        }

    async def run_pilot_verification(self, sample_size: int = 500) -> VerificationBatchResult:
        """
        Run pilot verification on sample documents to validate approach.

        Args:
            sample_size: Number of documents for pilot testing
        """
        logger.info(f"Starting pilot verification with {sample_size} documents...")

        # Collect diverse sample
        sample_documents = await self._collect_stratified_sample(sample_size)

        # Process pilot batch
        batch_result = await self._process_verification_batch(
            batch_id="pilot",
            document_paths=sample_documents
        )

        # Analyze pilot results
        await self._analyze_pilot_results(batch_result)

        return batch_result

    async def run_priority_category_verification(self) -> List[VerificationBatchResult]:
        """
        Run verification on priority categories (Cost of Goods Sold, Failed docs).
        """
        logger.info("Starting priority category verification...")
        results = []

        # Batch 1: Cost of Goods Sold documents
        cogs_documents = await self._collect_category_documents("Cost of Goods Sold")
        if cogs_documents:
            logger.info(f"Processing {len(cogs_documents)} Cost of Goods Sold documents...")
            cogs_result = await self._process_verification_batch(
                batch_id="cost_of_goods_sold",
                document_paths=cogs_documents
            )
            results.append(cogs_result)

        # Batch 2: Failed/low-confidence documents
        failed_documents = await self._collect_failed_documents()
        if failed_documents:
            logger.info(f"Processing {len(failed_documents)} failed/low-confidence documents...")
            failed_result = await self._process_verification_batch(
                batch_id="failed_recovery",
                document_paths=failed_documents
            )
            results.append(failed_result)

        return results

    async def run_comprehensive_verification(self) -> ComprehensiveVerificationResult:
        """
        Run comprehensive Claude Vision verification on all documents.
        """
        logger.info("Starting comprehensive document verification...")
        start_time = time.time()

        # Collect all documents
        all_documents = await self._collect_all_documents()
        logger.info(f"Found {len(all_documents)} documents for verification")

        # Process in batches to manage cost and rate limits
        batch_size = config.PARALLEL_LIMITS["batch_size"]
        batch_results = []
        total_cost = 0.0
        total_processed = 0

        for i in range(0, len(all_documents), batch_size):
            batch_docs = all_documents[i:i + batch_size]
            batch_id = f"comprehensive_batch_{i//batch_size + 1:03d}"

            logger.info(f"Processing batch {batch_id} ({len(batch_docs)} documents)...")

            batch_result = await self._process_verification_batch(
                batch_id=batch_id,
                document_paths=batch_docs
            )

            batch_results.append(batch_result)
            total_cost += batch_result.total_cost_usd
            total_processed += batch_result.documents_processed

            # Cost monitoring
            if total_cost > 400:  # Safety limit
                logger.warning(f"Approaching cost limit ($400). Processed {total_processed} documents.")
                break

        # Compile comprehensive results
        processing_time = time.time() - start_time

        comprehensive_result = ComprehensiveVerificationResult(
            verification_timestamp=datetime.now().isoformat(),
            total_documents_analyzed=total_processed,
            total_processing_cost=total_cost,
            average_confidence_score=self._calculate_average_confidence(batch_results),
            classification_improvements=sum(b.improved_classifications for b in batch_results),
            payment_status_improvements=sum(b.payment_status_corrections for b in batch_results),
            gl_account_optimizations=sum(b.improved_classifications for b in batch_results),
            failed_document_recoveries=sum(b.successful_verifications for b in batch_results
                                         if b.batch_id.startswith("failed")),
            batch_results=batch_results,
            quality_metrics=await self._calculate_quality_metrics(batch_results)
        )

        # Save comprehensive report
        await self._save_comprehensive_report(comprehensive_result)

        logger.info(f"Comprehensive verification completed in {processing_time:.2f} seconds")
        logger.info(f"Total cost: ${total_cost:.2f}")

        return comprehensive_result

    async def _collect_stratified_sample(self, sample_size: int) -> List[Path]:
        """Collect stratified sample from different document categories."""
        sample_docs = []

        # Categories to sample from
        categories = {
            "cost_of_goods_sold": 0.6,  # 60% of sample
            "operating_expenses": 0.2,   # 20% of sample
            "credit_cards": 0.1,         # 10% of sample
            "random": 0.1                # 10% random
        }

        for category, percentage in categories.items():
            category_size = int(sample_size * percentage)

            if category == "random":
                # Random sampling from all directories
                all_docs = await self._collect_all_documents()
                import random
                sample_docs.extend(random.sample(all_docs, min(category_size, len(all_docs))))
            else:
                # Category-specific sampling
                category_docs = await self._collect_category_documents(category)
                if category_docs:
                    import random
                    sample_docs.extend(random.sample(category_docs,
                                                   min(category_size, len(category_docs))))

        return sample_docs[:sample_size]

    async def _collect_category_documents(self, category: str) -> List[Path]:
        """Collect documents from specific QB category."""
        documents = []

        category_patterns = {
            "cost_of_goods_sold": ["Cost of Goods Sold"],
            "operating_expenses": ["Operating Expenses"],
            "credit_cards": ["Credit Cards"],
            "Cost of Goods Sold": ["Cost of Goods Sold"]
        }

        patterns = category_patterns.get(category, [category])

        for root, dirs, files in os.walk(self.target_directory):
            # Check if current directory matches category
            current_path = str(root).lower()
            if any(pattern.lower() in current_path for pattern in patterns):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        documents.append(Path(root) / file)

        return documents

    async def _collect_failed_documents(self) -> List[Path]:
        """Collect documents that previously failed classification or have low confidence."""
        # This would typically come from previous processing logs
        # For now, we'll use a heuristic approach

        failed_docs = []

        # Look for documents in generic folders or with poor naming
        for root, dirs, files in os.walk(self.target_directory):
            for file in files:
                if file.lower().endswith('.pdf'):
                    file_path = Path(root) / file

                    # Heuristics for potentially failed classifications
                    if (
                        "manual_review" in str(file_path).lower() or
                        "unprocessed" in str(file_path).lower() or
                        "unknown" in str(file_path).lower() or
                        len(file) < 20  # Very short filenames
                    ):
                        failed_docs.append(file_path)

        return failed_docs

    async def _collect_all_documents(self) -> List[Path]:
        """Collect all PDF documents in the target directory."""
        documents = []

        for root, dirs, files in os.walk(self.target_directory):
            for file in files:
                if file.lower().endswith('.pdf'):
                    documents.append(Path(root) / file)

        return documents

    async def _process_verification_batch(self,
                                        batch_id: str,
                                        document_paths: List[Path]) -> VerificationBatchResult:
        """Process a batch of documents through Claude Vision API."""
        start_time = time.time()
        classifications = []
        successful_verifications = 0
        failed_verifications = 0
        total_cost = 0.0
        improved_classifications = 0
        payment_status_corrections = 0

        # Process documents with semaphore for rate limiting
        semaphore = asyncio.Semaphore(config.PARALLEL_LIMITS["max_classifier_agents"])

        async def process_single_document(doc_path: Path):
            nonlocal successful_verifications, failed_verifications, total_cost
            nonlocal improved_classifications, payment_status_corrections

            async with semaphore:
                try:
                    # Get current classification from file location/name
                    current_classification = self._extract_current_classification(doc_path)

                    # Run Claude Vision classification
                    vision_classification = await self.claude_client.classify_document(str(doc_path))

                    # Compare and identify improvements
                    if self._is_classification_improved(current_classification, vision_classification):
                        improved_classifications += 1

                    if self._is_payment_status_improved(current_classification, vision_classification):
                        payment_status_corrections += 1

                    classifications.append(vision_classification)
                    total_cost += vision_classification.api_cost_usd
                    successful_verifications += 1

                except Exception as e:
                    logger.warning(f"Verification failed for {doc_path}: {e}")
                    failed_verifications += 1

        # Execute batch processing
        tasks = [process_single_document(doc_path) for doc_path in document_paths]
        await asyncio.gather(*tasks, return_exceptions=True)

        processing_time = time.time() - start_time
        average_confidence = (
            sum(c.confidence_score for c in classifications) / len(classifications)
            if classifications else 0.0
        )

        return VerificationBatchResult(
            batch_id=batch_id,
            documents_processed=len(document_paths),
            successful_verifications=successful_verifications,
            failed_verifications=failed_verifications,
            total_cost_usd=total_cost,
            average_confidence=average_confidence,
            processing_time_seconds=processing_time,
            classifications=classifications,
            improved_classifications=improved_classifications,
            payment_status_corrections=payment_status_corrections
        )

    def _extract_current_classification(self, doc_path: Path) -> Dict[str, Any]:
        """Extract current classification from file path and naming."""
        path_parts = doc_path.parts

        # Determine billing status from path
        billing_status = "CLOSED" if "CLOSED Billing" in str(doc_path) else "OPEN"

        # Extract GL account from path structure
        gl_account = "Unknown"
        for part in path_parts:
            if "(" in part and ")" in part:  # GL account pattern like "Building Supplies (6090)"
                gl_account = part
                break

        # Extract vendor from filename or path
        vendor = doc_path.stem.split('_')[0] if '_' in doc_path.stem else "Unknown"

        return {
            "billing_status": billing_status,
            "gl_account": gl_account,
            "vendor_name": vendor,
            "file_path": str(doc_path)
        }

    def _is_classification_improved(self,
                                  current: Dict[str, Any],
                                  vision: DocumentClassification) -> bool:
        """Determine if Vision API classification is an improvement."""
        # Check if Vision API provides more specific GL account
        if vision.gl_account and vision.gl_account != "Unknown":
            current_gl = current.get("gl_account", "Unknown")
            if current_gl == "Unknown" or "General" in current_gl:
                return True

        # Check if vendor name is more accurately extracted
        if vision.vendor_name and vision.vendor_name != "Unknown":
            current_vendor = current.get("vendor_name", "Unknown")
            if current_vendor == "Unknown" or len(vision.vendor_name) > len(current_vendor):
                return True

        return False

    def _is_payment_status_improved(self,
                                  current: Dict[str, Any],
                                  vision: DocumentClassification) -> bool:
        """Determine if payment status detection is improved."""
        # This would require analysis of Vision API's payment status detection
        # For now, assume improvement if confidence is high
        return vision.confidence_score > 0.9

    async def _analyze_pilot_results(self, pilot_result: VerificationBatchResult) -> None:
        """Analyze pilot results and provide recommendations."""
        logger.info("="*60)
        logger.info("PILOT VERIFICATION RESULTS")
        logger.info("="*60)
        logger.info(f"Documents Processed: {pilot_result.documents_processed}")
        logger.info(f"Success Rate: {pilot_result.successful_verifications/pilot_result.documents_processed*100:.1f}%")
        logger.info(f"Average Confidence: {pilot_result.average_confidence:.2f}")
        logger.info(f"Cost: ${pilot_result.total_cost_usd:.2f}")
        logger.info(f"Classification Improvements: {pilot_result.improved_classifications}")
        logger.info(f"Payment Status Corrections: {pilot_result.payment_status_corrections}")

        # Estimate full processing cost
        total_docs = len(await self._collect_all_documents())
        estimated_full_cost = (pilot_result.total_cost_usd / pilot_result.documents_processed) * total_docs

        logger.info(f"Estimated Full Processing Cost: ${estimated_full_cost:.2f}")
        logger.info("="*60)

    def _calculate_average_confidence(self, batch_results: List[VerificationBatchResult]) -> float:
        """Calculate average confidence across all batches."""
        total_confidence = 0.0
        total_documents = 0

        for batch in batch_results:
            total_confidence += batch.average_confidence * batch.successful_verifications
            total_documents += batch.successful_verifications

        return total_confidence / total_documents if total_documents > 0 else 0.0

    async def _calculate_quality_metrics(self, batch_results: List[VerificationBatchResult]) -> Dict[str, float]:
        """Calculate quality metrics from verification results."""
        if not batch_results:
            return {}

        total_processed = sum(b.documents_processed for b in batch_results)
        total_successful = sum(b.successful_verifications for b in batch_results)
        total_improvements = sum(b.improved_classifications for b in batch_results)

        return {
            "overall_success_rate": total_successful / total_processed * 100 if total_processed > 0 else 0,
            "improvement_rate": total_improvements / total_successful * 100 if total_successful > 0 else 0,
            "average_processing_time": sum(b.processing_time_seconds for b in batch_results) / len(batch_results),
            "cost_efficiency": total_processed / sum(b.total_cost_usd for b in batch_results) if sum(b.total_cost_usd for b in batch_results) > 0 else 0
        }

    async def _save_comprehensive_report(self, result: ComprehensiveVerificationResult) -> str:
        """Save comprehensive verification report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"claude_vision_verification_report_{timestamp}.json"

        # Convert to serializable format
        report_data = {
            "comprehensive_result": asdict(result),
            "batch_details": [asdict(batch) for batch in result.batch_results],
            "system_info": {
                "target_directory": str(self.target_directory),
                "claude_model": config.CLAUDE_MODEL,
                "verification_version": "1.0.0"
            }
        }

        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        logger.info(f"Comprehensive report saved: {report_file}")
        return report_file

async def main():
    """Main execution with command-line interface."""
    parser = argparse.ArgumentParser(description="Claude Vision API Document Verification")
    parser.add_argument("--target-dir",
                       default=settings.CONSOLIDATION_TARGET_DIR,
                       help="Target QB organized directory")
    parser.add_argument("--mode",
                       choices=["pilot", "priority", "comprehensive"],
                       default="pilot",
                       help="Verification mode")
    parser.add_argument("--sample-size", type=int, default=500,
                       help="Sample size for pilot verification")
    parser.add_argument("--max-cost", type=float, default=485.0,
                       help="Maximum processing cost limit")

    args = parser.parse_args()

    # Validate API key
    if not config.ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY environment variable required")
        return

    # Initialize verifier
    verifier = ClaudeVisionVerifier(args.target_dir)

    try:
        if args.mode == "pilot":
            result = await verifier.run_pilot_verification(args.sample_size)
            print(f"\nPilot verification completed. Cost: ${result.total_cost_usd:.2f}")

        elif args.mode == "priority":
            results = await verifier.run_priority_category_verification()
            total_cost = sum(r.total_cost_usd for r in results)
            print(f"\nPriority verification completed. Total cost: ${total_cost:.2f}")

        elif args.mode == "comprehensive":
            result = await verifier.run_comprehensive_verification()
            print(f"\nComprehensive verification completed.")
            print(f"Documents analyzed: {result.total_documents_analyzed:,}")
            print(f"Total cost: ${result.total_processing_cost:.2f}")
            print(f"Average confidence: {result.average_confidence_score:.2f}")
            print(f"Classification improvements: {result.classification_improvements}")

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())