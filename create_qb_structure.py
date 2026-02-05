#!/usr/bin/env python3
"""
QB Chart of Accounts Structure Creator
Creates complete QuickBooks Chart of Accounts folder structure
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QBStructureCreator:
    """Create QB Chart of Accounts folder structure."""

    def __init__(self, target_directory: str, dry_run: bool = True):
        """Initialize QB structure creator."""
        self.target_directory = Path(target_directory)
        self.dry_run = dry_run
        self.created_folders = []
        self.skipped_folders = []

    def get_complete_qb_structure(self) -> Dict[str, Any]:
        """Get complete QB Chart of Accounts structure."""
        return {
            "1000-ASSETS": {
                "1020-Banking": [
                    "Corporate_Checking",
                    "Savings_Accounts",
                    "Investment_Accounts"
                ],
                "1200-Accounts_Receivable": [],
                "1400-Current_Assets": [
                    "Inventory",
                    "Prepaid_Expenses",
                    "Other_Current_Assets"
                ],
                "1440-Fixed_Assets": [
                    "Tools_Equipment",
                    "Buildings",
                    "Vehicles",
                    "Office_Equipment",
                    "Accumulated_Depreciation"
                ],
                "1700-1900-LongTerm_Assets": [
                    "Goodwill",
                    "Other_Assets"
                ]
            },
            "2000-LIABILITIES": {
                "2000-Accounts_Payable": [],
                "2100-2200-Current_Liabilities": [
                    "Accrued_Liabilities",
                    "Payroll_Liabilities",
                    "Sales_Tax_Payable"
                ],
                "2400-2430-Loans_Payable": [
                    "Equipment_Loans",
                    "SBA_Loans",
                    "Other_Long_Term_Debt"
                ],
                "2139-2175-Credit_Cards": [
                    "AmEx",
                    "Capital_One",
                    "Home_Depot",
                    "Wells_Fargo",
                    "Other_Credit_Cards"
                ],
                "2536-2602-Equipment_Leases": [
                    "Vehicle_Leases",
                    "Equipment_Leases"
                ]
            },
            "3000-EQUITY": {
                "3100-Owners_Equity": [],
                "3200-Retained_Earnings": [],
                "3300-Distributions": []
            },
            "4000-INCOME": {
                "4060-Construction_Sales": [
                    "New_Construction",
                    "Commercial_Roofing"
                ],
                "4100-Sales": [
                    "Residential_Sales",
                    "Service_Revenue"
                ],
                "4110-Repairs": [
                    "Emergency_Repairs",
                    "Maintenance_Revenue"
                ],
                "4120-Reroofing": [
                    "Residential_Reroof",
                    "Commercial_Reroof"
                ]
            },
            "5000-COGS": {
                "5010-Roofing_Materials": [
                    "Shingles",
                    "Underlayment",
                    "Flashing",
                    "Hardware",
                    "Sealants"
                ],
                "5020-Direct_Labor": [
                    "Production_Labor",
                    "Overtime_Labor"
                ],
                "5030-Payroll_Taxes": [
                    "FICA_Employer",
                    "FUTA_SUTA",
                    "Workers_Comp"
                ]
            },
            "6000-OPERATING_EXPENSES": {
                "6075-6190-Insurance_Related": [
                    "General_Liability",
                    "Auto_Insurance",
                    "Property_Insurance",
                    "Workers_Comp_Insurance",
                    "Professional_Liability"
                ],
                "6200-6290-Professional_Services": [
                    "Accounting_Fees",
                    "Legal_Fees",
                    "Consulting",
                    "Software_Subscriptions"
                ],
                "6300-6400-Utilities_Rent": [
                    "Office_Rent",
                    "Warehouse_Rent",
                    "Electricity",
                    "Gas",
                    "Water_Sewer",
                    "Internet_Phone",
                    "Waste_Management"
                ],
                "6500-6600-Office_Admin": [
                    "Office_Supplies",
                    "Postage_Shipping",
                    "Banking_Fees",
                    "Permits_Licenses"
                ],
                "6700-6750-Equipment_Subcontractors": [
                    "Equipment_Rental",
                    "Tool_Rental",
                    "Subcontractor_Expense",
                    "Equipment_Repairs"
                ],
                "6800-6900-Taxes_Other_Expenses": [
                    "Property_Taxes",
                    "Business_Taxes",
                    "Other_Taxes",
                    "Miscellaneous"
                ]
            }
        }

    def create_folder_structure(self) -> Dict[str, Any]:
        """Create complete QB folder structure."""
        logger.info(f"🏗️  Creating QB structure ({'DRY RUN' if self.dry_run else 'LIVE'})")

        structure = self.get_complete_qb_structure()
        results = {
            "folders_created": 0,
            "folders_skipped": 0,
            "errors": [],
            "folder_list": [],
            "success": True
        }

        # Ensure target directory exists
        if not self.dry_run:
            self.target_directory.mkdir(parents=True, exist_ok=True)

        # Create folder structure
        for main_category, subcategories in structure.items():
            # Create main category folder
            main_folder = self.target_directory / main_category
            if self._create_folder(main_folder):
                results["folders_created"] += 1
                results["folder_list"].append(str(main_folder))
            else:
                results["folders_skipped"] += 1

            # Create subcategories
            for subcat_name, subcat_items in subcategories.items():
                subcat_folder = main_folder / subcat_name
                if self._create_folder(subcat_folder):
                    results["folders_created"] += 1
                    results["folder_list"].append(str(subcat_folder))
                else:
                    results["folders_skipped"] += 1

                # Create sub-items if any
                for item in subcat_items:
                    item_folder = subcat_folder / item
                    if self._create_folder(item_folder):
                        results["folders_created"] += 1
                        results["folder_list"].append(str(item_folder))
                    else:
                        results["folders_skipped"] += 1

        logger.info(f"✅ QB structure creation complete: "
                   f"{results['folders_created']} created, "
                   f"{results['folders_skipped']} skipped")

        return results

    def _create_folder(self, folder_path: Path) -> bool:
        """Create a single folder."""
        try:
            if folder_path.exists():
                logger.debug(f"📁 Folder exists: {folder_path}")
                self.skipped_folders.append(str(folder_path))
                return False

            if not self.dry_run:
                folder_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Created: {folder_path}")
            else:
                logger.info(f"🔍 Would create: {folder_path}")

            self.created_folders.append(str(folder_path))
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create {folder_path}: {str(e)}")
            return False

    def create_legacy_structure_migration(self) -> Dict[str, Any]:
        """Create folders that match legacy structure while adding QB compliance."""
        logger.info("🔄 Creating legacy-compatible QB structure...")

        # Keep existing basic structure but add QB hierarchy
        legacy_folders = [
            "CLOSED Billing",
            "OPEN Billing",
            "Closed Payable",
            "Open Payable"
        ]

        results = {
            "legacy_preserved": 0,
            "qb_structure_added": 0,
            "folders_created": []
        }

        # Preserve legacy folders
        for folder_name in legacy_folders:
            folder_path = self.target_directory / folder_name
            if not folder_path.exists():
                if self._create_folder(folder_path):
                    results["legacy_preserved"] += 1
                    results["folders_created"].append(str(folder_path))

        # Add QB structure alongside
        qb_results = self.create_folder_structure()
        results["qb_structure_added"] = qb_results["folders_created"]
        results["folders_created"].extend(qb_results["folder_list"])

        return results

    def generate_structure_report(self, results: Dict[str, Any]) -> None:
        """Generate structure creation report."""
        print(f"\n{'='*60}")
        print(f"🏗️  QB STRUCTURE CREATION REPORT")
        print(f"{'='*60}")
        print(f"📁 Target Directory: {self.target_directory}")
        print(f"🔒 Mode: {'DRY RUN' if self.dry_run else 'LIVE CREATION'}")
        print(f"✅ Folders Created: {results.get('folders_created', 0)}")
        print(f"⏭️  Folders Skipped: {results.get('folders_skipped', 0)}")
        print(f"❌ Errors: {len(results.get('errors', []))}")

        if results.get('errors'):
            print(f"\n❌ ERRORS:")
            for error in results['errors'][:5]:
                print(f"   • {error}")

        # Show sample of created folders
        folder_list = results.get('folder_list', [])
        if folder_list:
            print(f"\n📂 SAMPLE FOLDERS CREATED:")
            for folder in folder_list[:10]:  # Show first 10
                print(f"   • {folder}")
            if len(folder_list) > 10:
                print(f"   ... and {len(folder_list) - 10} more folders")

        print(f"\n🎯 QB CHART OF ACCOUNTS STRUCTURE:")
        structure = self.get_complete_qb_structure()
        for main_cat, subcats in structure.items():
            print(f"   {main_cat}/")
            for subcat in list(subcats.keys())[:3]:  # Show first 3 subcats
                print(f"     └── {subcat}/")
            if len(subcats) > 3:
                print(f"     └── ... and {len(subcats) - 3} more subcategories")

        print(f"{'='*60}")

        if results.get('folders_created', 0) > 0:
            print("✅ QB structure creation successful!")
        else:
            print("ℹ️  Structure already exists - no changes needed")

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="QB Chart of Accounts Structure Creator"
    )
    parser.add_argument(
        "--target-dir",
        default="C:/Users/AustinKidwell/ASR Dropbox/Austin Kidwell/Digital Billing Records (QB Organized)",
        help="Target directory for QB structure creation"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Perform dry run without creating folders"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute actual folder creation (overrides dry-run)"
    )
    parser.add_argument(
        "--legacy-compatible",
        action="store_true",
        help="Create structure compatible with existing legacy folders"
    )

    args = parser.parse_args()

    # Override dry_run if execute is specified
    if args.execute:
        args.dry_run = False

    # Initialize structure creator
    creator = QBStructureCreator(args.target_dir, args.dry_run)

    try:
        # Create structure
        if args.legacy_compatible:
            results = creator.create_legacy_structure_migration()
        else:
            results = creator.create_folder_structure()

        # Generate report
        creator.generate_structure_report(results)

        # Exit with appropriate code
        sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Structure creation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()