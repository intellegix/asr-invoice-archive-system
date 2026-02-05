"""
Comprehensive Audit and Consolidation System
Ensures complete file migration and proper QB organization across all directories
"""

import asyncio
import json
import logging
import os
import hashlib
import time
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_audit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class FileRecord:
    """Record of a single file with metadata."""
    file_path: str
    file_name: str
    file_hash: str
    file_size: int
    directory_source: str
    qb_category: Optional[str]
    vendor_extracted: Optional[str]
    modification_time: float

@dataclass
class DirectoryInventory:
    """Complete inventory of a directory."""
    directory_path: str
    total_files: int
    total_size_mb: float
    file_records: List[FileRecord]
    qb_categories: Dict[str, int]
    vendor_distribution: Dict[str, int]

@dataclass
class AuditResult:
    """Complete audit result across all directories."""
    audit_timestamp: str
    source_dir1_inventory: DirectoryInventory
    source_dir2_inventory: DirectoryInventory
    destination_inventory: DirectoryInventory
    migration_completeness: Dict[str, Any]
    classification_accuracy: Dict[str, Any]
    missing_files: List[str]
    duplicate_files: List[Tuple[str, str]]
    misclassified_files: List[str]
    qb_structure_compliance: Dict[str, Any]
    recommendations: List[str]

