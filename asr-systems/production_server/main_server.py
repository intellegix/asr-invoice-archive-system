"""
ASR Production Server - Main Application Launcher
Enterprise document processing server with Windows EXE + AWS deployment options
Preserves all existing sophisticated capabilities: 79 GL accounts, 5-method payment detection, 4 billing destinations
"""

import asyncio
import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configure structured logging before importing other modules
from config.logging_config import configure_logging

configure_logging(
    log_level=os.environ.get("LOG_LEVEL", "INFO"),
    log_format=os.environ.get("LOG_FORMAT", "text"),
)

# Force UTF-8 on stdout for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass

logger = logging.getLogger(__name__)

# Add shared components and local modules to path for both source and EXE contexts
CURRENT_DIR = Path(__file__).parent
SHARED_DIR = CURRENT_DIR.parent / "shared"
sys.path.insert(0, str(SHARED_DIR))
sys.path.insert(0, str(CURRENT_DIR))

from shared.core.constants import VERSION

# Import shared components
from shared.core.exceptions import ConfigurationError, CriticalSystemError


def _import_module(relative_path: str, absolute_path: str):
    """Import a module using relative import first, falling back to absolute for EXE context."""
    import importlib

    try:
        return importlib.import_module(relative_path, package="production_server")
    except (ImportError, SystemError):
        return importlib.import_module(absolute_path)


# Global shutdown flag
shutdown_requested = False


