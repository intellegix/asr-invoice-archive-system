"""
Automated Audit Trigger System
Monitors Claude Vision verification completion and triggers comprehensive audit
"""

import asyncio
import json
import time
import subprocess
import psutil
from datetime import datetime
from pathlib import Path

class AutoAuditTrigger:
    """Automated system to trigger audit after verification completion."""

    def __init__(self):
        self.verification_process_name = "python"
        self.verification_script = "execute_comprehensive_auto.py"
        self.monitoring_interval = 30  # seconds
        self.max_monitoring_time = 86400  # 24 hours max

    async def monitor_and_trigger_audit(self):
        """Monitor verification completion and trigger comprehensive audit."""
        print("="*70)
        print("AUTOMATED AUDIT TRIGGER SYSTEM ACTIVATED")
        print("="*70)
        print(f"Monitoring for completion of: {self.verification_script}")
        print(f"Check interval: {self.monitoring_interval} seconds")
        print(f"Maximum monitoring time: {self.max_monitoring_time/3600:.1f} hours")
        print()

        start_monitoring = time.time()

        while time.time() - start_monitoring < self.max_monitoring_time:
            # Check if verification process is still running
            verification_running = self._is_verification_running()

            if verification_running:
                elapsed = time.time() - start_monitoring
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Verification still running... "
                      f"(Elapsed: {elapsed/3600:.1f}h)")
                await asyncio.sleep(self.monitoring_interval)
                continue

            # Verification completed - wait a moment for cleanup
            print("\n" + "="*70)
            print("VERIFICATION COMPLETION DETECTED!")
            print("="*70)
            print("Waiting 60 seconds for process cleanup...")
            await asyncio.sleep(60)

            # Trigger comprehensive audit
            await self._trigger_comprehensive_audit()
            break

        else:
            print(f"\nMonitoring timeout reached ({self.max_monitoring_time/3600:.1f} hours)")
            print("Manual audit trigger may be required")

    def _is_verification_running(self) -> bool:
        """Check if verification process is still running."""
        for process in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if process.info['name'] == self.verification_process_name:
                    cmdline = ' '.join(process.info['cmdline'] or [])
                    if self.verification_script in cmdline:
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    async def _trigger_comprehensive_audit(self):
        """Trigger the comprehensive audit system."""
        print("INITIATING COMPREHENSIVE AUDIT SYSTEM...")
        print("="*70)

        try:
            # Run comprehensive audit
            result = subprocess.run([
                "python", "comprehensive_audit_system.py"
            ], capture_output=True, text=True, timeout=3600)  # 1 hour timeout

            if result.returncode == 0:
                print("[SUCCESS] Comprehensive audit completed successfully!")
                print("\nAudit Output:")
                print("-" * 50)
                print(result.stdout)
                if result.stderr:
                    print("\nAudit Warnings/Info:")
                    print("-" * 50)
                    print(result.stderr)
            else:
                print(f"[ERROR] Audit failed with return code: {result.returncode}")
                print(f"Error output: {result.stderr}")

        except subprocess.TimeoutExpired:
            print("[TIMEOUT] Audit process exceeded 1 hour timeout")
        except Exception as e:
            print(f"[EXCEPTION] Failed to run audit: {e}")

        # Generate final summary
        await self._generate_final_summary()

    async def _generate_final_summary(self):
        """Generate final summary of entire process."""
        print("\n" + "="*70)
        print("COMPLETE PROCESS SUMMARY")
        print("="*70)

        # Check for audit report files
        audit_reports = list(Path(".").glob("comprehensive_audit_report_*.json"))
        verification_reports = list(Path(".").glob("claude_vision_verification_report_*.json"))

        print(f"Vision Verification Reports: {len(verification_reports)}")
        print(f"Comprehensive Audit Reports: {len(audit_reports)}")

        if audit_reports:
            # Read latest audit report
            latest_audit = max(audit_reports, key=lambda p: p.stat().st_mtime)
            try:
                with open(latest_audit, 'r') as f:
                    audit_data = json.load(f)

                print(f"\nLatest Audit Report: {latest_audit}")
                print("-" * 50)

                # Extract key metrics
                migration = audit_data.get('migration_completeness', {})
                classification = audit_data.get('classification_accuracy', {})

                print(f"Migration Success: {migration.get('migration_percentage', 0):.1f}%")
                print(f"Classification Score: {classification.get('compliance_score', 0):.1f}%")
                print(f"Total Files Processed: {classification.get('total_files', 0):,}")

                recommendations = audit_data.get('recommendations', [])
                print(f"\nKey Recommendations: {len(recommendations)}")
                for i, rec in enumerate(recommendations[:3], 1):  # Show top 3
                    print(f"{i}. {rec[:100]}...")

            except Exception as e:
                print(f"Could not read audit report: {e}")

        print("\n" + "="*70)
        print("AUTOMATED PROCESS COMPLETE")
        print("="*70)
        print("Next Steps:")
        print("1. Review audit report for any issues identified")
        print("2. Implement recommendations if needed")
        print("3. Verify QB organization meets business requirements")
        print("4. System ready for production use")

async def main():
    """Main execution."""
    trigger_system = AutoAuditTrigger()
    await trigger_system.monitor_and_trigger_audit()

if __name__ == "__main__":
    asyncio.run(main())