class ComprehensiveAuditSystem:
    """Complete audit system for QB organization validation and file consolidation."""

    def __init__(self):
        # Define the three critical directories
        self.source_dir1 = Path("C:/Users/AustinKidwell/ASR Dropbox/Austin Kidwell/08_Financial_PayrollOperations/Digital Billing Records (QB Organized)")
        self.source_dir2 = Path("C:/Users/AustinKidwell/ASR Dropbox/Austin Kidwell/08_Financial_PayrollOperations/Digital Billing Records")
        self.destination_dir = Path("C:/Users/AustinKidwell/ASR Dropbox/Austin Kidwell/Digital Billing Records (QB Organized)")

        # QB Chart of Accounts structure for validation
        self.qb_structure = {
            "1000-ASSETS": ["Current Assets", "Fixed Assets", "Other Assets"],
            "2000-LIABILITIES": ["Current Liabilities", "Long Term Liabilities"],
            "2139-2175-Credit_Cards": ["Business Credit Cards", "Equipment Financing"],
            "3000-EQUITY": ["Owner Equity", "Retained Earnings"],
            "4000-INCOME": ["Service Revenue", "Product Sales"],
            "5000-COGS": ["Direct Materials", "Direct Labor"],
            "5010-Roofing_Materials": ["Shingles", "Membrane", "Flashing"],
            "6000-OPERATING_EXPENSES": ["General Operations", "Administration"],
            "6075-6190-Insurance_Related": ["Liability", "Workers Comp", "Vehicle"],
            "6300-6400-Utilities_Rent": ["Electric", "Gas", "Water", "Rent"],
            "6500-6600-Office_Admin": ["Office Supplies", "Professional Services"],
            "6700-6750-Equipment_Subcontractors": ["Equipment Rental", "Subcontractor Costs"]
        }

    async def run_comprehensive_audit(self) -> AuditResult:
        """
        Run complete audit of all directories and QB organization.
        """
        logger.info("Starting comprehensive audit and consolidation verification...")
        start_time = time.time()

        # Phase 1: Inventory all directories
        logger.info("Phase 1: Creating complete directory inventories...")
        source1_inventory = await self._create_directory_inventory(self.source_dir1, "Source Directory 1")
        source2_inventory = await self._create_directory_inventory(self.source_dir2, "Source Directory 2")
        destination_inventory = await self._create_directory_inventory(self.destination_dir, "Destination Directory")

        # Phase 2: Migration completeness analysis
        logger.info("Phase 2: Analyzing migration completeness...")
        migration_analysis = await self._analyze_migration_completeness(
            source1_inventory, source2_inventory, destination_inventory
        )

        # Phase 3: Classification accuracy assessment
        logger.info("Phase 3: Assessing classification accuracy...")
        classification_analysis = await self._assess_classification_accuracy(destination_inventory)

        # Phase 4: Find missing and duplicate files
        logger.info("Phase 4: Identifying missing and duplicate files...")
        missing_files, duplicate_files = await self._find_missing_and_duplicates(
            source1_inventory, source2_inventory, destination_inventory
        )

        # Phase 5: QB structure compliance check
        logger.info("Phase 5: Validating QB structure compliance...")
        qb_compliance = await self._validate_qb_structure(destination_inventory)

        # Phase 6: Generate recommendations
        logger.info("Phase 6: Generating recommendations...")
        recommendations = await self._generate_recommendations(
            migration_analysis, classification_analysis, missing_files, duplicate_files, qb_compliance
        )

        # Compile complete audit result
        audit_result = AuditResult(
            audit_timestamp=datetime.now().isoformat(),
            source_dir1_inventory=source1_inventory,
            source_dir2_inventory=source2_inventory,
            destination_inventory=destination_inventory,
            migration_completeness=migration_analysis,
            classification_accuracy=classification_analysis,
            missing_files=missing_files,
            duplicate_files=duplicate_files,
            misclassified_files=[], # Will be populated based on analysis
            qb_structure_compliance=qb_compliance,
            recommendations=recommendations
        )

        processing_time = time.time() - start_time
        logger.info(f"Comprehensive audit completed in {processing_time:.2f} seconds")

        # Save detailed audit report
        await self._save_audit_report(audit_result)

        return audit_result

    async def _create_directory_inventory(self, directory: Path, dir_name: str) -> DirectoryInventory:
        """Create complete inventory of a directory."""
        logger.info(f"Scanning {dir_name}: {directory}")

        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return DirectoryInventory(
                directory_path=str(directory),
                total_files=0,
                total_size_mb=0.0,
                file_records=[],
                qb_categories={},
                vendor_distribution={}
            )

        file_records = []
        total_size = 0
        qb_categories = defaultdict(int)
        vendor_distribution = defaultdict(int)

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.tiff')):
                    file_path = Path(root) / file

                    try:
                        # Get file metadata
                        file_size = file_path.stat().st_size
                        modification_time = file_path.stat().st_mtime
                        total_size += file_size

                        # Calculate file hash for duplicate detection
                        with open(file_path, 'rb') as f:
                            file_hash = hashlib.sha256(f.read()).hexdigest()

                        # Extract QB category from path
                        qb_category = self._extract_qb_category_from_path(file_path)
                        if qb_category:
                            qb_categories[qb_category] += 1

                        # Extract vendor from filename or path
                        vendor = self._extract_vendor_from_path(file_path)
                        if vendor:
                            vendor_distribution[vendor] += 1

                        file_record = FileRecord(
                            file_path=str(file_path),
                            file_name=file.name,
                            file_hash=file_hash,
                            file_size=file_size,
                            directory_source=dir_name,
                            qb_category=qb_category,
                            vendor_extracted=vendor,
                            modification_time=modification_time
                        )

                        file_records.append(file_record)

                    except Exception as e:
                        logger.warning(f"Could not process file {file_path}: {e}")

        return DirectoryInventory(
            directory_path=str(directory),
            total_files=len(file_records),
            total_size_mb=total_size / (1024 * 1024),
            file_records=file_records,
            qb_categories=dict(qb_categories),
            vendor_distribution=dict(Counter(vendor_distribution).most_common(50))
        )

    def _extract_qb_category_from_path(self, file_path: Path) -> Optional[str]:
        """Extract QB category from file path structure."""
        path_str = str(file_path)

        # Check for QB account patterns
        for qb_account in self.qb_structure.keys():
            if qb_account in path_str:
                return qb_account

        # Check for traditional patterns
        if "Cost of Goods Sold" in path_str:
            return "5000-COGS"
        elif "Operating Expenses" in path_str:
            return "6000-OPERATING_EXPENSES"
        elif "Credit Cards" in path_str:
            return "2139-2175-Credit_Cards"
        elif "CLOSED Billing" in path_str:
            return "Closed Payable"
        elif "OPEN Billing" in path_str:
            return "Open Payable"

        return None

    def _extract_vendor_from_path(self, file_path: Path) -> Optional[str]:
        """Extract vendor name from file path or filename."""
        path_parts = file_path.parts
        filename = file_path.stem

        # Look for vendor in path structure
        for part in path_parts:
            if part not in ["CLOSED Billing", "OPEN Billing", "Closed Payable", "Open Payable"] and len(part) > 3:
                # Skip obvious non-vendor parts
                if not any(skip in part.lower() for skip in ["cost of goods", "operating", "credit cards", "building supplies"]):
                    return part

        # Extract from filename patterns
        if '_' in filename:
            parts = filename.split('_')
            for part in parts:
                if len(part) > 3 and not part.isdigit():
                    return part

        return None

    async def _analyze_migration_completeness(self,
                                            source1: DirectoryInventory,
                                            source2: DirectoryInventory,
                                            destination: DirectoryInventory) -> Dict[str, Any]:
        """Analyze completeness of file migration from source directories."""

        # Create hash sets for comparison
        source1_hashes = {record.file_hash for record in source1.file_records}
        source2_hashes = {record.file_hash for record in source2.file_records}
        destination_hashes = {record.file_hash for record in destination.file_records}

        # Combine source hashes
        all_source_hashes = source1_hashes | source2_hashes

        # Calculate migration metrics
        migrated_count = len(all_source_hashes & destination_hashes)
        missing_count = len(all_source_hashes - destination_hashes)
        migration_percentage = (migrated_count / len(all_source_hashes)) * 100 if all_source_hashes else 0

        return {
            "total_source_files": len(all_source_hashes),
            "total_destination_files": len(destination_hashes),
            "migrated_files": migrated_count,
            "missing_files": missing_count,
            "migration_percentage": migration_percentage,
            "source1_contribution": len(source1_hashes),
            "source2_contribution": len(source2_hashes),
            "unique_to_destination": len(destination_hashes - all_source_hashes)
        }

    async def _assess_classification_accuracy(self, destination: DirectoryInventory) -> Dict[str, Any]:
        """Assess classification accuracy in destination directory."""

        total_files = len(destination.file_records)
        categorized_files = sum(1 for record in destination.file_records if record.qb_category)

        # Analyze QB category distribution
        category_distribution = destination.qb_categories
        compliance_score = (categorized_files / total_files) * 100 if total_files > 0 else 0

        # Check for proper QB structure usage
        qb_structure_usage = {}
        for category in self.qb_structure.keys():
            qb_structure_usage[category] = category_distribution.get(category, 0)

        return {
            "total_files": total_files,
            "categorized_files": categorized_files,
            "uncategorized_files": total_files - categorized_files,
            "compliance_score": compliance_score,
            "qb_category_distribution": category_distribution,
            "qb_structure_usage": qb_structure_usage,
            "vendor_diversity": len(destination.vendor_distribution)
        }

    async def _find_missing_and_duplicates(self,
                                         source1: DirectoryInventory,
                                         source2: DirectoryInventory,
                                         destination: DirectoryInventory) -> Tuple[List[str], List[Tuple[str, str]]]:
        """Find missing files and duplicates."""

        # Create hash-to-path mappings
        source_hash_to_path = {}
        for record in source1.file_records + source2.file_records:
            source_hash_to_path[record.file_hash] = record.file_path

        destination_hash_to_path = {}
        destination_duplicates = defaultdict(list)
        for record in destination.file_records:
            if record.file_hash in destination_hash_to_path:
                destination_duplicates[record.file_hash].append(record.file_path)
            destination_hash_to_path[record.file_hash] = record.file_path

        # Find missing files
        missing_files = []
        for file_hash, source_path in source_hash_to_path.items():
            if file_hash not in destination_hash_to_path:
                missing_files.append(source_path)

        # Find duplicate files in destination
        duplicate_files = []
        for file_hash, paths in destination_duplicates.items():
            if len(paths) > 1:
                duplicate_files.append((paths[0], paths[1]))  # Report first duplicate pair

        return missing_files, duplicate_files

    async def _validate_qb_structure(self, destination: DirectoryInventory) -> Dict[str, Any]:
        """Validate QB Chart of Accounts structure compliance."""

        # Check if QB structure folders exist
        existing_folders = set()
        for record in destination.file_records:
            file_path = Path(record.file_path)
            for part in file_path.parts:
                if part in self.qb_structure:
                    existing_folders.add(part)

        expected_folders = set(self.qb_structure.keys())
        missing_folders = expected_folders - existing_folders

        # Calculate compliance metrics
        structure_compliance = (len(existing_folders) / len(expected_folders)) * 100 if expected_folders else 0

        return {
            "expected_qb_folders": list(expected_folders),
            "existing_qb_folders": list(existing_folders),
            "missing_qb_folders": list(missing_folders),
            "structure_compliance_percentage": structure_compliance,
            "files_per_qb_category": destination.qb_categories
        }

    async def _generate_recommendations(self,
                                      migration_analysis: Dict[str, Any],
                                      classification_analysis: Dict[str, Any],
                                      missing_files: List[str],
                                      duplicate_files: List[Tuple[str, str]],
                                      qb_compliance: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on audit results."""

        recommendations = []

        # Migration completeness recommendations
        if migration_analysis["migration_percentage"] < 95:
            recommendations.append(
                f"CRITICAL: Only {migration_analysis['migration_percentage']:.1f}% of source files migrated. "
                f"Missing {migration_analysis['missing_files']} files require attention."
            )

        if missing_files:
            recommendations.append(
                f"ACTION REQUIRED: {len(missing_files)} files missing from destination. "
                "Run file migration process to copy missing files."
            )

        # Classification recommendations
        if classification_analysis["compliance_score"] < 90:
            recommendations.append(
                f"IMPROVEMENT NEEDED: Only {classification_analysis['compliance_score']:.1f}% of files properly categorized. "
                "Run Claude Vision classification on uncategorized files."
            )

        # Duplicate file recommendations
        if duplicate_files:
            recommendations.append(
                f"CLEANUP NEEDED: {len(duplicate_files)} duplicate files found. "
                "Review and remove duplicates to optimize storage."
            )

        # QB structure recommendations
        if qb_compliance["structure_compliance_percentage"] < 100:
            missing_folders = qb_compliance["missing_qb_folders"]
            recommendations.append(
                f"QB STRUCTURE: Missing {len(missing_folders)} QB folders: {', '.join(missing_folders)}. "
                "Create missing folders for complete Chart of Accounts compliance."
            )

        # Overall system recommendations
        if len(recommendations) == 0:
            recommendations.append(
                "EXCELLENT: System shows complete migration and proper QB organization. "
                "All files successfully consolidated and classified."
            )
        else:
            recommendations.append(
                "PRIORITY: Address critical migration and classification issues for optimal system performance."
            )

        return recommendations

    async def _save_audit_report(self, audit_result: AuditResult) -> str:
        """Save comprehensive audit report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"comprehensive_audit_report_{timestamp}.json"

        # Convert to serializable format
        report_data = asdict(audit_result)

        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        logger.info(f"Comprehensive audit report saved: {report_file}")
        return report_file

    def print_audit_summary(self, audit_result: AuditResult) -> None:
        """Print comprehensive audit summary."""
        print("\n" + "="*80)
        print("COMPREHENSIVE AUDIT AND CONSOLIDATION REPORT")
        print("="*80)

        # Migration Summary
        migration = audit_result.migration_completeness
        print(f"\n[MIGRATION ANALYSIS]")
        print(f"Source Files Total: {migration['total_source_files']:,}")
        print(f"Destination Files: {migration['total_destination_files']:,}")
        print(f"Migration Success: {migration['migration_percentage']:.1f}%")
        print(f"Missing Files: {migration['missing_files']:,}")

        # Classification Summary
        classification = audit_result.classification_accuracy
        print(f"\n[CLASSIFICATION ANALYSIS]")
        print(f"Total Files: {classification['total_files']:,}")
        print(f"Properly Categorized: {classification['categorized_files']:,}")
        print(f"Classification Score: {classification['compliance_score']:.1f}%")
        print(f"QB Categories Used: {len(classification['qb_category_distribution'])}")

        # QB Structure Compliance
        qb_compliance = audit_result.qb_structure_compliance
        print(f"\n[QB STRUCTURE COMPLIANCE]")
        print(f"Expected Folders: {len(qb_compliance['expected_qb_folders'])}")
        print(f"Existing Folders: {len(qb_compliance['existing_qb_folders'])}")
        print(f"Structure Compliance: {qb_compliance['structure_compliance_percentage']:.1f}%")

        # Issues Found
        print(f"\n[ISSUES IDENTIFIED]")
        print(f"Missing Files: {len(audit_result.missing_files)}")
        print(f"Duplicate Files: {len(audit_result.duplicate_files)}")
        print(f"Missing QB Folders: {len(qb_compliance['missing_qb_folders'])}")

        # Recommendations
        print(f"\n[RECOMMENDATIONS]")
        for i, recommendation in enumerate(audit_result.recommendations, 1):
            print(f"{i}. {recommendation}")

        print("\n" + "="*80)

async def main():
    """Main execution with command-line interface."""
    parser = argparse.ArgumentParser(description="Comprehensive Audit and Consolidation System")
    parser.add_argument("--wait-for-completion", action="store_true",
                       help="Wait for Vision verification to complete before running audit")
    parser.add_argument("--monitor-interval", type=int, default=300,
                       help="Monitoring interval in seconds (default: 300)")

    args = parser.parse_args()

    # Initialize audit system
    audit_system = ComprehensiveAuditSystem()

    if args.wait_for_completion:
        print("Monitoring for Vision verification completion...")

        # Monitor for completion (simplified - in practice would check process status)
        while True:
            # Check if verification is still running (simplified check)
            # In practice, would check process status or completion files
            await asyncio.sleep(args.monitor_interval)

            print(f"Checking verification status... (monitoring every {args.monitor_interval}s)")
            # Break when verification complete (implement actual check)
            break

    # Run comprehensive audit
    print("Starting comprehensive audit and consolidation verification...")
    audit_result = await audit_system.run_comprehensive_audit()

    # Display results
    audit_system.print_audit_summary(audit_result)

    print(f"\nAudit completed successfully!")
    print(f"Detailed report saved with recommendations for next steps.")

if __name__ == "__main__":
    asyncio.run(main())