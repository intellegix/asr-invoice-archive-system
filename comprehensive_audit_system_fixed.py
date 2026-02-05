"""
Comprehensive Audit and Consolidation System - FIXED VERSION
Fixes calculation bugs and handles missing files gracefully
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
        logging.FileHandler('comprehensive_audit_fixed.log'),
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
    exists: bool = True

@dataclass
class DirectoryInventory:
    """Complete inventory of a directory with accurate counts."""
    directory_path: str
    total_files: int
    total_accessible_files: int  # NEW: Files that actually exist and are readable
    total_missing_files: int     # NEW: Files in structure but missing
    total_size_mb: float
    file_records: List[FileRecord]
    qb_categories: Dict[str, int]
    vendor_distribution: Dict[str, int]
    scan_statistics: Dict[str, int]  # NEW: Statistics about the scan

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

class ComprehensiveAuditSystemFixed:
    """FIXED: Complete audit system with accurate file counting."""

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
        """Run complete audit with FIXED calculations."""
        logger.info("Starting FIXED comprehensive audit...")
        start_time = time.time()

        # Phase 1: Inventory all directories with accurate counting
        logger.info("Phase 1: Creating accurate directory inventories...")
        source1_inventory = await self._create_directory_inventory_fixed(self.source_dir1, "Source Directory 1")
        source2_inventory = await self._create_directory_inventory_fixed(self.source_dir2, "Source Directory 2")
        destination_inventory = await self._create_directory_inventory_fixed(self.destination_dir, "Destination Directory")

        # Phase 2: Migration completeness analysis (FIXED)
        logger.info("Phase 2: Analyzing migration completeness with accurate metrics...")
        migration_analysis = await self._analyze_migration_completeness_fixed(
            source1_inventory, source2_inventory, destination_inventory
        )

        # Phase 3: Classification accuracy assessment (FIXED)
        logger.info("Phase 3: Assessing classification accuracy with proper calculations...")
        classification_analysis = await self._assess_classification_accuracy_fixed(destination_inventory)

        # Phase 4: Find missing and duplicate files
        logger.info("Phase 4: Identifying missing and duplicate files...")
        missing_files, duplicate_files = await self._find_missing_and_duplicates_fixed(
            source1_inventory, source2_inventory, destination_inventory
        )

        # Phase 5: QB structure compliance check
        logger.info("Phase 5: Validating QB structure compliance...")
        qb_compliance = await self._validate_qb_structure(destination_inventory)

        # Phase 6: Generate recommendations
        logger.info("Phase 6: Generating recommendations...")
        recommendations = await self._generate_recommendations_fixed(
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
            misclassified_files=[],
            qb_structure_compliance=qb_compliance,
            recommendations=recommendations
        )

        processing_time = time.time() - start_time
        logger.info(f"FIXED comprehensive audit completed in {processing_time:.2f} seconds")

        # Save detailed audit report
        await self._save_audit_report_fixed(audit_result)

        return audit_result

    async def _create_directory_inventory_fixed(self, directory: Path, dir_name: str) -> DirectoryInventory:
        """FIXED: Create accurate inventory counting existing vs missing files."""
        logger.info(f"Scanning {dir_name}: {directory}")

        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return DirectoryInventory(
                directory_path=str(directory),
                total_files=0,
                total_accessible_files=0,
                total_missing_files=0,
                total_size_mb=0.0,
                file_records=[],
                qb_categories={},
                vendor_distribution={},
                scan_statistics={"directories_scanned": 0, "files_attempted": 0, "files_accessible": 0, "files_missing": 0}
            )

        file_records = []
        total_size = 0
        accessible_count = 0
        missing_count = 0
        qb_categories = defaultdict(int)
        vendor_distribution = defaultdict(int)

        directories_scanned = 0
        files_attempted = 0

        # Scan directory structure
        for root, dirs, files in os.walk(directory):
            directories_scanned += 1

            for file in files:
                if file.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.tiff')):
                    files_attempted += 1
                    file_path = Path(root) / file

                    # Check if file actually exists and is accessible
                    try:
                        if not file_path.exists():
                            missing_count += 1
                            logger.debug(f"Missing file: {file_path}")

                            # Still track QB category for missing files
                            qb_category = self._extract_qb_category_from_path(file_path)
                            if qb_category:
                                qb_categories[qb_category] += 1

                            # Create record for missing file
                            file_record = FileRecord(
                                file_path=str(file_path),
                                file_name=file,
                                file_hash="MISSING",
                                file_size=0,
                                directory_source=dir_name,
                                qb_category=qb_category,
                                vendor_extracted=self._extract_vendor_from_path(file_path),
                                modification_time=0.0,
                                exists=False
                            )
                            file_records.append(file_record)
                            continue

                        # File exists - get full metadata
                        file_size = file_path.stat().st_size
                        modification_time = file_path.stat().st_mtime
                        total_size += file_size
                        accessible_count += 1

                        # Calculate file hash for accessible files
                        try:
                            with open(file_path, 'rb') as f:
                                file_hash = hashlib.sha256(f.read()).hexdigest()
                        except Exception as e:
                            logger.warning(f"Could not hash file {file_path}: {e}")
                            file_hash = "HASH_ERROR"

                        # Extract QB category and vendor
                        qb_category = self._extract_qb_category_from_path(file_path)
                        if qb_category:
                            qb_categories[qb_category] += 1

                        vendor = self._extract_vendor_from_path(file_path)
                        if vendor:
                            vendor_distribution[vendor] += 1

                        file_record = FileRecord(
                            file_path=str(file_path),
                            file_name=file,
                            file_hash=file_hash,
                            file_size=file_size,
                            directory_source=dir_name,
                            qb_category=qb_category,
                            vendor_extracted=vendor,
                            modification_time=modification_time,
                            exists=True
                        )
                        file_records.append(file_record)

                    except Exception as e:
                        missing_count += 1
                        logger.warning(f"Could not access file {file_path}: {e}")

                        # Track as missing file
                        qb_category = self._extract_qb_category_from_path(file_path)
                        if qb_category:
                            qb_categories[qb_category] += 1

        scan_stats = {
            "directories_scanned": directories_scanned,
            "files_attempted": files_attempted,
            "files_accessible": accessible_count,
            "files_missing": missing_count
        }

        logger.info(f"{dir_name} scan complete: {files_attempted} files attempted, {accessible_count} accessible, {missing_count} missing")

        return DirectoryInventory(
            directory_path=str(directory),
            total_files=files_attempted,  # Total files found in structure
            total_accessible_files=accessible_count,  # Files that actually exist
            total_missing_files=missing_count,  # Files missing from structure
            total_size_mb=total_size / (1024 * 1024),
            file_records=file_records,
            qb_categories=dict(qb_categories),
            vendor_distribution=dict(Counter(vendor_distribution).most_common(50)),
            scan_statistics=scan_stats
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

    async def _analyze_migration_completeness_fixed(self,
                                                   source1: DirectoryInventory,
                                                   source2: DirectoryInventory,
                                                   destination: DirectoryInventory) -> Dict[str, Any]:
        """FIXED: Analyze migration with accurate file counts."""

        # Only count accessible files for hash comparison
        source1_hashes = {record.file_hash for record in source1.file_records if record.exists and record.file_hash != "MISSING"}
        source2_hashes = {record.file_hash for record in source2.file_records if record.exists and record.file_hash != "MISSING"}
        destination_hashes = {record.file_hash for record in destination.file_records if record.exists and record.file_hash != "MISSING"}

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
            "unique_to_destination": len(destination_hashes - all_source_hashes),
            # NEW: File accessibility metrics
            "source1_accessible": source1.total_accessible_files,
            "source2_accessible": source2.total_accessible_files,
            "destination_accessible": destination.total_accessible_files,
            "total_missing_files": source1.total_missing_files + source2.total_missing_files + destination.total_missing_files
        }

    async def _assess_classification_accuracy_fixed(self, destination: DirectoryInventory) -> Dict[str, Any]:
        """FIXED: Assess classification accuracy with proper file counts."""

        total_files = destination.total_accessible_files  # Only count accessible files
        categorized_files = sum(1 for record in destination.file_records if record.exists and record.qb_category)

        # Analyze QB category distribution (only for accessible files)
        category_distribution = {}
        for category, count in destination.qb_categories.items():
            # Count only accessible files in each category
            accessible_in_category = sum(1 for record in destination.file_records
                                       if record.exists and record.qb_category == category)
            category_distribution[category] = accessible_in_category

        compliance_score = (categorized_files / total_files) * 100 if total_files > 0 else 0

        # Check for proper QB structure usage
        qb_structure_usage = {}
        for category in self.qb_structure.keys():
            qb_structure_usage[category] = category_distribution.get(category, 0)

        return {
            "total_files": total_files,
            "total_files_in_structure": destination.total_files,  # Including missing files
            "categorized_files": categorized_files,
            "uncategorized_files": total_files - categorized_files,
            "compliance_score": compliance_score,
            "qb_category_distribution": category_distribution,
            "qb_structure_usage": qb_structure_usage,
            "vendor_diversity": len(destination.vendor_distribution),
            "accessibility_rate": (destination.total_accessible_files / destination.total_files) * 100 if destination.total_files > 0 else 0
        }

    async def _find_missing_and_duplicates_fixed(self,
                                               source1: DirectoryInventory,
                                               source2: DirectoryInventory,
                                               destination: DirectoryInventory) -> Tuple[List[str], List[Tuple[str, str]]]:
        """FIXED: Find missing files and duplicates considering accessibility."""

        # Only consider accessible files for comparison
        source_hash_to_path = {}
        for record in source1.file_records + source2.file_records:
            if record.exists and record.file_hash != "MISSING":
                source_hash_to_path[record.file_hash] = record.file_path

        destination_hash_to_path = {}
        destination_duplicates = defaultdict(list)
        for record in destination.file_records:
            if record.exists and record.file_hash != "MISSING":
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
                duplicate_files.append((paths[0], paths[1]))

        return missing_files, duplicate_files

    async def _validate_qb_structure(self, destination: DirectoryInventory) -> Dict[str, Any]:
        """Validate QB Chart of Accounts structure compliance."""

        # Check if QB structure folders exist
        existing_folders = set()
        for record in destination.file_records:
            if record.exists:  # Only consider accessible files
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

    async def _generate_recommendations_fixed(self,
                                            migration_analysis: Dict[str, Any],
                                            classification_analysis: Dict[str, Any],
                                            missing_files: List[str],
                                            duplicate_files: List[Tuple[str, str]],
                                            qb_compliance: Dict[str, Any]) -> List[str]:
        """FIXED: Generate recommendations with accurate metrics."""

        recommendations = []

        # Migration completeness recommendations
        if migration_analysis["migration_percentage"] < 95:
            recommendations.append(
                f"MIGRATION: {migration_analysis['migration_percentage']:.1f}% of accessible source files migrated. "
                f"Missing {migration_analysis['missing_files']} accessible files require attention."
            )

        # File accessibility recommendations
        total_missing = migration_analysis.get("total_missing_files", 0)
        if total_missing > 0:
            recommendations.append(
                f"FILE ACCESS: {total_missing:,} files found in directory structure but are inaccessible or missing. "
                "This may indicate moved files, broken links, or permission issues."
            )

        # Classification recommendations
        if classification_analysis["compliance_score"] < 90:
            recommendations.append(
                f"CLASSIFICATION: {classification_analysis['compliance_score']:.1f}% of accessible files properly categorized. "
                f"Run Claude Vision classification on {classification_analysis['uncategorized_files']} uncategorized files."
            )

        # Accessibility recommendations
        accessibility_rate = classification_analysis.get("accessibility_rate", 100)
        if accessibility_rate < 95:
            recommendations.append(
                f"ACCESSIBILITY: Only {accessibility_rate:.1f}% of files in directory structure are accessible. "
                "Review file locations and fix broken file paths."
            )

        # Duplicate file recommendations
        if duplicate_files:
            recommendations.append(
                f"CLEANUP: {len(duplicate_files)} duplicate files found among accessible files. "
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
                "EXCELLENT: System shows complete migration, accessible files, and proper QB organization. "
                "All files successfully consolidated and classified."
            )
        else:
            recommendations.append(
                "PRIORITY: Address file accessibility and classification issues for optimal system performance."
            )

        return recommendations

    async def _save_audit_report_fixed(self, audit_result: AuditResult) -> str:
        """Save FIXED comprehensive audit report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"comprehensive_audit_report_FIXED_{timestamp}.json"

        # Convert to serializable format
        report_data = asdict(audit_result)

        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        logger.info(f"FIXED comprehensive audit report saved: {report_file}")
        return report_file

    def print_audit_summary_fixed(self, audit_result: AuditResult) -> None:
        """Print FIXED comprehensive audit summary with accurate metrics."""
        print("\n" + "="*80)
        print("FIXED COMPREHENSIVE AUDIT AND CONSOLIDATION REPORT")
        print("="*80)

        # Migration Summary (FIXED)
        migration = audit_result.migration_completeness
        print(f"\n[MIGRATION ANALYSIS - FIXED]")
        print(f"Accessible Source Files: {migration['total_source_files']:,}")
        print(f"Accessible Destination Files: {migration['total_destination_files']:,}")
        print(f"Migration Success Rate: {migration['migration_percentage']:.1f}%")
        print(f"Missing Accessible Files: {migration['missing_files']:,}")
        print(f"Total Inaccessible Files: {migration.get('total_missing_files', 0):,}")

        # Classification Summary (FIXED)
        classification = audit_result.classification_accuracy
        print(f"\n[CLASSIFICATION ANALYSIS - FIXED]")
        print(f"Total Accessible Files: {classification['total_files']:,}")
        print(f"Files in Directory Structure: {classification['total_files_in_structure']:,}")
        print(f"Properly Categorized: {classification['categorized_files']:,}")
        print(f"Classification Score: {classification['compliance_score']:.1f}%")
        print(f"File Accessibility Rate: {classification.get('accessibility_rate', 100):.1f}%")
        print(f"QB Categories Used: {len(classification['qb_category_distribution'])}")

        # QB Structure Compliance
        qb_compliance = audit_result.qb_structure_compliance
        print(f"\n[QB STRUCTURE COMPLIANCE]")
        print(f"Expected Folders: {len(qb_compliance['expected_qb_folders'])}")
        print(f"Existing Folders: {len(qb_compliance['existing_qb_folders'])}")
        print(f"Structure Compliance: {qb_compliance['structure_compliance_percentage']:.1f}%")

        # Issues Found (FIXED)
        print(f"\n[ISSUES IDENTIFIED - FIXED]")
        print(f"Missing Accessible Files: {len(audit_result.missing_files)}")
        print(f"Duplicate Files: {len(audit_result.duplicate_files)}")
        print(f"Inaccessible Files: {migration.get('total_missing_files', 0):,}")
        print(f"Missing QB Folders: {len(qb_compliance['missing_qb_folders'])}")

        # Recommendations
        print(f"\n[RECOMMENDATIONS - FIXED]")
        for i, recommendation in enumerate(audit_result.recommendations, 1):
            print(f"{i}. {recommendation}")

        print("\n" + "="*80)

async def main():
    """Main execution with FIXED audit system."""
    parser = argparse.ArgumentParser(description="FIXED Comprehensive Audit and Consolidation System")
    parser.add_argument("--wait-for-completion", action="store_true",
                       help="Wait for Vision verification to complete before running audit")

    args = parser.parse_args()

    # Initialize FIXED audit system
    audit_system = ComprehensiveAuditSystemFixed()

    # Run FIXED comprehensive audit
    print("Starting FIXED comprehensive audit with accurate calculations...")
    audit_result = await audit_system.run_comprehensive_audit()

    # Display results
    audit_system.print_audit_summary_fixed(audit_result)

    print(f"\nFIXED audit completed successfully!")
    print(f"Detailed report saved with accurate metrics and recommendations.")

if __name__ == "__main__":
    asyncio.run(main())