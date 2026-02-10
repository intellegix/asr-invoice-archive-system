#!/usr/bin/env python3
"""
ASR System Load Testing
Tests system performance under high volume and concurrent load
"""

import asyncio
import json
import logging
import statistics
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List

import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ASRLoadTester:
    """Load testing framework for ASR system"""

    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.session: aiohttp.ClientSession = None
        self.results = {
            "requests_sent": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "response_times": [],
            "errors": [],
            "throughput": 0,
        }

    async def initialize(self):
        """Initialize load testing session"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def cleanup(self):
        """Cleanup load testing resources"""
        if self.session:
            await self.session.close()

    async def test_server_discovery_load(
        self, concurrent_requests: int = 50
    ) -> Dict[str, Any]:
        """Test server discovery endpoint under load"""
        logger.info(
            f"🔍 Testing server discovery with {concurrent_requests} concurrent requests..."
        )

        tasks = []
        for i in range(concurrent_requests):
            task = self._test_discovery_request()
            tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        successful = len([r for r in results if not isinstance(r, Exception)])
        failed = len(results) - successful
        total_time = end_time - start_time

        logger.info(f"   • Successful: {successful}/{concurrent_requests}")
        logger.info(f"   • Failed: {failed}/{concurrent_requests}")
        logger.info(f"   • Total time: {total_time:.2f}s")
        logger.info(f"   • Requests/second: {concurrent_requests/total_time:.2f}")

        return {
            "test_name": "server_discovery_load",
            "concurrent_requests": concurrent_requests,
            "successful": successful,
            "failed": failed,
            "total_time": total_time,
            "requests_per_second": concurrent_requests / total_time,
        }

    async def _test_discovery_request(self) -> Dict[str, Any]:
        """Single server discovery request"""
        start_time = time.time()

        try:
            async with self.session.get(
                f"{self.server_url}/api/scanner/discovery"
            ) as response:
                response_data = await response.json()
                end_time = time.time()

                return {
                    "success": response.status == 200,
                    "status_code": response.status,
                    "response_time": end_time - start_time,
                    "data": response_data if response.status == 200 else None,
                }
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "error": str(e),
                "response_time": end_time - start_time,
            }

    async def test_document_upload_load(
        self, concurrent_uploads: int = 10, documents_per_client: int = 5
    ) -> Dict[str, Any]:
        """Test document upload under concurrent load"""
        total_uploads = concurrent_uploads * documents_per_client
        logger.info(
            f"📤 Testing document upload: {concurrent_uploads} concurrent clients, {documents_per_client} docs each ({total_uploads} total)..."
        )

        # Create test documents
        test_documents = self._create_test_documents(documents_per_client)

        # Create concurrent upload tasks
        tasks = []
        for client_id in range(concurrent_uploads):
            task = self._test_client_upload_session(client_id, test_documents.copy())
            tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Analyze results
        successful_uploads = 0
        failed_uploads = 0
        response_times = []

        for result in results:
            if isinstance(result, Exception):
                failed_uploads += documents_per_client
            else:
                successful_uploads += result.get("successful", 0)
                failed_uploads += result.get("failed", 0)
                response_times.extend(result.get("response_times", []))

        total_time = end_time - start_time
        throughput = successful_uploads / total_time if total_time > 0 else 0

        logger.info(f"   • Successful uploads: {successful_uploads}/{total_uploads}")
        logger.info(f"   • Failed uploads: {failed_uploads}/{total_uploads}")
        logger.info(f"   • Total time: {total_time:.2f}s")
        logger.info(f"   • Upload throughput: {throughput:.2f} docs/second")

        if response_times:
            avg_response_time = statistics.mean(response_times)
            logger.info(f"   • Average response time: {avg_response_time:.3f}s")

        return {
            "test_name": "document_upload_load",
            "concurrent_clients": concurrent_uploads,
            "documents_per_client": documents_per_client,
            "total_uploads": total_uploads,
            "successful": successful_uploads,
            "failed": failed_uploads,
            "total_time": total_time,
            "throughput": throughput,
            "average_response_time": (
                statistics.mean(response_times) if response_times else 0
            ),
        }

    def _create_test_documents(self, count: int) -> List[Dict[str, Any]]:
        """Create test documents for upload testing"""
        documents = []

        test_contents = [
            b"INVOICE\nHome Depot\nConstruction materials\nAmount: $1,234.56",
            b"BILL\nSDGE Electric\nUtility service\nAmount: $456.78",
            b"RECEIPT\nShell Gas Station\nFuel purchase\nAmount: $89.12",
            b"INVOICE\nABC Legal Services\nAttorney consultation\nAmount: $2,500.00",
            b"BILL\nState Farm Insurance\nMonthly premium\nAmount: $345.67",
        ]

        for i in range(count):
            content = test_contents[i % len(test_contents)]
            documents.append(
                {
                    "filename": f"test_document_{i+1}.pdf",
                    "content": content,
                    "content_type": "application/pdf",
                }
            )

        return documents

    async def _test_client_upload_session(
        self, client_id: int, documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Simulate a single client uploading multiple documents"""
        successful = 0
        failed = 0
        response_times = []

        for doc_index, document in enumerate(documents):
            try:
                start_time = time.time()

                # Create form data
                data = aiohttp.FormData()
                data.add_field(
                    "file",
                    document["content"],
                    filename=document["filename"],
                    content_type=document["content_type"],
                )

                # Add scanner info
                scanner_info = {
                    "scanner_id": f"load_test_client_{client_id}",
                    "upload_timestamp": time.time(),
                }
                data.add_field("scanner_info", json.dumps(scanner_info))

                async with self.session.post(
                    f"{self.server_url}/api/scanner/upload", data=data
                ) as response:
                    await response.read()  # Consume response
                    end_time = time.time()
                    response_time = end_time - start_time
                    response_times.append(response_time)

                    if response.status == 200:
                        successful += 1
                    else:
                        failed += 1
                        logger.warning(
                            f"Upload failed for client {client_id}, doc {doc_index}: {response.status}"
                        )

            except Exception as e:
                failed += 1
                logger.error(
                    f"Upload exception for client {client_id}, doc {doc_index}: {e}"
                )

        return {
            "client_id": client_id,
            "successful": successful,
            "failed": failed,
            "response_times": response_times,
        }

    async def test_scanner_registration_load(
        self, concurrent_registrations: int = 20
    ) -> Dict[str, Any]:
        """Test scanner registration under load"""
        logger.info(
            f"📱 Testing scanner registration with {concurrent_registrations} concurrent registrations..."
        )

        tasks = []
        for scanner_id in range(concurrent_registrations):
            task = self._test_scanner_registration(scanner_id)
            tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        successful = len(
            [r for r in results if not isinstance(r, Exception) and r.get("success")]
        )
        failed = len(results) - successful
        total_time = end_time - start_time

        logger.info(
            f"   • Successful registrations: {successful}/{concurrent_registrations}"
        )
        logger.info(f"   • Failed registrations: {failed}/{concurrent_registrations}")
        logger.info(f"   • Total time: {total_time:.2f}s")

        return {
            "test_name": "scanner_registration_load",
            "concurrent_registrations": concurrent_registrations,
            "successful": successful,
            "failed": failed,
            "total_time": total_time,
        }

    async def _test_scanner_registration(self, scanner_id: int) -> Dict[str, Any]:
        """Single scanner registration request"""
        registration_data = {
            "scanner_name": f"Load Test Scanner {scanner_id}",
            "tenant_id": "load_test_tenant",
            "api_key": "load_test_key",
            "capabilities": {
                "formats": ["pdf", "jpg", "png"],
                "batch_upload": True,
                "offline_queue": True,
            },
        }

        try:
            async with self.session.post(
                f"{self.server_url}/api/v1/scanner/register", json=registration_data
            ) as response:
                result = await response.json() if response.status == 200 else {}

                return {
                    "success": response.status == 200,
                    "scanner_id": scanner_id,
                    "status_code": response.status,
                    "result": result,
                }
        except Exception as e:
            return {"success": False, "scanner_id": scanner_id, "error": str(e)}

    async def test_batch_upload_performance(
        self, batch_size: int = 10, concurrent_batches: int = 5
    ) -> Dict[str, Any]:
        """Test batch upload performance"""
        total_documents = batch_size * concurrent_batches
        logger.info(
            f"📦 Testing batch upload: {concurrent_batches} concurrent batches of {batch_size} docs each ({total_documents} total)..."
        )

        tasks = []
        for batch_id in range(concurrent_batches):
            task = self._test_batch_upload(batch_id, batch_size)
            tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        successful_batches = len(
            [r for r in results if not isinstance(r, Exception) and r.get("success")]
        )
        total_time = end_time - start_time
        throughput = total_documents / total_time if total_time > 0 else 0

        logger.info(
            f"   • Successful batches: {successful_batches}/{concurrent_batches}"
        )
        logger.info(f"   • Total time: {total_time:.2f}s")
        logger.info(f"   • Batch throughput: {throughput:.2f} docs/second")

        return {
            "test_name": "batch_upload_performance",
            "batch_size": batch_size,
            "concurrent_batches": concurrent_batches,
            "total_documents": total_documents,
            "successful_batches": successful_batches,
            "total_time": total_time,
            "throughput": throughput,
        }

    async def _test_batch_upload(
        self, batch_id: int, batch_size: int
    ) -> Dict[str, Any]:
        """Single batch upload test"""
        try:
            data = aiohttp.FormData()

            # Add multiple files to form data
            for doc_id in range(batch_size):
                content = f"Batch {batch_id} Document {doc_id} test content".encode()
                filename = f"batch_{batch_id}_doc_{doc_id}.pdf"

                data.add_field(
                    "files", content, filename=filename, content_type="application/pdf"
                )

            async with self.session.post(
                f"{self.server_url}/api/scanner/batch", data=data
            ) as response:
                result = await response.json() if response.status == 200 else {}

                return {
                    "success": response.status == 200,
                    "batch_id": batch_id,
                    "status_code": response.status,
                    "result": result,
                }
        except Exception as e:
            return {"success": False, "batch_id": batch_id, "error": str(e)}

    async def run_comprehensive_load_test(self) -> Dict[str, Any]:
        """Run comprehensive load testing suite"""
        logger.info("🚀 Starting ASR System Load Testing Suite")
        logger.info("=" * 60)

        await self.initialize()

        test_results = {}

        try:
            # Test 1: Server Discovery Load
            test_results["server_discovery"] = await self.test_server_discovery_load(50)

            # Test 2: Scanner Registration Load
            test_results["scanner_registration"] = (
                await self.test_scanner_registration_load(20)
            )

            # Test 3: Document Upload Load
            test_results["document_upload"] = await self.test_document_upload_load(
                10, 5
            )

            # Test 4: Batch Upload Performance
            test_results["batch_upload"] = await self.test_batch_upload_performance(
                10, 5
            )

            # Calculate overall performance metrics
            test_results["summary"] = self._calculate_performance_summary(test_results)

            return test_results

        except Exception as e:
            logger.error(f"❌ Load testing failed: {e}")
            return {"error": str(e)}

        finally:
            await self.cleanup()

    def _calculate_performance_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall performance summary"""
        summary = {
            "total_tests": len([k for k in results.keys() if k != "summary"]),
            "tests_passed": 0,
            "tests_failed": 0,
            "peak_throughput": 0,
            "average_response_time": 0,
        }

        throughputs = []
        response_times = []

        for test_name, result in results.items():
            if (
                isinstance(result, dict)
                and "successful" in result
                and "failed" in result
            ):
                if result["successful"] > result["failed"]:
                    summary["tests_passed"] += 1
                else:
                    summary["tests_failed"] += 1

                if "throughput" in result:
                    throughputs.append(result["throughput"])

                if "average_response_time" in result:
                    response_times.append(result["average_response_time"])

        if throughputs:
            summary["peak_throughput"] = max(throughputs)

        if response_times:
            summary["average_response_time"] = statistics.mean(response_times)

        return summary

    def print_load_test_report(self, results: Dict[str, Any]) -> None:
        """Print comprehensive load test report"""
        logger.info("=" * 60)
        logger.info("📊 ASR LOAD TESTING REPORT")
        logger.info("=" * 60)

        for test_name, result in results.items():
            if test_name == "summary":
                continue

            logger.info(f"\n🧪 {test_name.replace('_', ' ').title()}:")

            if isinstance(result, dict):
                if "successful" in result and "failed" in result:
                    total = result["successful"] + result["failed"]
                    success_rate = (
                        (result["successful"] / total * 100) if total > 0 else 0
                    )
                    logger.info(
                        f"   • Success Rate: {success_rate:.1f}% ({result['successful']}/{total})"
                    )

                if "throughput" in result:
                    logger.info(
                        f"   • Throughput: {result['throughput']:.2f} requests/second"
                    )

                if "total_time" in result:
                    logger.info(f"   • Total Time: {result['total_time']:.2f} seconds")

                if "average_response_time" in result:
                    logger.info(
                        f"   • Avg Response Time: {result['average_response_time']:.3f} seconds"
                    )

        if "summary" in results:
            summary = results["summary"]
            logger.info(f"\n📈 PERFORMANCE SUMMARY:")
            logger.info(
                f"   • Tests Passed: {summary['tests_passed']}/{summary['total_tests']}"
            )
            logger.info(
                f"   • Peak Throughput: {summary['peak_throughput']:.2f} requests/second"
            )
            logger.info(
                f"   • Average Response Time: {summary['average_response_time']:.3f} seconds"
            )

        logger.info("=" * 60)


async def main():
    """Main load testing entry point"""
    print("🧪 ASR System Load Testing")
    print("Testing system performance under concurrent load")
    print("=" * 50)

    # You can customize the server URL here
    server_url = "http://localhost:8000"

    load_tester = ASRLoadTester(server_url)
    results = await load_tester.run_comprehensive_load_test()

    load_tester.print_load_test_report(results)

    # Return success if most tests passed
    if "summary" in results:
        success_rate = (
            results["summary"]["tests_passed"] / results["summary"]["total_tests"]
        )
        return 0 if success_rate >= 0.8 else 1
    else:
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n🔄 Load testing interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Load testing failed: {e}")
        exit(1)
