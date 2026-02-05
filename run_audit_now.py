"""
Manual Audit Trigger - Run Comprehensive Audit Immediately
Use this to run the comprehensive audit at any time
"""

import asyncio
from comprehensive_audit_system import ComprehensiveAuditSystem

async def main():
    """Run comprehensive audit immediately."""
    print("="*80)
    print("MANUAL COMPREHENSIVE AUDIT EXECUTION")
    print("="*80)
    print("This will audit all three directories and verify:")
    print("A. All files migrated from source directories")
    print("B. All files properly classified in QB organization")
    print()

    # Confirm execution
    response = input("Proceed with comprehensive audit? (yes/no): ")
    if response.lower() != 'yes':
        print("Audit cancelled")
        return

    # Initialize and run audit
    audit_system = ComprehensiveAuditSystem()
    audit_result = await audit_system.run_comprehensive_audit()

    # Display results
    audit_system.print_audit_summary(audit_result)

    print("\n[SUCCESS] Manual audit completed!")

if __name__ == "__main__":
    asyncio.run(main())