#!/usr/bin/env python3
"""
ASR System Performance Validation
Comprehensive testing of production server and document scanner performance
"""

import asyncio
import aiohttp
import time
import json
import logging
import statistics
import tempfile
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import subprocess

# Add shared modules to path
sys.path.insert(0, str(Path(__file__).parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent / "production_server"))
sys.path.insert(0, str(Path(__file__).parent / "document-scanner"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance test metric"""
    test_name: str
    success_count: int
    failure_count: int
    total_time: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    throughput: float
    error_rate: float


@dataclass
class SystemHealthCheck:
    """System health check result"""
    component: str
    status: str
    response_time_ms: float
    details: Dict[str, Any]


class ASRPerformanceValidator:
    """Comprehensive ASR system performance validation"""

    def __init__(self, production_server_url: str = "http://localhost:8000"):
        self.production_server_url = production_server_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.test_results: List[PerformanceMetric] = []
        self.health_checks: List[SystemHealthCheck] = []

    async def initialize(self) -> None:
        """Initialize performance validator"""
        logger.info("🚀 Initializing ASR Performance Validator")

        timeout = aiohttp.ClientTimeout(total=60)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self.session:
            await self.session.close()

    async def test_production_server_health(self) -> SystemHealthCheck:
        """Test production server health and responsiveness"""
        logger.info("🏥 Testing production server health...")

        start_time = time.time()
        try:
            async with self.session.get(f"{self.production_server_url}/health") as response:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000

                if response.status == 200:
                    data = await response.json()
                    status = "healthy" if data.get("status") == "healthy" else "degraded"
                else:
                    status = "error"
                    data = {"error": f"HTTP {response.status}"}

                return SystemHealthCheck(
                    component="production_server",
                    status=status,
                    response_time_ms=response_time,
                    details=data
                )

        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            return SystemHealthCheck(
                component="production_server",
                status="error",
                response_time_ms=response_time,
                details={"error": str(e)}
            )

    async def test_server_discovery_performance(self, concurrent_requests: int = 50) -> PerformanceMetric:
        """Test server discovery endpoint performance"""
        logger.info(f"🔍 Testing server discovery performance ({concurrent_requests} concurrent requests)...")

        response_times = []
        success_count = 0
        failure_count = 0

        start_time = time.time()

        # Create concurrent discovery requests
        tasks = []
        for _ in range(concurrent_requests):
            tasks.append(self._discovery_request())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        total_time = end_time - start_time

        # Process results
        for result in results:
            if isinstance(result, Exception):
                failure_count += 1
            else:
                success_count += 1
                response_times.append(result["response_time"])

        # Calculate metrics
        avg_response_time = statistics.mean(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        throughput = concurrent_requests / total_time
        error_rate = failure_count / concurrent_requests

        return PerformanceMetric(
            test_name="server_discovery_performance",
            success_count=success_count,
            failure_count=failure_count,
            total_time=total_time,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            throughput=throughput,
            error_rate=error_rate
        )

    async def _discovery_request(self) -> Dict[str, Any]:
        """Single server discovery request"""
        start_time = time.time()
        try:
            async with self.session.get(f"{self.production_server_url}/api/scanner/discovery") as response:
                await response.read()
                end_time = time.time()
                return {
                    "success": response.status == 200,
                    "response_time": end_time - start_time,
                    "status_code": response.status
                }
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "response_time": end_time - start_time,
                "error": str(e)
            }

    async def test_document_upload_performance(self, concurrent_uploads: int = 10,
                                             documents_per_upload: int = 3) -> PerformanceMetric:
        """Test document upload performance under load"""
        total_uploads = concurrent_uploads * documents_per_upload
        logger.info(f"📤 Testing document upload performance ({concurrent_uploads} concurrent clients, "
                   f"{documents_per_upload} docs each = {total_uploads} total)...")

        # Create test documents
        test_documents = self._create_test_documents(documents_per_upload)

        response_times = []
        success_count = 0
        failure_count = 0

        start_time = time.time()

        # Create concurrent upload tasks
        tasks = []
        for client_id in range(concurrent_uploads):
            task = self._upload_client_session(client_id, test_documents)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        total_time = end_time - start_time

        # Process results
        for result in results:
            if isinstance(result, Exception):
                failure_count += documents_per_upload
            else:
                success_count += result["successful"]
                failure_count += result["failed"]
                response_times.extend(result["response_times"])

        # Calculate metrics
        avg_response_time = statistics.mean(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        throughput = success_count / total_time if total_time > 0 else 0
        error_rate = failure_count / total_uploads

        return PerformanceMetric(
            test_name="document_upload_performance",
            success_count=success_count,
            failure_count=failure_count,
            total_time=total_time,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            throughput=throughput,
            error_rate=error_rate
        )

    def _create_test_documents(self, count: int) -> List[Dict[str, Any]]:
        """Create test documents for upload testing"""
        documents = []

        test_contents = [
            b"INVOICE\nHome Depot\nLumber and construction materials\nAmount: $1,234.56\nDate: 2024-01-15",
            b"BILL\nSDGE Electric Company\nElectric utility service\nAmount: $456.78\nDate: 2024-01-16",
            b"RECEIPT\nShell Gas Station\nFuel purchase\nAmount: $89.12\nDate: 2024-01-17",
            b"INVOICE\nABC Legal Services\nAttorney consultation fees\nAmount: $2,500.00\nDate: 2024-01-18",
            b"BILL\nState Farm Insurance\nMonthly insurance premium\nAmount: $345.67\nDate: 2024-01-19"
        ]

        for i in range(count):
            content = test_contents[i % len(test_contents)]
            documents.append({
                "filename": f"perf_test_document_{i+1}.pdf",
                "content": content,
                "content_type": "application/pdf"
            })

        return documents

    async def _upload_client_session(self, client_id: int, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simulate a single client uploading multiple documents"""
        successful = 0
        failed = 0
        response_times = []

        for doc_index, document in enumerate(documents):
            try:
                start_time = time.time()

                # Create form data
                data = aiohttp.FormData()
                data.add_field('file',
                             document['content'],
                             filename=document['filename'],
                             content_type=document['content_type'])

                # Add metadata
                metadata = {
                    "scanner_id": f"perf_test_client_{client_id}",
                    "upload_timestamp": time.time()
                }
                data.add_field('metadata', json.dumps(metadata))

                async with self.session.post(f"{self.production_server_url}/api/scanner/upload",
                                           data=data) as response:
                    await response.read()
                    end_time = time.time()
                    response_time = end_time - start_time
                    response_times.append(response_time)

                    if response.status == 200:
                        successful += 1
                    else:
                        failed += 1

            except Exception as e:
                failed += 1
                logger.warning(f"Upload failed for client {client_id}, doc {doc_index}: {e}")

        return {
            "client_id": client_id,
            "successful": successful,
            "failed": failed,
            "response_times": response_times
        }

    async def test_gl_classification_performance(self, test_samples: int = 100) -> PerformanceMetric:
        """Test GL account classification performance"""
        logger.info(f"🏷️ Testing GL classification performance ({test_samples} samples)...")

        test_texts = [
            "Home Depot lumber plywood construction materials supplies",
            "SDGE electric bill utility payment monthly service",
            "Shell gasoline fuel trucks transportation costs",
            "Legal fees attorney consultation contract review",
            "State Farm insurance premium monthly coverage",
            "Office rent monthly payment building lease",
            "Staples office supplies paper pens printer ink",
            "AT&T phone bill monthly telecommunication service",
            "Repair costs equipment maintenance service call",
            "Training seminar employee development education"
        ]

        response_times = []
        success_count = 0
        failure_count = 0

        start_time = time.time()

        # Test classification requests
        for i in range(test_samples):
            test_text = test_texts[i % len(test_texts)]

            try:
                request_start = time.time()

                async with self.session.post(
                    f"{self.production_server_url}/api/classify",
                    json={"text": test_text}
                ) as response:
                    await response.read()
                    request_end = time.time()

                    response_times.append(request_end - request_start)

                    if response.status == 200:
                        success_count += 1
                    else:
                        failure_count += 1

            except Exception as e:
                failure_count += 1
                logger.warning(f"Classification failed for sample {i}: {e}")

        end_time = time.time()
        total_time = end_time - start_time

        # Calculate metrics
        avg_response_time = statistics.mean(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        throughput = success_count / total_time if total_time > 0 else 0
        error_rate = failure_count / test_samples

        return PerformanceMetric(
            test_name="gl_classification_performance",
            success_count=success_count,
            failure_count=failure_count,
            total_time=total_time,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            throughput=throughput,
            error_rate=error_rate
        )

    def test_executable_builds(self) -> Dict[str, bool]:
        """Test that both executables can be built successfully"""
        logger.info("🔨 Testing executable builds...")

        results = {}

        # Test production server build
        try:
            logger.info("Building production server executable...")
            result = subprocess.run([
                sys.executable, "build_production_server.py"
            ], capture_output=True, text=True, timeout=300)

            results["production_server"] = result.returncode == 0
            if result.returncode != 0:
                logger.error(f"Production server build failed: {result.stderr}")

        except Exception as e:
            logger.error(f"Production server build error: {e}")
            results["production_server"] = False

        # Test document scanner build
        try:
            logger.info("Building document scanner executable...")
            result = subprocess.run([
                sys.executable, "build_document_scanner.py"
            ], capture_output=True, text=True, timeout=300)

            results["document_scanner"] = result.returncode == 0
            if result.returncode != 0:
                logger.error(f"Document scanner build failed: {result.stderr}")

        except Exception as e:
            logger.error(f"Document scanner build error: {e}")
            results["document_scanner"] = False

        return results

    async def run_comprehensive_performance_validation(self) -> Dict[str, Any]:
        """Run complete performance validation suite"""
        logger.info("🚀 Starting ASR System Performance Validation")
        logger.info("=" * 70)

        await self.initialize()

        validation_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "server_url": self.production_server_url,
            "health_checks": [],
            "performance_tests": [],
            "build_tests": {},
            "overall_status": "unknown"
        }

        try:
            # Health checks
            logger.info("📋 Running health checks...")
            health_check = await self.test_production_server_health()
            self.health_checks.append(health_check)
            validation_results["health_checks"].append(asdict(health_check))

            if health_check.status != "healthy":
                logger.warning("⚠️ Production server is not healthy, skipping performance tests")
                validation_results["overall_status"] = "degraded"
                return validation_results

            # Performance tests
            logger.info("⚡ Running performance tests...")

            # Test 1: Server Discovery
            discovery_metric = await self.test_server_discovery_performance(50)
            self.test_results.append(discovery_metric)
            validation_results["performance_tests"].append(asdict(discovery_metric))

            # Test 2: Document Upload
            upload_metric = await self.test_document_upload_performance(10, 3)
            self.test_results.append(upload_metric)
            validation_results["performance_tests"].append(asdict(upload_metric))

            # Test 3: GL Classification
            classification_metric = await self.test_gl_classification_performance(50)
            self.test_results.append(classification_metric)
            validation_results["performance_tests"].append(asdict(classification_metric))

            # Build tests
            logger.info("🔨 Running build tests...")
            build_results = self.test_executable_builds()
            validation_results["build_tests"] = build_results

            # Calculate overall status
            all_tests_passed = all(
                metric.error_rate < 0.05 for metric in self.test_results
            ) and all(build_results.values())

            validation_results["overall_status"] = "passed" if all_tests_passed else "failed"

            return validation_results

        except Exception as e:
            logger.error(f"❌ Performance validation failed: {e}")
            validation_results["overall_status"] = "error"
            validation_results["error"] = str(e)
            return validation_results

        finally:
            await self.cleanup()

    def print_performance_report(self, results: Dict[str, Any]) -> None:
        """Print comprehensive performance validation report"""
        logger.info("=" * 70)
        logger.info("📊 ASR SYSTEM PERFORMANCE VALIDATION REPORT")
        logger.info("=" * 70)

        # Overall status
        status = results["overall_status"]
        status_icon = "✅" if status == "passed" else "❌" if status == "failed" else "⚠️"
        logger.info(f"{status_icon} Overall Status: {status.upper()}")
        logger.info(f"📅 Test Date: {results['timestamp']}")
        logger.info(f"🌐 Server URL: {results['server_url']}")

        # Health checks
        logger.info("\n🏥 HEALTH CHECKS:")
        for health in results["health_checks"]:
            status_icon = "✅" if health["status"] == "healthy" else "⚠️" if health["status"] == "degraded" else "❌"
            logger.info(f"   {status_icon} {health['component']}: {health['status']} "
                       f"({health['response_time_ms']:.1f}ms)")

        # Performance tests
        logger.info("\n⚡ PERFORMANCE TESTS:")
        for test in results["performance_tests"]:
            success_rate = (test["success_count"] / (test["success_count"] + test["failure_count"]) * 100) if (test["success_count"] + test["failure_count"]) > 0 else 0
            status_icon = "✅" if test["error_rate"] < 0.05 else "⚠️" if test["error_rate"] < 0.20 else "❌"

            logger.info(f"   {status_icon} {test['test_name'].replace('_', ' ').title()}:")
            logger.info(f"      • Success Rate: {success_rate:.1f}% ({test['success_count']}/{test['success_count'] + test['failure_count']})")
            logger.info(f"      • Average Response: {test['avg_response_time']*1000:.1f}ms")
            logger.info(f"      • Throughput: {test['throughput']:.1f} req/sec")
            logger.info(f"      • Error Rate: {test['error_rate']*100:.1f}%")

        # Build tests
        logger.info("\n🔨 BUILD TESTS:")
        for component, passed in results["build_tests"].items():
            status_icon = "✅" if passed else "❌"
            logger.info(f"   {status_icon} {component.replace('_', ' ').title()} Build: {'PASSED' if passed else 'FAILED'}")

        # Performance benchmarks
        logger.info("\n📈 PERFORMANCE BENCHMARKS:")
        logger.info("   Target Thresholds:")
        logger.info("   • Server Discovery: <500ms avg, <5% error rate")
        logger.info("   • Document Upload: <3000ms avg, <5% error rate")
        logger.info("   • GL Classification: <1000ms avg, <2% error rate")
        logger.info("   • Overall Success Rate: >95%")

        # Recommendations
        logger.info("\n💡 RECOMMENDATIONS:")
        if status == "passed":
            logger.info("   ✅ System performance meets all benchmarks")
            logger.info("   ✅ Ready for production deployment")
        else:
            logger.info("   ⚠️  Review failed tests and performance metrics")
            logger.info("   🔧 Consider system optimization before production")

        logger.info("=" * 70)


async def main():
    """Performance validation entry point"""
    print("🧪 ASR System Performance Validation Suite")
    print("Testing production server and document scanner performance")
    print("=" * 70)

    # Server URL - can be customized
    server_url = "http://localhost:8000"

    validator = ASRPerformanceValidator(server_url)
    results = await validator.run_comprehensive_performance_validation()

    validator.print_performance_report(results)

    # Save results to file
    results_file = Path(f"performance_validation_results_{int(time.time())}.json")
    with results_file.open('w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"📁 Detailed results saved to: {results_file}")

    # Return exit code based on results
    return 0 if results["overall_status"] == "passed" else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🔄 Performance validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Performance validation failed: {e}")
        sys.exit(1)