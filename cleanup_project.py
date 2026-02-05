#!/usr/bin/env python3
"""
Project Cleanup Script - Move unnecessary files to DELETE folder
Organizes project directory by moving temporary, old, and obsolete files
"""

import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

def cleanup_project():
    """Move unnecessary files and folders to DELETE directory for organization."""

    project_root = Path.cwd()
    delete_folder = project_root / "DELETE"

    # Create DELETE folder if it doesn't exist
    delete_folder.mkdir(exist_ok=True)

    # Create timestamp for this cleanup operation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cleanup_folder = delete_folder / f"cleanup_{timestamp}"
    cleanup_folder.mkdir(exist_ok=True)

    print(f"[STARTING] PROJECT CLEANUP")
    print(f"Moving unnecessary files to: {cleanup_folder}")
    print("=" * 70)

    moved_count = 0
    total_size = 0

    # Files and patterns to move to DELETE
    items_to_delete = [
        # Temporary Claude files
        "tmpclaude-*",

        # System cache and git temp
        "__pycache__",
        ".git-rewrite",
        "nul",

        # Old backup directories
        "backup_20260203_*",
        "consolidation_backup_20260203_*",
        "consolidation_backups",

        # Large JSON result files (keep only the latest)
        "classification_results_1770154*.json",
        "deduplication_report_1770157*.json",
        "scan_audit_1770154*.json",
        "scan_audit_1770155*.json",
        "scan_audit_1770157*.json",
        "consolidation_report_20260203_*.json",
        "actual_consolidation_results.json",
        "local_only_consolidation_results.json",
        "cost_effective_duplicate_results.json",
        "clark_migration_log_20260115_083347.json",
        "document_consolidation_execution_report.json",
        "document_only_processing_plan.json",

        # Old log files
        "consolidation_execution.log",
        "consolidation_progress.log",
        "consolidation_test.log",
        "asr_system.log",
        "qb_classification.log",
        "qb_validation.log",
        "qb_validation_simple.log",
        "comprehensive_audit.log",
        "comprehensive_audit_fixed.log",

        # Old deployment and configuration files
        "backend-demo-task-def*.json",
        "backend-production-task-def*.json",
        "backend-simple-task-def.json",
        "backend-working-task-def.json",
        "current-backend-*.json",
        "current-task-def.json",
        "fastapi-backend-task.json",
        "frontend-placeholder-task.json",
        "frontend-production-task-def.json",
        "production-backend-task.json",
        "production-fastapi-task.json",
        "public-fastapi-test.json",
        "reliable-fastapi-task.json",
        "simple-backend-task.json",
        "simple-test-fastapi.json",
        "corrected-fastapi-task.json",
        "fixed-backend-task-def.json",
        "health-rule.json",
        "ecs-execution-role-trust.json",

        # CodeBuild files
        "codebuild-*.json",
        "buildspec.yml",
        "buildspec-production.yml",

        # Old shell scripts and automation
        "admin-fix.sh",
        "build-and-push-containers.sh",
        "build-simulation.py",
        "COMPLETE_DEPLOYMENT_SIMULATION.sh",
        "deploy-containers.sh",
        "deploy-ecs-services.sh",
        "deploy-iam-roles.sh",
        "deploy-production.sh",
        "daily-health-check.sh",
        "execute-build-simulation.sh",
        "EXECUTE_PRODUCTION_DEPLOYMENT.sh",
        "setup-cloudshell-environment.sh",
        "setup-monitoring.py",
        "create-cloudwatch-dashboard.py",
        "create-monitoring.py",
        "cost-monitoring-setup.py",
        "prepare-cloudshell-package.ps1",
        "test-db-connection.py",
        "validate-deployment.sh",
        "validate_27k_scale_config.py",

        # Test and development files
        "test_consolidation*.py",
        "test_duplicate_detection.py",
        "test_integration.py",
        "test_invoice.pdf",
        "test_relay_only.py",
        "test_setup.py",
        "test_system.py",
        "test_template_workflow.py",
        "simple_test.py",
        "simple_consolidation_test.py",
        "demo_system.py",
        "quick_build.py",
        "scanner_integration.py",

        # Old consolidation scripts
        "actual_file_consolidation.py",
        "clark_contracts_migration.py",
        "claude_duplicate_verification.py",
        "cleanup_system_files.py",
        "cost_comparison.py",
        "cost_effective_duplicate_detection.py",
        "deep_file_scan.py",
        "direct_consolidation.py",
        "execute_consolidation_plan.py",
        "execute_document_consolidation.py",
        "execute_full_consolidation.py",
        "execute_haiku_consolidation.py",
        "final_consolidation_haiku.py",
        "final_system_verification.py",
        "fixed_file_consolidation.py",
        "local_only_consolidation.py",
        "robust_consolidation.py",
        "run_consolidation*.py",
        "simple_consolidation_runner.py",
        "simple_final_verification.py",
        "simple_qb_*.py",
        "simple_validation.py",
        "simple_cleanup.py",

        # Old processing scripts
        "auto_batch_processor.py",
        "deploy_consolidation.py",
        "process_documents_only.py",
        "process_manual_review.py",
        "process_scanned_docs.py",
        "pdf_text_extractor.py",
        "pdf_to_image_converter.py",
        "fix_all_unicode.py",
        "fix_unicode_emojis.py",
        "install_dependencies.py",
        "simulate-build-process.py",
        "start_local_system.py",

        # Archive files
        "terraform_1.6.6_*.zip",
        "files (6).zip",

        # Old documentation and reports (keeping essential ones)
        "27K_SCALE_EXECUTION_READINESS.md",
        "admin-setup-instructions.md",
        "ASR_RECORDS_DEPLOYMENT_SOP.md",
        "AWS_*.md",
        "BUDGET_ALIGNED_DMS_COSTS.md",
        "BUILD_READINESS_REPORT.md",
        "CLARK_CONTRACTS_MIGRATION_FINAL_REPORT.md",
        "CLAUDE_AI_INTEGRATION_GUIDE.md",
        "CLOUDSHELL_UPLOAD_INSTRUCTIONS.md",
        "COMPREHENSIVE_DMS_FINE_TUNING_COSTS.md",
        "consolidation_execution_summary.md",
        "CONSOLIDATION_QUICK_START.md",
        "CONTAINER_DEPLOYMENT_*.md",
        "container-deployment-guide.md",
        "DEPLOYMENT_*.md",
        "deployment-verification-report.md",
        "DIRECT_AWS_API_DEPLOYMENT.md",
        "FINAL_SUCCESS_REPORT.md",
        "IMMEDIATE_NEXT_STEPS.md",
        "IMPLEMENTATION_*.md",
        "Intellegix_DocSort_Plan.md",
        "Invoice_Matching_Plan.md",
        "MANUAL_DEPLOYMENT_RESULTS.md",
        "NEXT_STEPS_EXECUTION_REPORT.md",
        "operational-procedures.md",
        "PARALLEL_CONSOLIDATION_README.md",
        "PERSISTENT_AI_GUIDE.md",
        "PRODUCTION_DEPLOYMENT_GUIDE.md",
        "QB_ORGANIZATION_FINAL_SUCCESS_REPORT.md",
        "QB_VALIDATION_SUCCESS_REPORT.md",
        "RELAY_DEPLOYMENT_GUIDE.md",
        "TENANT_ONBOARDING_GUIDE.md",
        "setup_vision_verification.md",

        # Database and audit files
        "consolidation_audit.db",
        "file_consolidation_audit.db",
        "consolidation_requirements.txt",
        "consolidation_results*.json",
        "consolidation_scan_results.json",
        "consolidation_validation_report.json",
        "duplicate_detection_test_report.json",
        "final_verification_report.json",
        "fixed_consolidation_results.json",
        "qb_validation_report_*.json",
        "template_workflow_validation.json",
        "verify_cost_calculation.py",

        # Old directories
        "anomaly detection logic",
        "asr-records-legacy",
        "build",
        "client",
        "data",
        "dist",
        "docsort-client",
        "file-watcher",
        "invoice-archive-system",
        "logs",
        "NextSteps",
        "records retreival system",
        "records_consolidation_system",
        "relay",
        "shared_dropbox",

        # Spec files and old documents
        "ASR_Document_Uploader.spec",
        "ASR_Invoice_Archive_Server.spec",
        "invoice_archive_components.csv",
        "invoice-archive-blueprint",
        "architecture_diagram.png",
        "~$c System Architecture.docx",
        "run_vision_pilot.bat",

        # Keep only essential current files, move everything else
    ]

    # Get list of all items in current directory
    all_items = list(project_root.iterdir())

    # Essential files to KEEP (do not move to DELETE)
    essential_files = {
        ".env", ".env.example", ".env.relay",
        ".git", ".gitignore", ".claude",
        "CLAUDE.md", "README.md", "START_HERE.md", "SETUP_GUIDE.md", "QUICK_START.md",
        "requirements.txt", "render.yaml",
        "config", "services", "models", "api",
        "main_app.py", "process_qb_classification.py",
        "claude_vision_verifier.py", "execute_comprehensive_auto.py",
        "comprehensive_audit_system.py", "comprehensive_audit_system_fixed.py",
        "auto_audit_trigger.py", "run_audit_now.py",
        "execute_vision_verification.py",
        "create_qb_structure.py", "validate_qb_organization.py",
        "RecordsManager_Blueprint.md",
        "Doc System Architecture.docx",
        "Closed Invoice Archive System - Complete Blueprint.md",
        "WHATS_NEW.md",
        # Keep the latest audit and verification reports
        "comprehensive_audit_report_20260204_124012.json",
        "comprehensive_audit_report_FIXED_20260204_125452.json",
        "claude_vision_verification_report_20260204_125832.json",
        "claude_vision_verification.log",
        # Keep current billing directories
        "CLOSED Billing", "OPEN Billing", "Digital Billing Records",
        "DELETE"  # Don't move the DELETE folder itself!
    }

    # Move items that match deletion patterns
    for item in all_items:
        item_name = item.name
        should_delete = False

        # Skip essential files
        if item_name in essential_files:
            continue

        # Check if item matches any deletion pattern
        for pattern in items_to_delete:
            if "*" in pattern:
                # Handle wildcard patterns
                prefix = pattern.split("*")[0]
                suffix = pattern.split("*")[-1] if pattern.count("*") == 1 else ""
                if item_name.startswith(prefix) and item_name.endswith(suffix):
                    should_delete = True
                    break
            else:
                # Exact match
                if item_name == pattern:
                    should_delete = True
                    break

        # Move item to DELETE folder
        if should_delete:
            try:
                destination = cleanup_folder / item_name

                # Calculate size before moving
                if item.is_file():
                    size = item.stat().st_size
                    total_size += size
                elif item.is_dir():
                    size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                    total_size += size

                # Move the item
                shutil.move(str(item), str(destination))
                moved_count += 1

                if item.is_dir():
                    print(f"[DIR] Moved directory: {item_name}")
                else:
                    print(f"[FILE] Moved file: {item_name}")

            except Exception as e:
                print(f"[ERROR] Error moving {item_name}: {e}")

    # Summary
    print("\n" + "=" * 70)
    print(f"[SUCCESS] CLEANUP COMPLETE!")
    print(f"Items moved: {moved_count:,}")
    print(f"Total size moved: {total_size / (1024 * 1024):.2f} MB")
    print(f"Items moved to: {cleanup_folder}")
    print("=" * 70)
    print("\nProject directory is now organized and clean!")
    print("All unnecessary files are safely stored in the DELETE folder")

if __name__ == "__main__":
    cleanup_project()