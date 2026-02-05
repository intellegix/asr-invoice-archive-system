#!/usr/bin/env python3
"""
ASR Records QB Document Classification & Organization
Process documents using Claude Vision and organize into QB Chart of Accounts
"""

import os
import sys
import json
import asyncio
import logging
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import time
import re

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config.settings import settings
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('qb_classification.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DocumentMove:
    """Represents a document move operation."""
    source_path: str
    target_path: str
    vendor_name: str
    gl_account: str
    confidence: float
    reason: str

class QBDocumentProcessor:
    """Process documents into QB Chart of Accounts structure."""

    def __init__(self, target_directory: str, dry_run: bool = True, sample_size: Optional[int] = None):
        """Initialize document processor."""
        self.target_directory = Path(target_directory)
        self.dry_run = dry_run
        self.sample_size = sample_size
        self.moves_planned = []
        self.processing_stats = {
            "files_scanned": 0,
            "files_processed": 0,
            "files_moved": 0,
            "errors": 0,
            "cost_estimate": 0.0
        }

        # QB folder mappings
        self.vendor_mappings = self._get_vendor_mappings()
        self.qb_folders = self._get_qb_folders()

        logger.info(f"QB Document Processor initialized")
        logger.info(f"Target: {self.target_directory}")
        logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE PROCESSING'}")
        if sample_size:
            logger.info(f"Sample size: {sample_size} documents")

    def _get_vendor_mappings(self) -> Dict[str, str]:
        """Get vendor to GL account mappings."""
        return {
            # Materials/Supplies
            "abc_supply": "5010-Roofing_Materials",
            "home_depot": "5010-Roofing_Materials",
            "lowes": "5010-Roofing_Materials",
            "beacon": "5010-Roofing_Materials",
            "ferguson": "5010-Roofing_Materials",

            # Utilities & Waste
            "usa_waste": "6300-6400-Utilities_Rent",
            "waste_management": "6300-6400-Utilities_Rent",
            "edco": "6300-6400-Utilities_Rent",
            "republic": "6300-6400-Utilities_Rent",
            "sdge": "6300-6400-Utilities_Rent",
            "cox": "6300-6400-Utilities_Rent",
            "verizon": "6300-6400-Utilities_Rent",
            "att": "6300-6400-Utilities_Rent",

            # Vehicle/Equipment
            "ford": "6700-6750-Equipment_Subcontractors",
            "chevrolet": "6700-6750-Equipment_Subcontractors",
            "toyota": "6700-6750-Equipment_Subcontractors",
            "nissan": "6700-6750-Equipment_Subcontractors",
            "united_rentals": "6700-6750-Equipment_Subcontractors",
            "sunbelt": "6700-6750-Equipment_Subcontractors",

            # Insurance
            "liberty_mutual": "6075-6190-Insurance_Related",
            "state_farm": "6075-6190-Insurance_Related",
            "allstate": "6075-6190-Insurance_Related",
            "farmers": "6075-6190-Insurance_Related",
            "progressive": "6075-6190-Insurance_Related",

            # Professional Services
            "quickbooks": "6200-6290-Professional_Services",
            "intuit": "6200-6290-Professional_Services",
            "adobe": "6200-6290-Professional_Services",
            "microsoft": "6200-6290-Professional_Services",
            "google": "6200-6290-Professional_Services",

            # Credit Cards
            "wells_fargo": "2139-2175-Credit_Cards/Wells_Fargo",
            "capital_one": "2139-2175-Credit_Cards/Capital_One",
            "american_express": "2139-2175-Credit_Cards/AmEx",
            "amex": "2139-2175-Credit_Cards/AmEx",
            "home_depot_card": "2139-2175-Credit_Cards/Home_Depot",

            # Office/Admin
            "staples": "6500-6600-Office_Admin",
            "office_depot": "6500-6600-Office_Admin",
            "costco": "6500-6600-Office_Admin",
            "fedex": "6500-6600-Office_Admin",
            "ups": "6500-6600-Office_Admin",
            "usps": "6500-6600-Office_Admin"
        }

    def _get_qb_folders(self) -> List[str]:
        """Get list of QB account folders."""
        base_folders = [
            "1000-ASSETS",
            "2000-LIABILITIES",
            "3000-EQUITY",
            "4000-INCOME",
            "5000-COGS",
            "6000-OPERATING_EXPENSES"
        ]

        subfolders = [
            "1020-Banking", "1200-Accounts_Receivable", "1400-Current_Assets", "1440-Fixed_Assets",
            "2000-Accounts_Payable", "2139-2175-Credit_Cards", "2400-2430-Loans_Payable",
            "4060-Construction_Sales", "4100-Sales", "4110-Repairs", "4120-Reroofing",
            "5010-Roofing_Materials", "5020-Direct_Labor", "5030-Payroll_Taxes",
            "6075-6190-Insurance_Related", "6200-6290-Professional_Services",
            "6300-6400-Utilities_Rent", "6500-6600-Office_Admin", "6700-6750-Equipment_Subcontractors"
        ]

        return base_folders + subfolders

    async def scan_documents_for_processing(self) -> List[Dict[str, Any]]:
        """Scan legacy folders for documents to process."""
        logger.info("Scanning legacy folders for documents...")

        legacy_folders = [
            "CLOSED Billing",
            "OPEN Billing",
            "Closed Payable",
            "Open Payable"
        ]

        documents_found = []

        for folder_name in legacy_folders:
            folder_path = self.target_directory / folder_name
            if not folder_path.exists():
                logger.warning(f"Legacy folder not found: {folder_path}")
                continue

            logger.info(f"Scanning folder: {folder_name}")

            for file_path in folder_path.rglob("*.pdf"):
                documents_found.append({
                    "file_path": str(file_path),
                    "source_folder": folder_name,
                    "file_size": file_path.stat().st_size,
                    "filename": file_path.name
                })

        self.processing_stats["files_scanned"] = len(documents_found)

        # Apply sample size limit if specified
        if self.sample_size and len(documents_found) > self.sample_size:
            logger.info(f"Limiting to sample size: {self.sample_size}")
            documents_found = documents_found[:self.sample_size]

        logger.info(f"Found {len(documents_found)} documents for processing")
        return documents_found

    async def classify_document_by_filename(self, file_info: Dict[str, Any]) -> DocumentMove:
        """Classify document based on filename analysis (fast, no API cost)."""
        file_path = file_info["file_path"]
        filename = file_info["filename"]

        # Parse filename for vendor information
        # Format: YYYYMMDD_HHMMSS_Vendor_Amount_...
        parts = filename.split('_')

        vendor_name = "Unknown"
        gl_account = "6000-OPERATING_EXPENSES"
        confidence = 0.5
        reason = "filename_analysis"

        if len(parts) >= 3:
            # Extract vendor name (usually parts[2] and possibly parts[3])
            vendor_parts = []
            for i in range(2, len(parts)):
                if parts[i].replace('.', '').replace(',', '').isdigit():
                    # This is likely the amount, stop here
                    break
                vendor_parts.append(parts[i])

            vendor_name = "_".join(vendor_parts).upper()

            # Map vendor to GL account
            vendor_clean = vendor_name.lower().replace('_', ' ')

            # Check for vendor mappings
            best_match_folder = "6000-OPERATING_EXPENSES"  # Default
            best_confidence = 0.6

            for vendor_key, folder in self.vendor_mappings.items():
                if vendor_key.replace('_', ' ') in vendor_clean:
                    best_match_folder = folder
                    best_confidence = 0.9
                    break
                elif any(word in vendor_clean for word in vendor_key.split('_')):
                    best_match_folder = folder
                    best_confidence = 0.7

            gl_account = best_match_folder
            confidence = best_confidence
            reason = f"vendor_mapping_{vendor_key if 'vendor_key' in locals() else 'default'}"

        # Determine target path
        target_folder = self.target_directory / gl_account
        target_path = target_folder / filename

        return DocumentMove(
            source_path=file_path,
            target_path=str(target_path),
            vendor_name=vendor_name,
            gl_account=gl_account,
            confidence=confidence,
            reason=reason
        )

    async def process_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process documents for QB organization."""
        logger.info(f"Processing {len(documents)} documents...")

        moves = []
        errors = []

        for i, doc_info in enumerate(documents):
            try:
                if i % 100 == 0:
                    logger.info(f"Processing document {i+1}/{len(documents)}")

                # Classify document (fast filename-based method)
                move = await self.classify_document_by_filename(doc_info)
                moves.append(move)

                self.processing_stats["files_processed"] += 1

            except Exception as e:
                error_msg = f"Error processing {doc_info.get('filename', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                self.processing_stats["errors"] += 1

        logger.info(f"Classification complete: {len(moves)} moves planned, {len(errors)} errors")

        return {
            "moves": moves,
            "errors": errors,
            "total_processed": len(documents),
            "successful": len(moves),
            "failed": len(errors)
        }

    async def execute_document_moves(self, moves: List[DocumentMove]) -> Dict[str, Any]:
        """Execute document moves to QB folders."""
        logger.info(f"Executing {len(moves)} document moves...")

        moves_completed = 0
        moves_failed = 0
        folders_created = set()
        errors = []

        for i, move in enumerate(moves):
            try:
                if i % 50 == 0:
                    logger.info(f"Moving document {i+1}/{len(moves)}")

                source_path = Path(move.source_path)
                target_path = Path(move.target_path)

                # Ensure target folder exists
                target_folder = target_path.parent
                if not target_folder.exists():
                    if not self.dry_run:
                        target_folder.mkdir(parents=True, exist_ok=True)
                    folders_created.add(str(target_folder))

                # Handle filename conflicts
                if target_path.exists():
                    # Append timestamp to avoid conflicts
                    timestamp = int(time.time())
                    name_parts = target_path.name.rsplit('.', 1)
                    if len(name_parts) == 2:
                        new_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
                    else:
                        new_name = f"{target_path.name}_{timestamp}"
                    target_path = target_folder / new_name

                # Execute move
                if not self.dry_run:
                    shutil.move(str(source_path), str(target_path))
                    logger.debug(f"MOVED: {source_path.name} -> {move.gl_account}")
                else:
                    logger.debug(f"WOULD MOVE: {source_path.name} -> {move.gl_account}")

                moves_completed += 1

            except Exception as e:
                error_msg = f"Failed to move {move.source_path}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                moves_failed += 1

        self.processing_stats["files_moved"] = moves_completed

        logger.info(f"Move execution complete: {moves_completed} successful, {moves_failed} failed")

        return {
            "moves_completed": moves_completed,
            "moves_failed": moves_failed,
            "folders_created": list(folders_created),
            "errors": errors
        }

    def generate_processing_report(self, classification_result: Dict[str, Any],
                                 move_result: Dict[str, Any]) -> None:
        """Generate comprehensive processing report."""
        print(f"\n{'='*70}")
        print(f"ASR RECORDS QB DOCUMENT PROCESSING REPORT")
        print(f"{'='*70}")
        print(f"Target Directory: {self.target_directory}")
        print(f"Processing Mode: {'DRY RUN' if self.dry_run else 'LIVE EXECUTION'}")
        print(f"Processing Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        print(f"\nPROCESSING STATISTICS:")
        print(f"Documents Scanned: {self.processing_stats['files_scanned']:,}")
        print(f"Documents Processed: {self.processing_stats['files_processed']:,}")
        print(f"Documents Moved: {self.processing_stats['files_moved']:,}")
        print(f"Processing Errors: {self.processing_stats['errors']:,}")

        print(f"\nCLASSIFICATION RESULTS:")
        print(f"Successful Classifications: {classification_result['successful']:,}")
        print(f"Failed Classifications: {classification_result['failed']:,}")
        print(f"Success Rate: {(classification_result['successful']/max(1,classification_result['total_processed'])*100):.1f}%")

        print(f"\nMOVE EXECUTION RESULTS:")
        print(f"Moves Completed: {move_result['moves_completed']:,}")
        print(f"Moves Failed: {move_result['moves_failed']:,}")
        print(f"Folders Created: {len(move_result['folders_created']):,}")

        # Show sample GL account distribution
        if classification_result['moves']:
            gl_accounts = {}
            for move in classification_result['moves']:
                gl_accounts[move.gl_account] = gl_accounts.get(move.gl_account, 0) + 1

            print(f"\nGL ACCOUNT DISTRIBUTION (Top 10):")
            sorted_accounts = sorted(gl_accounts.items(), key=lambda x: x[1], reverse=True)
            for account, count in sorted_accounts[:10]:
                print(f"  {account}: {count:,} documents")

        if move_result['errors']:
            print(f"\nERRORS (First 5):")
            for error in move_result['errors'][:5]:
                print(f"  - {error}")

        print(f"\nCOST ANALYSIS:")
        print(f"API Cost: $0.00 (filename-based classification)")
        print(f"Processing Method: Fast filename analysis")
        print(f"Cost Savings: 100% vs Claude API classification")

        print(f"{'='*70}")

        # Overall success assessment
        overall_success_rate = (self.processing_stats['files_moved'] /
                               max(1, self.processing_stats['files_scanned']) * 100)

        if overall_success_rate >= 95:
            print(f"STATUS: EXCELLENT - {overall_success_rate:.1f}% success rate")
        elif overall_success_rate >= 85:
            print(f"STATUS: GOOD - {overall_success_rate:.1f}% success rate")
        elif overall_success_rate >= 70:
            print(f"STATUS: ACCEPTABLE - {overall_success_rate:.1f}% success rate")
        else:
            print(f"STATUS: NEEDS IMPROVEMENT - {overall_success_rate:.1f}% success rate")

async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="ASR Records QB Document Classification & Organization"
    )
    parser.add_argument(
        "--target-dir",
        default="C:/Users/AustinKidwell/ASR Dropbox/Austin Kidwell/Digital Billing Records (QB Organized)",
        help="Target directory containing QB structure and legacy folders"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Perform dry run without moving files"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute actual file moves (overrides dry-run)"
    )
    parser.add_argument(
        "--sample",
        type=int,
        help="Process only a sample of N documents for testing"
    )

    args = parser.parse_args()

    # Override dry_run if execute is specified
    if args.execute:
        args.dry_run = False

    # Initialize processor
    processor = QBDocumentProcessor(args.target_dir, args.dry_run, args.sample)

    try:
        # Phase 1: Scan documents
        logger.info("PHASE 1: Scanning documents")
        documents = await processor.scan_documents_for_processing()

        if not documents:
            print("No documents found for processing!")
            return 0

        # Phase 2: Classify documents
        logger.info("PHASE 2: Classifying documents")
        classification_result = await processor.process_documents(documents)

        # Phase 3: Execute moves
        logger.info("PHASE 3: Executing document moves")
        move_result = await processor.execute_document_moves(classification_result['moves'])

        # Generate report
        processor.generate_processing_report(classification_result, move_result)

        # Return success/failure
        overall_errors = (classification_result['failed'] + move_result['moves_failed'])
        return 0 if overall_errors == 0 else 1

    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))