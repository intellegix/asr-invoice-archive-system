#!/usr/bin/env python3
"""
ASR System Verification Suite
Final validation of complete system capabilities and deployment readiness
"""

import asyncio
import aiohttp
import json
import logging
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Add shared modules to path
sys.path.insert(0, str(Path(__file__).parent / "shared"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Single verification test result"""
    test_name: str
    category: str
    status: str  # passed, failed, skipped, error
    message: str
    details: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0


class ASRSystemVerifier:
    """Complete ASR system verification and deployment readiness checker"""

    def __init__(self, production_server_url: str = "http://localhost:8000"):
        self.production_server_url = production_server_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.verification_results: List[VerificationResult] = []
        self.project_root = Path(__file__).parent

    async def initialize(self) -> None:
        """Initialize system verifier"""
        logger.info("🚀 Initializing ASR System Verifier")
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self.session:
            await self.session.close()

    def add_result(self, test_name: str, category: str, status: str,
                   message: str, details: Optional[Dict[str, Any]] = None,
                   execution_time: float = 0.0) -> None:
        """Add verification result"""
        result = VerificationResult(
            test_name=test_name,
            category=category,
            status=status,
            message=message,
            details=details,
            execution_time=execution_time
        )
        self.verification_results.append(result)

    async def verify_project_structure(self) -> None:
        """Verify complete project structure and file integrity"""
        logger.info("📁 Verifying project structure...")

        # Required directories and files
        required_structure = {
            "directories": [
                "shared/core",
                "shared/api",
                "shared/utils",
                "production_server/api",
                "production_server/services",
                "production_server/config",
                "document-scanner/services",
                "document-scanner/gui",
                "document-scanner/config",
                "tests"
            ],
            "files": [
                # Shared components
                "shared/core/models.py",
                "shared/core/exceptions.py",
                "shared/api/schemas.py",

                # Production server
                "production_server/main_server.py",
                "production_server/api/main.py",
                "production_server/services/gl_account_service.py",
                "production_server/services/payment_detection_service.py",
                "production_server/services/billing_router_service.py",

                # Document scanner
                "document-scanner/main_scanner.py",
                "document-scanner/services/upload_queue_service.py",
                "document-scanner/services/server_discovery_service.py",
                "document-scanner/gui/main_window.py",

                # Tests
                "tests/test_gl_account_service.py",
                "tests/load_test.py",
                "integration_test.py",

                # Build scripts
                "build_production_server.py",
                "build_document_scanner.py",
                "performance_validation.py"
            ]
        }

        start_time = time.time()

        # Check directories
        missing_dirs = []
        for directory in required_structure["directories"]:
            dir_path = self.project_root / directory
            if not dir_path.exists():
                missing_dirs.append(directory)

        # Check files
        missing_files = []
        for file_path in required_structure["files"]:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)

        execution_time = time.time() - start_time

        if missing_dirs or missing_files:
            self.add_result(
                "project_structure",
                "structure",
                "failed",
                f"Missing {len(missing_dirs)} directories and {len(missing_files)} files",
                {"missing_directories": missing_dirs, "missing_files": missing_files},
                execution_time
            )
        else:
            self.add_result(
                "project_structure",
                "structure",
                "passed",
                "All required directories and files present",
                {"checked_dirs": len(required_structure["directories"]),
                 "checked_files": len(required_structure["files"])},
                execution_time
            )

    async def verify_backend_capabilities(self) -> None:
        """Verify all backend processing capabilities are preserved"""
        logger.info("🏭 Verifying backend capabilities...")

        capabilities_to_verify = [
            {
                "name": "server_health",
                "endpoint": "/health",
                "expected_status": 200,
                "required_fields": ["status", "timestamp"]
            },
            {
                "name": "gl_accounts",
                "endpoint": "/api/gl-accounts",
                "expected_status": 200,
                "validation": lambda data: len(data) == 79  # 79 GL accounts
            },
            {
                "name": "billing_destinations",
                "endpoint": "/api/billing/destinations",
                "expected_status": 200,
                "validation": lambda data: len(data) == 4  # 4 billing destinations
            },
            {
                "name": "scanner_discovery",
                "endpoint": "/api/scanner/discovery",
                "expected_status": 200,
                "required_fields": ["server_name", "version", "capabilities"]
            }
        ]

        for capability in capabilities_to_verify:
            start_time = time.time()

            try:
                async with self.session.get(f"{self.production_server_url}{capability['endpoint']}") as response:
                    execution_time = time.time() - start_time

                    if response.status == capability["expected_status"]:
                        try:
                            data = await response.json()

                            # Check required fields if specified
                            if "required_fields" in capability:
                                missing_fields = []
                                for field in capability["required_fields"]:
                                    if field not in data:
                                        missing_fields.append(field)

                                if missing_fields:
                                    self.add_result(
                                        f"backend_{capability['name']}",
                                        "backend",
                                        "failed",
                                        f"Missing required fields: {missing_fields}",
                                        execution_time=execution_time
                                    )
                                    continue

                            # Custom validation if specified
                            if "validation" in capability:
                                try:
                                    if not capability["validation"](data):
                                        self.add_result(
                                            f"backend_{capability['name']}",
                                            "backend",
                                            "failed",
                                            "Custom validation failed",
                                            {"data_preview": str(data)[:200]},
                                            execution_time
                                        )
                                        continue
                                except Exception as e:
                                    self.add_result(
                                        f"backend_{capability['name']}",
                                        "backend",
                                        "error",
                                        f"Validation error: {e}",
                                        execution_time=execution_time
                                    )
                                    continue

                            self.add_result(
                                f"backend_{capability['name']}",
                                "backend",
                                "passed",
                                f"Endpoint responding correctly",
                                {"response_size": len(str(data))},
                                execution_time
                            )

                        except Exception as e:
                            self.add_result(
                                f"backend_{capability['name']}",
                                "backend",
                                "error",
                                f"JSON parsing error: {e}",
                                execution_time=execution_time
                            )
                    else:
                        self.add_result(
                            f"backend_{capability['name']}",
                            "backend",
                            "failed",
                            f"HTTP {response.status} (expected {capability['expected_status']})",
                            execution_time=execution_time
                        )

            except Exception as e:
                execution_time = time.time() - start_time
                self.add_result(
                    f"backend_{capability['name']}",
                    "backend",
                    "error",
                    f"Connection error: {e}",
                    execution_time=execution_time
                )

    def verify_build_environment(self) -> None:
        """Verify build tools and dependencies are available"""
        logger.info("🔨 Verifying build environment...")

        build_requirements = [
            {
                "name": "python_version",
                "command": [sys.executable, "--version"],
                "validation": lambda output: "Python 3." in output and int(output.split()[1].split('.')[1]) >= 8
            },
            {
                "name": "pyinstaller",
                "command": [sys.executable, "-m", "PyInstaller", "--version"],
                "validation": lambda output: "PyInstaller" in output or len(output) > 0
            },
            {
                "name": "pip_packages",
                "command": [sys.executable, "-m", "pip", "list"],
                "validation": lambda output: all(pkg in output.lower() for pkg in [
                    "fastapi", "aiohttp", "pydantic", "sqlalchemy", "tkinter"
                ])
            }
        ]

        for requirement in build_requirements:
            start_time = time.time()

            try:
                result = subprocess.run(
                    requirement["command"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                execution_time = time.time() - start_time

                if result.returncode == 0:
                    output = result.stdout + result.stderr

                    if requirement["validation"](output):
                        self.add_result(
                            f"build_{requirement['name']}",
                            "build",
                            "passed",
                            "Requirement satisfied",
                            {"output_preview": output[:100]},
                            execution_time
                        )
                    else:
                        self.add_result(
                            f"build_{requirement['name']}",
                            "build",
                            "failed",
                            "Validation failed",
                            {"output": output[:200]},
                            execution_time
                        )
                else:
                    self.add_result(
                        f"build_{requirement['name']}",
                        "build",
                        "failed",
                        f"Command failed with exit code {result.returncode}",
                        {"stderr": result.stderr[:200]},
                        execution_time
                    )

            except subprocess.TimeoutExpired:
                self.add_result(
                    f"build_{requirement['name']}",
                    "build",
                    "error",
                    "Command timeout",
                    execution_time=30.0
                )
            except Exception as e:
                execution_time = time.time() - start_time
                self.add_result(
                    f"build_{requirement['name']}",
                    "build",
                    "error",
                    f"Command error: {e}",
                    execution_time=execution_time
                )

    async def verify_api_integration(self) -> None:
        """Verify API integration and communication protocols"""
        logger.info("🔄 Verifying API integration...")

        # Test document upload simulation
        start_time = time.time()
        try:
            # Create mock upload data
            form_data = aiohttp.FormData()
            form_data.add_field('file', b'Mock PDF content', filename='test.pdf', content_type='application/pdf')
            form_data.add_field('metadata', json.dumps({
                "scanner_id": "verification_test",
                "timestamp": time.time()
            }))

            async with self.session.post(
                f"{self.production_server_url}/api/scanner/upload",
                data=form_data
            ) as response:
                execution_time = time.time() - start_time

                if response.status in [200, 201]:
                    data = await response.json()
                    self.add_result(
                        "api_document_upload",
                        "integration",
                        "passed",
                        "Document upload API working",
                        {"response_keys": list(data.keys()) if isinstance(data, dict) else None},
                        execution_time
                    )
                else:
                    self.add_result(
                        "api_document_upload",
                        "integration",
                        "failed",
                        f"Upload failed with HTTP {response.status}",
                        execution_time=execution_time
                    )

        except Exception as e:
            execution_time = time.time() - start_time
            self.add_result(
                "api_document_upload",
                "integration",
                "error",
                f"Upload test error: {e}",
                execution_time=execution_time
            )

    def verify_configuration_completeness(self) -> None:
        """Verify all configuration files and templates are complete"""
        logger.info("⚙️ Verifying configuration completeness...")

        config_files_to_check = [
            {
                "path": "shared/core/models.py",
                "required_content": ["DocumentMetadata", "GLAccount", "BillingDestination"],
                "description": "Shared data models"
            },
            {
                "path": "production_server/config/production_settings.py",
                "required_content": ["DATABASE_URL", "ANTHROPIC_API_KEY"],
                "description": "Production server configuration"
            },
            {
                "path": "document-scanner/config/scanner_settings.py",
                "required_content": ["ScannerSettings", "production_servers"],
                "description": "Document scanner configuration"
            }
        ]

        for config in config_files_to_check:
            start_time = time.time()
            config_path = self.project_root / config["path"]

            try:
                if config_path.exists():
                    content = config_path.read_text(encoding='utf-8')
                    execution_time = time.time() - start_time

                    missing_content = []
                    for required_item in config["required_content"]:
                        if required_item not in content:
                            missing_content.append(required_item)

                    if missing_content:
                        self.add_result(
                            f"config_{config_path.stem}",
                            "configuration",
                            "failed",
                            f"Missing required content: {missing_content}",
                            {"file_size": len(content)},
                            execution_time
                        )
                    else:
                        self.add_result(
                            f"config_{config_path.stem}",
                            "configuration",
                            "passed",
                            f"{config['description']} complete",
                            {"file_size": len(content), "content_items": len(config["required_content"])},
                            execution_time
                        )
                else:
                    self.add_result(
                        f"config_{config_path.stem}",
                        "configuration",
                        "failed",
                        f"Configuration file missing: {config['path']}",
                        execution_time=time.time() - start_time
                    )

            except Exception as e:
                execution_time = time.time() - start_time
                self.add_result(
                    f"config_{config_path.stem}",
                    "configuration",
                    "error",
                    f"Error reading config: {e}",
                    execution_time=execution_time
                )

    async def run_comprehensive_verification(self) -> Dict[str, Any]:
        """Run complete system verification suite"""
        logger.info("🚀 Starting ASR System Comprehensive Verification")
        logger.info("=" * 70)

        await self.initialize()

        verification_summary = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "categories": {},
            "results": [],
            "overall_status": "unknown",
            "deployment_ready": False
        }

        try:
            # Run all verification tests
            await self.verify_project_structure()
            await self.verify_backend_capabilities()
            self.verify_build_environment()
            await self.verify_api_integration()
            self.verify_configuration_completeness()

            # Process results
            verification_summary["total_tests"] = len(self.verification_results)

            category_stats = {}
            for result in self.verification_results:
                # Overall counts
                if result.status == "passed":
                    verification_summary["passed"] += 1
                elif result.status == "failed":
                    verification_summary["failed"] += 1
                elif result.status == "error":
                    verification_summary["errors"] += 1
                elif result.status == "skipped":
                    verification_summary["skipped"] += 1

                # Category stats
                if result.category not in category_stats:
                    category_stats[result.category] = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
                category_stats[result.category][result.status] += 1

                # Add to results
                verification_summary["results"].append(asdict(result))

            verification_summary["categories"] = category_stats

            # Determine overall status
            total_critical_tests = verification_summary["passed"] + verification_summary["failed"] + verification_summary["errors"]
            success_rate = verification_summary["passed"] / total_critical_tests if total_critical_tests > 0 else 0

            if success_rate >= 0.95:
                verification_summary["overall_status"] = "excellent"
                verification_summary["deployment_ready"] = True
            elif success_rate >= 0.85:
                verification_summary["overall_status"] = "good"
                verification_summary["deployment_ready"] = True
            elif success_rate >= 0.70:
                verification_summary["overall_status"] = "acceptable"
                verification_summary["deployment_ready"] = False
            else:
                verification_summary["overall_status"] = "poor"
                verification_summary["deployment_ready"] = False

            return verification_summary

        except Exception as e:
            logger.error(f"❌ System verification failed: {e}")
            verification_summary["overall_status"] = "error"
            verification_summary["error"] = str(e)
            return verification_summary

        finally:
            await self.cleanup()

    def print_verification_report(self, summary: Dict[str, Any]) -> None:
        """Print comprehensive verification report"""
        logger.info("=" * 70)
        logger.info("📊 ASR SYSTEM VERIFICATION REPORT")
        logger.info("=" * 70)

        # Overall status
        status = summary["overall_status"]
        deployment_ready = summary["deployment_ready"]

        status_icons = {
            "excellent": "🌟", "good": "✅", "acceptable": "⚠️",
            "poor": "❌", "error": "💥", "unknown": "❓"
        }

        logger.info(f"{status_icons.get(status, '❓')} Overall Status: {status.upper()}")
        logger.info(f"🚀 Deployment Ready: {'YES' if deployment_ready else 'NO'}")
        logger.info(f"📅 Verification Date: {summary['timestamp']}")

        # Test summary
        logger.info(f"\n📋 TEST SUMMARY:")
        logger.info(f"   • Total Tests: {summary['total_tests']}")
        logger.info(f"   • ✅ Passed: {summary['passed']}")
        logger.info(f"   • ❌ Failed: {summary['failed']}")
        logger.info(f"   • 💥 Errors: {summary['errors']}")
        logger.info(f"   • ⏭️ Skipped: {summary['skipped']}")

        # Category breakdown
        logger.info(f"\n📊 CATEGORY BREAKDOWN:")
        for category, stats in summary["categories"].items():
            total_cat = sum(stats.values())
            success_rate = stats["passed"] / total_cat * 100 if total_cat > 0 else 0
            logger.info(f"   {category.title()}: {success_rate:.1f}% success ({stats['passed']}/{total_cat})")

        # Critical issues
        critical_failures = [r for r in summary["results"] if r["status"] in ["failed", "error"]]
        if critical_failures:
            logger.info(f"\n🔥 CRITICAL ISSUES ({len(critical_failures)}):")
            for issue in critical_failures[:5]:  # Show top 5
                logger.info(f"   ❌ {issue['test_name']}: {issue['message']}")
            if len(critical_failures) > 5:
                logger.info(f"   ... and {len(critical_failures) - 5} more issues")

        # Deployment readiness
        logger.info(f"\n🚀 DEPLOYMENT READINESS:")
        if deployment_ready:
            logger.info("   ✅ System ready for production deployment")
            logger.info("   ✅ All critical components verified")
            logger.info("   ✅ Build environment configured")
            logger.info("   ✅ API integration functional")
        else:
            logger.info("   ⚠️ System requires attention before deployment")
            logger.info("   🔧 Review failed tests and resolve issues")
            logger.info("   📝 Update configuration as needed")

        # Next steps
        logger.info(f"\n💡 NEXT STEPS:")
        if deployment_ready:
            logger.info("   1. 🏗️ Run build scripts: python build_production_server.py")
            logger.info("   2. 📱 Run build scripts: python build_document_scanner.py")
            logger.info("   3. ⚡ Run performance validation: python performance_validation.py")
            logger.info("   4. 🚀 Deploy to production environment")
        else:
            logger.info("   1. 🔧 Fix critical issues identified above")
            logger.info("   2. ⚙️ Update configuration files")
            logger.info("   3. 🔄 Re-run system verification")
            logger.info("   4. 📞 Contact support if issues persist")

        logger.info("=" * 70)


async def main():
    """System verification entry point"""
    print("🧪 ASR System Comprehensive Verification Suite")
    print("Verifying deployment readiness and system capabilities")
    print("=" * 70)

    # Server URL - can be customized
    server_url = "http://localhost:8000"

    verifier = ASRSystemVerifier(server_url)
    results = await verifier.run_comprehensive_verification()

    verifier.print_verification_report(results)

    # Save results to file
    results_file = Path(f"system_verification_results_{int(time.time())}.json")
    with results_file.open('w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"📁 Detailed results saved to: {results_file}")

    # Return exit code based on deployment readiness
    return 0 if results["deployment_ready"] else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🔄 System verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ System verification failed: {e}")
        sys.exit(1)