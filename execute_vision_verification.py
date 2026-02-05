"""
Execute Claude Vision API verification with immediate monitoring
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from claude_vision_verifier import ClaudeVisionVerifier
from config.settings import settings

async def run_immediate_pilot():
    """Run immediate pilot verification with 100 documents for quick validation."""

    # Set API key from environment or file
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
            print("ERROR: ANTHROPIC_API_KEY environment variable not set and API key file not found")
            print("Please set your API key:")
            print('set ANTHROPIC_API_KEY=your_api_key_here')
            return

    # Initialize verifier
    target_dir = "C:/Users/AustinKidwell/ASR Dropbox/Austin Kidwell/08_Financial_PayrollOperations/Digital Billing Records (QB Organized)"

    print("Initializing Claude Vision Verifier...")
    print(f"Target Directory: {target_dir}")

    verifier = ClaudeVisionVerifier(target_dir)

    # Check directory exists
    if not Path(target_dir).exists():
        print(f"ERROR: Target directory does not exist: {target_dir}")
        return

    try:
        # Run pilot with 100 documents for immediate feedback
        print("\nStarting pilot verification (100 documents)...")
        print("This will cost approximately $3-4 for immediate validation")

        pilot_result = await verifier.run_pilot_verification(sample_size=100)

        # Display results
        print("\n" + "="*60)
        print("PILOT VERIFICATION COMPLETED")
        print("="*60)
        print(f"Documents Processed: {pilot_result.documents_processed}")
        print(f"Success Rate: {pilot_result.successful_verifications/pilot_result.documents_processed*100:.1f}%")
        print(f"Average Confidence: {pilot_result.average_confidence:.2f}")
        print(f"Actual Cost: ${pilot_result.total_cost_usd:.2f}")
        print(f"Classification Improvements: {pilot_result.improved_classifications}")
        print(f"Payment Status Corrections: {pilot_result.payment_status_corrections}")
        print(f"Processing Time: {pilot_result.processing_time_seconds:.1f} seconds")

        # Extrapolate for full processing
        total_docs = len(await verifier._collect_all_documents())
        cost_per_doc = pilot_result.total_cost_usd / pilot_result.documents_processed
        full_cost_estimate = cost_per_doc * total_docs

        print(f"\nProjections for all {total_docs:,} documents:")
        print(f"Estimated Full Cost: ${full_cost_estimate:.2f}")
        print(f"Estimated Processing Time: {(pilot_result.processing_time_seconds / pilot_result.documents_processed) * total_docs / 60:.1f} minutes")
        print(f"Expected Improvements: {int(pilot_result.improved_classifications / pilot_result.documents_processed * total_docs):,} documents")

        if full_cost_estimate <= 485:
            print("\n✅ WITHIN BUDGET - Ready for comprehensive verification")
            print("\nTo proceed with full verification:")
            print("python execute_vision_verification.py --mode comprehensive")
        else:
            print(f"\n⚠️  OVER BUDGET - Full cost (${full_cost_estimate:.2f}) exceeds limit ($485)")
            print("Consider priority category processing instead")

        print("="*60)

    except Exception as e:
        print(f"\nERROR: Pilot verification failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check API key is valid")
        print("2. Verify network connectivity")
        print("3. Check target directory permissions")

async def run_comprehensive():
    """Run comprehensive verification on all documents."""

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

    target_dir = "C:/Users/AustinKidwell/ASR Dropbox/Austin Kidwell/08_Financial_PayrollOperations/Digital Billing Records (QB Organized)"
    verifier = ClaudeVisionVerifier(target_dir)

    print("Starting comprehensive Claude Vision verification...")
    print("This will process ALL 13,226 documents")

    # Confirm with user
    response = input("Are you sure you want to proceed? (yes/no): ")
    if response.lower() != "yes":
        print("Verification cancelled")
        return

    try:
        result = await verifier.run_comprehensive_verification()

        print("\n" + "="*60)
        print("COMPREHENSIVE VERIFICATION COMPLETED")
        print("="*60)
        print(f"Total Documents Analyzed: {result.total_documents_analyzed:,}")
        print(f"Total Processing Cost: ${result.total_processing_cost:.2f}")
        print(f"Average Confidence Score: {result.average_confidence_score:.2f}")
        print(f"Classification Improvements: {result.classification_improvements:,}")
        print(f"Payment Status Improvements: {result.payment_status_improvements:,}")
        print(f"GL Account Optimizations: {result.gl_account_optimizations:,}")
        print(f"Failed Document Recoveries: {result.failed_document_recoveries:,}")
        print("="*60)

    except Exception as e:
        print(f"Comprehensive verification failed: {e}")

async def main():
    """Main execution with mode selection."""

    if len(sys.argv) > 1 and sys.argv[1] == "--mode" and len(sys.argv) > 2:
        mode = sys.argv[2]
        if mode == "comprehensive":
            await run_comprehensive()
        elif mode == "pilot":
            await run_immediate_pilot()
        else:
            print(f"Unknown mode: {mode}")
    else:
        # Default to pilot
        await run_immediate_pilot()

if __name__ == "__main__":
    asyncio.run(main())