class ASRProductionServerLauncher:
    """
    Main launcher for ASR Production Server
    Coordinates startup of all sophisticated document processing components
    """

    def __init__(self):
        self.main_api_task = None
        self.health_monitor_task = None
        self.background_tasks = []
        self.running = False

        # Setup signal handlers
        self._setup_signal_handlers()

        # Initialize settings
        self._initialize_settings()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""

        def signal_handler(signum, frame):
            global shutdown_requested
            logger.info(f"Received signal {signum}, initiating shutdown...")
            shutdown_requested = True
            self.shutdown()

        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, signal_handler)

    def _initialize_settings(self):
        """Initialize application settings"""
        try:
            try:
                from .config.production_settings import ProductionSettings
            except (ImportError, SystemError):
                from config.production_settings import (  # type: ignore[no-redef]
                    ProductionSettings,
                )
            self.settings = ProductionSettings()

            # Log current configuration
            logger.info("=" * 60)
            logger.info("🚀 ASR Production Server Starting")
            logger.info("=" * 60)
            logger.info(f"Version: {VERSION}")
            logger.info(f"System Type: Production Server")
            logger.info(f"Debug Mode: {self.settings.DEBUG}")
            logger.info(f"API Host: {self.settings.get_api_host}")
            logger.info(f"API Port: {self.settings.API_PORT}")
            logger.info(f"Storage Backend: {self.settings.STORAGE_BACKEND}")
            logger.info(f"GL Accounts: 79 QuickBooks accounts enabled")
            logger.info(f"Payment Detection: 5-method consensus system")
            logger.info(f"Billing Destinations: 4 routing destinations")

            if self.settings.SCANNER_API_ENABLED:
                logger.info(f"Scanner API: Enabled on /api/v1/scanner/*")
                logger.info(f"Max Scanner Clients: {self.settings.MAX_SCANNER_CLIENTS}")

            # Ensure required directories exist
            self._ensure_directories()

        except Exception as e:
            logger.error(f"Failed to initialize settings: {e}")
            raise CriticalSystemError(
                f"Settings initialization failed: {e}", component="settings"
            )

    def _ensure_directories(self):
        """Ensure required directories exist"""
        try:
            # Ensure data directory exists
            data_dir = self.settings.get_data_dir
            data_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Data directory: {data_dir}")

            # Ensure document processing directories
            processing_dirs = [
                data_dir / "uploads" / "temp",
                data_dir / "processed" / "open_payable",
                data_dir / "processed" / "closed_payable",
                data_dir / "processed" / "open_receivable",
                data_dir / "processed" / "closed_receivable",
                data_dir / "manual_review",
                data_dir / "backups",
            ]

            for dir_path in processing_dirs:
                dir_path.mkdir(parents=True, exist_ok=True)

            logger.info("✅ Document processing directories ensured")

            # Ensure tenant isolation directories if multi-tenant enabled
            if self.settings.MULTI_TENANT_ENABLED:
                tenant_base = data_dir / "tenants"
                tenant_base.mkdir(parents=True, exist_ok=True)
                logger.info("✅ Multi-tenant directory structure ensured")

        except Exception as e:
            logger.error(f"Failed to ensure directories: {e}")
            raise CriticalSystemError(
                f"Directory initialization failed: {e}", component="directories"
            )

    async def start_main_api_server(self):
        """Start the main FastAPI application server with sophisticated capabilities"""
        try:
            logger.info("🚀 Starting Production Server API...")
            logger.info("Loading sophisticated document processing capabilities...")

            # Import uvicorn and main app
            import uvicorn

            try:
                from .api.main import app
            except (ImportError, SystemError):
                from api.main import app

            # Configure uvicorn for production
            config = uvicorn.Config(
                app,
                host=self.settings.get_api_host,
                port=self.settings.API_PORT,
                log_level="info" if self.settings.DEBUG else "warning",
                access_log=self.settings.DEBUG,
                workers=1 if self.settings.DEBUG else self.settings.API_WORKERS,
                timeout_keep_alive=self.settings.API_TIMEOUT,
                timeout_graceful_shutdown=30,
            )

            server = uvicorn.Server(config)

            logger.info("✅ API Server configured with:")
            logger.info(f"   • 79 QuickBooks GL Accounts")
            logger.info(f"   • 5-Method Payment Consensus Detection")
            logger.info(f"   • 4 Billing Destination Routing")
            logger.info(f"   • Claude AI Integration")
            logger.info(f"   • Scanner Client API")
            logger.info(f"   • Multi-Tenant Architecture")

            # Run server
            await server.serve()

        except Exception as e:
            logger.error(f"Production API server failed: {e}")
            raise CriticalSystemError(
                f"API server startup failed: {e}", component="api_server"
            )

    async def health_monitor(self):
        """Monitor system health and sophisticated components"""
        while self.running and not shutdown_requested:
            try:
                await asyncio.sleep(60)  # Check every minute

                # Log system status
                logger.debug("🔍 Production Server health check")

                # Check if main API is responding
                try:
                    import httpx

                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get(
                            f"http://localhost:{self.settings.API_PORT}/health"
                        )
                        if response.status_code == 200:
                            health_data = response.json()
                            logger.debug("✅ Production API is healthy")

                            # Log component status
                            if "checks" in health_data:
                                checks = health_data["checks"]
                                if checks.get("database") == "connected":
                                    logger.debug("✅ Database: Connected")
                                if checks.get("claude_api") == "configured":
                                    logger.debug("✅ Claude AI: Configured")
                                if checks.get("storage") == "configured":
                                    logger.debug("✅ Storage: Configured")
                        else:
                            logger.warning(
                                f"⚠️ API health check failed: {response.status_code}"
                            )
                except Exception as e:
                    logger.warning(f"⚠️ API health check error: {e}")

                # Monitor sophisticated components
                try:
                    # Check GL Account system
                    try:
                        from .services.gl_account_service import GLAccountService
                    except (ImportError, SystemError):
                        from services.gl_account_service import (  # type: ignore[no-redef]
                            GLAccountService,
                        )
                    gl_service = GLAccountService()
                    gl_count = len(gl_service.get_all_accounts())
                    if gl_count == 79:
                        logger.debug(f"✅ GL Accounts: {gl_count} loaded")
                    else:
                        logger.warning(
                            f"⚠️ GL Accounts: Only {gl_count} loaded (expected 79)"
                        )

                    # Check payment detection system
                    try:
                        from .services.payment_detection_service import (
                            PaymentDetectionService,
                        )
                    except (ImportError, SystemError):
                        from services.payment_detection_service import (  # type: ignore[no-redef]
                            PaymentDetectionService,
                        )
                    payment_service = PaymentDetectionService({}, [])  # type: ignore[call-arg]
                    methods = payment_service.get_enabled_methods()
                    logger.debug(
                        f"✅ Payment Detection: {len(methods)} methods enabled"
                    )

                    # Check billing router
                    try:
                        from .services.billing_router_service import (
                            BillingRouterService,
                        )
                    except (ImportError, SystemError):
                        from services.billing_router_service import (  # type: ignore[no-redef]
                            BillingRouterService,
                        )
                    router_service = BillingRouterService([], 0.8)  # type: ignore[call-arg]
                    destinations = router_service.get_available_destinations()
                    logger.debug(f"✅ Billing Router: {len(destinations)} destinations")

                except Exception as e:
                    logger.warning(f"⚠️ Sophisticated components check error: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")

    async def run_production_server(self):
        """Run the complete ASR Production Server"""
        self.running = True
        logger.info("🚀 Starting ASR Production Server")
        logger.info("Loading all sophisticated document processing capabilities...")

        try:
            # Create tasks for all components
            tasks = []

            # Main API server (required)
            main_task = asyncio.create_task(self.start_main_api_server())
            tasks.append(main_task)

            # Health monitoring
            health_task = asyncio.create_task(self.health_monitor())
            tasks.append(health_task)

            logger.info("=" * 60)
            logger.info("🎯 ASR Production Server ONLINE")
            logger.info("=" * 60)
            logger.info(f"🌐 API Endpoint: http://localhost:{self.settings.API_PORT}")
            logger.info(
                f"📋 Health Check: http://localhost:{self.settings.API_PORT}/health"
            )
            logger.info(
                f"📊 API Status: http://localhost:{self.settings.API_PORT}/api/status"
            )

            if self.settings.SCANNER_API_ENABLED:
                logger.info(
                    f"📱 Scanner API: http://localhost:{self.settings.API_PORT}/api/v1/scanner"
                )

            logger.info("=" * 60)
            logger.info("📁 Sophisticated Capabilities Active:")
            logger.info("   • 79 QuickBooks GL Accounts with keyword matching")
            logger.info(
                "   • 5-Method Payment Detection (Claude AI + Regex + Keywords + Amount + OCR)"
            )
            logger.info("   • 4 Billing Destinations (Open/Closed Payable/Receivable)")
            logger.info("   • Complete Audit Trail with confidence scoring")
            logger.info("   • Multi-tenant document isolation")
            logger.info("   • Scanner client API for distributed processing")
            logger.info("=" * 60)

            if self.settings.AWS_DEPLOYMENT_MODE:
                logger.info("☁️  AWS Deployment Mode: Optimized for ECS/Fargate")
            else:
                logger.info("🖥️  Standalone Mode: Windows EXE deployment")

            logger.info("Press Ctrl+C to shutdown")
            logger.info("=" * 60)

            # Wait for tasks or shutdown signal
            try:
                await asyncio.gather(*tasks)
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
            except asyncio.CancelledError:
                logger.info("Tasks cancelled")

        except Exception as e:
            logger.error(f"Production server startup failed: {e}")
            raise CriticalSystemError(
                f"System startup failed: {e}", component="startup"
            )
        finally:
            self.running = False

    def shutdown(self):
        """Shutdown the production server"""
        global shutdown_requested
        shutdown_requested = True
        self.running = False

        logger.info("🛑 Shutting down ASR Production Server...")

        # Cancel running tasks
        current_task = None
        try:
            current_task = asyncio.current_task()
        except RuntimeError:
            pass

        if current_task:
            for task in asyncio.all_tasks():
                if task != current_task and not task.done():
                    task.cancel()

        logger.info("✅ ASR Production Server shutdown complete")

    def run(self):
        """Main entry point"""
        try:
            # Check for command line arguments
            if len(sys.argv) > 1:
                command = sys.argv[1].lower()

                if command == "--version":
                    print(f"ASR Production Server v{VERSION}")
                    print(f"Sophisticated Document Processing Engine")
                    print(f"• 79 QuickBooks GL Accounts")
                    print(f"• 5-Method Payment Detection")
                    print(f"• 4 Billing Destination Routing")
                    print(f"• Multi-Tenant Architecture")
                    return 0

                elif command == "--config":
                    self.print_configuration()
                    return 0

                elif command == "--test":
                    return self.run_system_test()

                elif command == "--help":
                    self.print_help()
                    return 0

            # Run the production server
            return asyncio.run(self.run_production_server())

        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
            return 0
        except Exception as e:
            logger.error(f"Production server failed: {e}")
            return 1

    def print_configuration(self):
        """Print current configuration"""
        print("\n" + "=" * 60)
        print("ASR Production Server Configuration")
        print("=" * 60)
        print(f"System Type: Production Document Processing Server")
        print(f"Version: {VERSION}")
        print(f"Debug Mode: {self.settings.DEBUG}")
        print(f"Data Directory: {self.settings.get_data_dir}")
        print(f"API Host: {self.settings.get_api_host}")
        print(f"API Port: {self.settings.API_PORT}")
        print(f"Storage Backend: {self.settings.STORAGE_BACKEND}")

        print(f"\nSophisticated Processing Capabilities:")
        print(f"QuickBooks GL Accounts: 79 accounts with keyword matching")
        print(f"Payment Detection Methods: 5 consensus methods")
        print(f"Billing Destinations: 4 routing destinations with audit trails")
        print(f"Multi-Tenant Support: {self.settings.MULTI_TENANT_ENABLED}")

        print(f"\nScanner API Configuration:")
        print(f"Scanner API Enabled: {self.settings.SCANNER_API_ENABLED}")
        if self.settings.SCANNER_API_ENABLED:
            print(f"Max Scanner Clients: {self.settings.MAX_SCANNER_CLIENTS}")
            print(f"Scanner Authentication: API Key based")

        print(f"\nDatabase Configuration:")
        print(f"Database URL: {self.settings.DATABASE_URL}")
        print(f"Pool Size: {self.settings.DB_POOL_SIZE}")

        print(f"\nClaude AI Configuration:")
        api_key_configured = bool(self.settings.ANTHROPIC_API_KEY)
        print(f"API Key Configured: {api_key_configured}")
        if api_key_configured:
            key_preview = (
                self.settings.ANTHROPIC_API_KEY[:10] + "..."  # type: ignore[index]
                if len(self.settings.ANTHROPIC_API_KEY) > 10  # type: ignore[arg-type]
                else "***"
            )
            print(f"API Key Preview: {key_preview}")

    def run_system_test(self) -> int:
        """Run comprehensive system tests"""
        print("\n" + "=" * 60)
        print("Running ASR Production Server Tests")
        print("=" * 60)

        tests_passed = 0
        total_tests = 0

        # Test 1: Configuration validation
        total_tests += 1
        try:
            self.settings.validate_required_secrets()
            print("✅ Configuration validation passed")
            tests_passed += 1
        except Exception as e:
            print(f"❌ Configuration validation failed: {e}")

        # Test 2: Directory creation
        total_tests += 1
        try:
            self._ensure_directories()
            print("✅ Directory creation test passed")
            tests_passed += 1
        except Exception as e:
            print(f"❌ Directory creation test failed: {e}")

        # Test 3: Sophisticated components
        total_tests += 1
        try:
            from .services.gl_account_service import GLAccountService

            gl_service = GLAccountService()
            accounts = gl_service.get_all_accounts()
            if len(accounts) == 79:
                print(f"✅ GL Account system test passed (79 accounts loaded)")
                tests_passed += 1
            else:
                print(
                    f"❌ GL Account system test failed (only {len(accounts)} accounts)"
                )
        except Exception as e:
            print(f"❌ GL Account system test failed: {e}")

        # Test 4: Payment detection
        total_tests += 1
        try:
            from .services.payment_detection_service import PaymentDetectionService

            payment_service = PaymentDetectionService({}, [])  # type: ignore[call-arg]
            methods = payment_service.get_enabled_methods()
            if len(methods) >= 5:
                print(
                    f"✅ Payment detection system test passed ({len(methods)} methods)"
                )
                tests_passed += 1
            else:
                print(
                    f"❌ Payment detection system test failed (only {len(methods)} methods)"
                )
        except Exception as e:
            print(f"❌ Payment detection system test failed: {e}")

        # Test 5: Billing router
        total_tests += 1
        try:
            from .services.billing_router_service import BillingRouterService

            router = BillingRouterService()  # type: ignore[call-arg]
            destinations = router.get_available_destinations()
            if len(destinations) == 4:
                print(f"✅ Billing router test passed (4 destinations)")
                tests_passed += 1
            else:
                print(
                    f"❌ Billing router test failed (only {len(destinations)} destinations)"
                )
        except Exception as e:
            print(f"❌ Billing router test failed: {e}")

        print(f"\n" + "=" * 60)
        print(f"Test Results: {tests_passed}/{total_tests} passed")
        print("=" * 60)
        return 0 if tests_passed == total_tests else 1

    def print_help(self):
        """Print help information"""
        print(f"\n" + "=" * 60)
        print(f"ASR Production Server v{VERSION}")
        print("Enterprise Document Processing System")
        print("=" * 60)
        print("\nUsage: ASR_Production_Server.exe [command]")
        print("\nCommands:")
        print("  (no command)    Start the production server")
        print("  --version       Show version and capabilities")
        print("  --config        Show current configuration")
        print("  --test          Run comprehensive system tests")
        print("  --help          Show this help message")
        print("\nSophisticated Capabilities:")
        print("  • 79 QuickBooks GL Accounts with automated classification")
        print("  • 5-Method Payment Detection with consensus scoring")
        print("  • 4 Billing Destination routing with audit trails")
        print("  • Claude AI integration for document analysis")
        print("  • Multi-tenant document isolation")
        print("  • Scanner client API for distributed processing")
        print("\nEnvironment Variables:")
        print("  DEBUG               Enable debug mode (true/false)")
        print("  API_PORT            API server port (default: 8000)")
        print("  STORAGE_BACKEND     Storage backend (local/s3/render_disk)")
        print("  ANTHROPIC_API_KEY   Claude AI API key")
        print("  DATABASE_URL        Database connection string")
        print("  MULTI_TENANT_ENABLED Enable multi-tenant mode")
        print("\nDeployment Options:")
        print("  • Windows EXE: Standalone executable for local deployment")
        print("  • AWS ECS: Container deployment with auto-scaling")
        print("  • Docker: Containerized deployment for any platform")
        print("\nFor scanner integration:")
        print("  • Scanners connect via REST API")
        print("  • Automatic server discovery")
        print("  • Offline queue management")
        print("  • Batch document processing")
        print("\nSupport:")
        print("  Documentation: ./docs/PRODUCTION_SERVER_GUIDE.md")
        print("  API Reference: http://localhost:8000/docs")
        print("=" * 60)


def main():
    """Main entry point for ASR Production Server"""
    # Ensure we're running from the correct directory
    app_dir = Path(__file__).parent
    os.chdir(app_dir)

    # Add current directory to Python path
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))

    try:
        launcher = ASRProductionServerLauncher()
        return launcher.run()

    except KeyboardInterrupt:
        print("\nShutdown requested")
        return 0
    except Exception as e:
        print(f"\nFatal error: {e}")
        logger.exception("Fatal error in production server main")
        return 1


if __name__ == "__main__":
    sys.exit(main())
