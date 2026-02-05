"""
Auto-execute comprehensive Claude Vision verification without user prompts
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from claude_vision_verifier import ClaudeVisionVerifier
from config.settings import settings

async def run_comprehensive_auto(target_dir: str):
    """Run comprehensive verification automatically without prompts."""

    # Ensure API key is loaded
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        # Try reading from API key file
        api_key_file = r"C:\Users\AustinKidwell\ASR Dropbox\Austin Kidwell\02.02_ApiKeys\Claude\claude api keys.txt"
        try:
            with open(api_key_file, 'r') as f:
                api_key = f.read().strip()
                os.environ["ANTHROPIC_API_KEY"] = api_key
                print("[OK] API key loaded from file")
        except FileNotFoundError:
            print("ERROR: API key not configured")
            return

    verifier = ClaudeVisionVerifier(target_dir)

    print(f"Starting comprehensive Claude Vision verification...")
    print(f"Target directory: {target_dir}")

    # Count documents
    total_docs = len(await verifier._collect_all_documents())
    print(f"Found {total_docs:,} documents to process")

    # Automatically proceed with comprehensive verification
    try:
        result = await verifier.run_comprehensive_verification()

        print("\n" + "="*60)
        print("COMPREHENSIVE VERIFICATION COMPLETED")
        print("="*60)
        print(f"Target Directory: {target_dir}")
        print(f"Total Documents Analyzed: {result.total_documents_analyzed:,}")
        print(f"Total Processing Cost: ${result.total_processing_cost:.2f}")
        print(f"Average Confidence Score: {result.average_confidence_score:.2f}")
        print(f"Classification Improvements: {result.classification_improvements:,}")
        print(f"Payment Status Improvements: {result.payment_status_improvements:,}")
        print(f"GL Account Optimizations: {result.gl_account_optimizations:,}")
        print(f"Failed Document Recoveries: {result.failed_document_recoveries:,}")

        # Quality metrics
        if result.quality_metrics:
            print(f"Overall Success Rate: {result.quality_metrics.get('overall_success_rate', 0):.1f}%")
            print(f"Improvement Rate: {result.quality_metrics.get('improvement_rate', 0):.1f}%")

        print("="*60)
        print(f"[COMPLETE] Directory {target_dir.split('/')[-1]} processing complete!")

        return result

    except Exception as e:
        print(f"Comprehensive verification failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Process both directories automatically."""

    # Directory 1 - Partial QB organization (where pilot was successful)
    dir1 = "C:/Users/AustinKidwell/ASR Dropbox/Austin Kidwell/08_Financial_PayrollOperations/Digital Billing Records (QB Organized)"

    # Directory 2 - Complete QB Chart of Accounts structure
    dir2 = "C:/Users/AustinKidwell/ASR Dropbox/Austin Kidwell/Digital Billing Records (QB Organized)"

    print("[STARTING] COMPREHENSIVE CLAUDE VISION VERIFICATION - DUAL DIRECTORY PROCESSING")
    print("="*80)

    results = []

    # Process Directory 1
    print(f"\n[PHASE 1] Processing Directory 1 (Validated by pilot)")
    print(f"Path: {dir1}")
    result1 = await run_comprehensive_auto(dir1)
    if result1:
        results.append(("Directory 1", result1))

    # Process Directory 2
    print(f"\n[PHASE 2] Processing Directory 2 (Complete QB structure)")
    print(f"Path: {dir2}")
    result2 = await run_comprehensive_auto(dir2)
    if result2:
        results.append(("Directory 2", result2))

    # Summary Report
    print("\n" + "="*80)
    print("[SUCCESS] DUAL DIRECTORY PROCESSING COMPLETE - FINAL SUMMARY")
    print("="*80)

    total_documents = 0
    total_cost = 0.0
    total_improvements = 0

    for name, result in results:
        print(f"\n{name}:")
        print(f"  Documents Processed: {result.total_documents_analyzed:,}")
        print(f"  Processing Cost: ${result.total_processing_cost:.2f}")
        print(f"  Classification Improvements: {result.classification_improvements:,}")
        print(f"  Average Confidence: {result.average_confidence_score:.2f}")

        total_documents += result.total_documents_analyzed
        total_cost += result.total_processing_cost
        total_improvements += result.classification_improvements

    print(f"\n[TOTALS] COMBINED RESULTS:")
    print(f"  Total Documents Processed: {total_documents:,}")
    print(f"  Total Processing Cost: ${total_cost:.2f}")
    print(f"  Total Classification Improvements: {total_improvements:,}")
    print(f"  Improvement Rate: {(total_improvements/total_documents)*100:.1f}%")
    print(f"  Cost per Document: ${total_cost/total_documents:.4f}")

    budget_used = (total_cost / 485.0) * 100
    print(f"  Budget Utilization: {budget_used:.1f}% of $485 budget")

    print("\n[SUCCESS] All QB organized directories enhanced with Claude Vision API!")
    print("[SUCCESS] Professional-grade document classification complete!")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())