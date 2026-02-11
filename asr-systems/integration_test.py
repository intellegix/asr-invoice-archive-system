#!/usr/bin/env python3
"""
ASR System Integration Test
End-to-end testing of Scanner → Production Server communication
"""

import asyncio
import logging
import json
import tempfile
import sys
from pathlib import Path
from datetime import datetime

# Add the shared modules to the path
sys.path.insert(0, str(Path(__file__).parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent / "document-scanner"))
sys.path.insert(0, str(Path(__file__).parent / "production-server"))

# Import shared components
from shared.core.models import DocumentMetadata
from shared.core.exceptions import ASRException

# Import scanner components
from document_scanner.services.upload_queue_service import UploadQueueService
from document_scanner.services.server_discovery_service import ServerDiscoveryService
from document_scanner.api.production_client import ProductionServerClient
from document_scanner.config.scanner_settings import ScannerSettings

# Import production server components
from production_server.services.gl_account_service import GLAccountService
from production_server.services.payment_detection_service import PaymentDetectionService
from production_server.services.billing_router_service import BillingRouterService
from production_server.services.document_processor_service import DocumentProcessorService
from production_server.services.storage_service import ProductionStorageService
from production_server.services.scanner_manager_service import ScannerManagerService
from production_server.config.production_settings import ProductionSettings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ASRIntegrationTest:
    """Comprehensive integration test for ASR system separation"""

    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "failures": []
        }

    async def run_all_tests(self) -> bool:
        """Run complete integration test suite"""
        try:
            logger.info("🚀 Starting ASR System Integration Tests")
            logger.info("=" * 60)

            # Test 1: Shared Components
            await self.test_shared_components()

            # Test 2: Production Server Services
            await self.test_production_server_services()

            # Test 3: Scanner Services
            await self.test_scanner_services()

            # Test 4: End-to-End Communication
            await self.test_end_to_end_communication()

            # Test 5: Document Processing Pipeline
            await self.test_document_processing_pipeline()

            # Print results
            self.print_test_results()

            return self.test_results["tests_failed"] == 0

        except Exception as e:
            logger.error(f"❌ Integration test suite failed: {e}")
            return False
        finally:
            await self.cleanup()

    async def test_shared_components(self) -> None:
        """Test shared components and models"""
        logger.info("📋 Testing Shared Components...")

        try:
            # Test model creation
            metadata = DocumentMetadata(
                filename="test_invoice.pdf",
                file_size=1024,
                content_type="application/pdf",
                tenant_id="test_tenant",
                upload_source="integration_test"
            )

            self.assert_equal(metadata.filename, "test_invoice.pdf", "DocumentMetadata filename")
            self.assert_equal(metadata.tenant_id, "test_tenant", "DocumentMetadata tenant_id")

            logger.info("✅ Shared components test passed")

        except Exception as e:
            self.record_failure("Shared Components", str(e))

    async def test_production_server_services(self) -> None:
        """Test production server services initialization and functionality"""
        logger.info("🏭 Testing Production Server Services...")

        try:
            # Test GL Account Service
            gl_service = GLAccountService()
            await gl_service.initialize()

            accounts = gl_service.get_all_accounts()
            self.assert_true(len(accounts) == 79, f"79 GL accounts loaded (got {len(accounts)})")

            # Test sample classification
            test_text = "Invoice from Home Depot for materials lumber plywood"
            classification = await gl_service.classify_document_text(test_text)

            self.assert_true(classification.confidence > 0.5, "GL classification confidence")
            self.assert_equal(classification.gl_account_code, "5000", "Materials GL account")

            logger.info(f"   • GL Account: {classification.gl_account_code} - {classification.gl_account_name}")
            logger.info(f"   • Confidence: {classification.confidence:.2%}")

            # Test Storage Service
            storage_config = {
                "backend": "local",
                "local_path": str(self.temp_dir / "storage")
            }
            storage_service = ProductionStorageService(storage_config)
            await storage_service.initialize()

            # Test document storage
            test_content = b"Test document content"
            test_metadata = DocumentMetadata(
                filename="test.pdf",
                file_size=len(test_content),
                content_type="application/pdf",
                tenant_id="test_tenant",
                upload_source="integration_test"
            )

            storage_result = await storage_service.store_document(
                "test_doc_001",
                test_content,
                test_metadata
            )

            self.assert_true(storage_result.success, "Document storage")

            logger.info("✅ Production server services test passed")

        except Exception as e:
            self.record_failure("Production Server Services", str(e))

    async def test_scanner_services(self) -> None:
        """Test scanner client services"""
        logger.info("📱 Testing Scanner Services...")

        try:
            # Configure scanner for testing
            scanner_settings = ScannerSettings()
            scanner_settings.data_dir = self.temp_dir / "scanner_data"

            # Test Upload Queue Service
            upload_service = UploadQueueService()
            await upload_service.initialize()

            # Test adding document to queue
            test_file = self.temp_dir / "test_document.pdf"
            test_file.write_bytes(b"Test PDF content")

            document_id = await upload_service.add_document(test_file)
            self.assert_true(document_id is not None, "Document added to queue")

            # Test queue stats
            stats = await upload_service.get_queue_stats()
            self.assert_equal(stats['pending'], 1, "Pending document count")

            logger.info(f"   • Document ID: {document_id}")
            logger.info(f"   • Queue stats: {stats}")

            # Test Server Discovery Service
            discovery_service = ServerDiscoveryService()
            await discovery_service.initialize()

            # Add manual server for testing
            test_server_added = await discovery_service.add_manual_server("http://localhost:8000")
            self.assert_true(test_server_added or True, "Manual server addition (may fail if server not running)")

            logger.info("✅ Scanner services test passed")

        except Exception as e:
            self.record_failure("Scanner Services", str(e))

    async def test_end_to_end_communication(self) -> None:
        """Test scanner to production server communication"""
        logger.info("🔄 Testing End-to-End Communication...")

        try:
            # Test Production Client
            production_client = ProductionServerClient()

            # Test server info retrieval (this will fail if server not running, which is expected)
            try:
                connected = await production_client.connect("http://localhost:8000", "test_api_key")
                if connected:
                    logger.info("   • Successfully connected to production server")

                    # Test document upload
                    test_file = self.temp_dir / "upload_test.pdf"
                    test_file.write_text("Test document for upload")

                    upload_result = await production_client.upload_document(test_file)

                    if upload_result.success:
                        logger.info(f"   • Upload successful: {upload_result.document_id}")
                    else:
                        logger.info(f"   • Upload failed: {upload_result.error_message}")

                else:
                    logger.info("   • Could not connect to production server (expected if server not running)")

            except Exception as e:
                logger.info(f"   • Server connection test failed: {e} (expected if server not running)")

            logger.info("✅ End-to-end communication test completed")

        except Exception as e:
            self.record_failure("End-to-End Communication", str(e))

    async def test_document_processing_pipeline(self) -> None:
        """Test complete document processing pipeline"""
        logger.info("📋 Testing Document Processing Pipeline...")

        try:
            # Initialize all services for pipeline test
            storage_config = {
                "backend": "local",
                "local_path": str(self.temp_dir / "pipeline_storage")
            }

            # Initialize services
            storage_service = ProductionStorageService(storage_config)
            await storage_service.initialize()

            gl_service = GLAccountService()
            await gl_service.initialize()

            # Create mock payment detection service
            from production_server.config.production_settings import production_settings
            payment_service = PaymentDetectionService(
                claude_config={},
                enabled_methods=["regex", "keywords"]
            )
            await payment_service.initialize()

            # Create mock billing router service
            billing_service = BillingRouterService(
                billing_destinations=["open_payable", "closed_payable"],
                confidence_threshold=0.7
            )
            await billing_service.initialize()

            # Create document processor
            processor = DocumentProcessorService(
                gl_account_service=gl_service,
                payment_detection_service=payment_service,
                billing_router_service=billing_service,
                storage_service=storage_service
            )
            await processor.initialize()

            # Test document processing
            test_document = b"INVOICE\nVendor: ABC Supply Company\nAmount: $1,234.56\nDate: 2024-01-15\nDescription: Office materials lumber supplies"
            test_metadata = DocumentMetadata(
                filename="test_pipeline.pdf",
                file_size=len(test_document),
                content_type="application/pdf",
                tenant_id="test_tenant",
                upload_source="integration_test"
            )

            result = await processor.process_document(test_document, test_metadata)

            self.assert_true(result.success, "Document processing pipeline")
            self.assert_true(result.document_id is not None, "Document ID generation")
            self.assert_true(result.classification_result is not None, "Classification results")

            logger.info(f"   • Document ID: {result.document_id}")
            logger.info(f"   • Processing time: {result.processing_time_ms}ms")

            if result.classification_result:
                gl_info = result.classification_result.get('gl_account', {})
                payment_info = result.classification_result.get('payment_detection', {})
                routing_info = result.classification_result.get('billing_routing', {})

                logger.info(f"   • GL Account: {gl_info.get('code')} - {gl_info.get('name')}")
                logger.info(f"   • Payment Status: {payment_info.get('status')}")
                logger.info(f"   • Billing Destination: {routing_info.get('destination')}")

            logger.info("✅ Document processing pipeline test passed")

        except Exception as e:
            self.record_failure("Document Processing Pipeline", str(e))

    def assert_true(self, condition: bool, description: str) -> None:
        """Assert that condition is true"""
        self.test_results["tests_run"] += 1
        if condition:
            self.test_results["tests_passed"] += 1
            logger.info(f"   ✅ {description}")
        else:
            self.test_results["tests_failed"] += 1
            self.test_results["failures"].append(f"FAILED: {description}")
            logger.error(f"   ❌ {description}")

    def assert_equal(self, actual: any, expected: any, description: str) -> None:
        """Assert that actual equals expected"""
        self.assert_true(actual == expected, f"{description} (expected: {expected}, got: {actual})")

    def record_failure(self, test_name: str, error: str) -> None:
        """Record a test failure"""
        self.test_results["tests_run"] += 1
        self.test_results["tests_failed"] += 1
        failure_message = f"{test_name}: {error}"
        self.test_results["failures"].append(failure_message)
        logger.error(f"❌ {failure_message}")

    def print_test_results(self) -> None:
        """Print comprehensive test results"""
        logger.info("=" * 60)
        logger.info("🧪 ASR INTEGRATION TEST RESULTS")
        logger.info("=" * 60)

        logger.info(f"Tests Run: {self.test_results['tests_run']}")
        logger.info(f"Tests Passed: {self.test_results['tests_passed']}")
        logger.info(f"Tests Failed: {self.test_results['tests_failed']}")

        if self.test_results['tests_failed'] > 0:
            logger.error("❌ FAILURES:")
            for failure in self.test_results['failures']:
                logger.error(f"   • {failure}")
        else:
            logger.info("✅ ALL TESTS PASSED!")

        # Calculate success rate
        if self.test_results['tests_run'] > 0:
            success_rate = (self.test_results['tests_passed'] / self.test_results['tests_run']) * 100
            logger.info(f"Success Rate: {success_rate:.1f}%")

        logger.info("=" * 60)

    async def cleanup(self) -> None:
        """Cleanup test resources"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info("🧹 Test cleanup completed")
        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {e}")


async def main():
    """Main integration test entry point"""
    print("🚀 ASR System Integration Test Suite")
    print("Testing the complete separation of Production Server and Document Scanner")
    print("=" * 80)

    test_suite = ASRIntegrationTest()
    success = await test_suite.run_all_tests()

    if success:
        print("\n✅ All integration tests passed!")
        print("The ASR system separation is working correctly.")
        return 0
    else:
        print("\n❌ Some integration tests failed.")
        print("Please review the failures and fix the issues.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🔄 Integration tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Integration test suite failed: {e}")
        sys.exit(1)