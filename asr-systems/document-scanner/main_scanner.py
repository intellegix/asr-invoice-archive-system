"""
ASR Document Scanner - Main Application Launcher
Desktop scanning client with offline capabilities and production server integration
"""

import asyncio
import logging
import signal
import sys
import threading
import tkinter as tk
from pathlib import Path
from typing import Optional
import argparse

# Import shared components
from shared.core.models import ScannerHealth
from shared.core.exceptions import ScannerError

# Import scanner components
from .config.scanner_settings import scanner_settings
from .services.upload_queue_service import UploadQueueService
from .services.server_discovery_service import ServerDiscoveryService
from .services.scanner_hardware_service import ScannerHardwareService
from .gui.main_window import ScannerMainWindow
from .api.production_client import ProductionServerClient

logger = logging.getLogger(__name__)


class ASRDocumentScannerLauncher:
    """
    Main launcher for ASR Document Scanner desktop application

    Coordinates all scanner components:
    - Desktop GUI interface
    - Upload queue management
    - Server discovery and connectivity
    - Scanner hardware integration
    - Production server communication
    """

    def __init__(self):
        self.services = {}
        self.running = False
        self.gui_root: Optional[tk.Tk] = None
        self.main_window: Optional[ScannerMainWindow] = None
        self.async_loop: Optional[asyncio.AbstractEventLoop] = None

    async def initialize_services(self) -> None:
        """Initialize all scanner services"""
        try:
            logger.info("🚀 Initializing ASR Document Scanner services...")

            # Initialize upload queue service
            self.services['upload_queue'] = UploadQueueService()
            await self.services['upload_queue'].initialize()

            # Initialize server discovery
            self.services['server_discovery'] = ServerDiscoveryService()
            await self.services['server_discovery'].initialize()

            # Initialize scanner hardware
            self.services['scanner_hardware'] = ScannerHardwareService()
            await self.services['scanner_hardware'].initialize()

            # Initialize production server client
            self.services['production_client'] = ProductionServerClient()

            # Attempt to discover and connect to production server
            await self._discover_and_connect_server()

            logger.info("✅ All scanner services initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize scanner services: {e}")
            raise ScannerError(f"Service initialization failed: {e}")

    async def _discover_and_connect_server(self) -> None:
        """Discover and connect to production server"""
        try:
            # Attempt to find production servers on network
            servers = await self.services['server_discovery'].discover_servers()

            if servers:
                # Connect to the first available server
                server = servers[0]
                await self.services['production_client'].connect(
                    server_url=server.url,
                    api_key=scanner_settings.api_key
                )
                logger.info(f"✅ Connected to production server: {server.url}")
            else:
                logger.warning("⚠️ No production servers discovered. Running in offline mode.")

        except Exception as e:
            logger.warning(f"⚠️ Server connection failed: {e}. Running in offline mode.")

    def initialize_gui(self) -> None:
        """Initialize the desktop GUI interface"""
        try:
            # Create main Tkinter window
            self.gui_root = tk.Tk()
            self.gui_root.title("ASR Document Scanner")
            self.gui_root.geometry("1000x700")

            # Set window icon and properties
            self.gui_root.resizable(True, True)
            self.gui_root.minsize(800, 600)

            # Initialize main window with services
            self.main_window = ScannerMainWindow(
                root=self.gui_root,
                services=self.services,
                async_loop=self.async_loop
            )

            # Handle window close
            self.gui_root.protocol("WM_DELETE_WINDOW", self._on_window_close)

            logger.info("✅ Desktop GUI initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize GUI: {e}")
            raise ScannerError(f"GUI initialization failed: {e}")

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"📡 Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _on_window_close(self) -> None:
        """Handle GUI window close event"""
        logger.info("🔄 Window close requested, initiating shutdown...")
        asyncio.create_task(self.shutdown())

    async def run_async_background(self) -> None:
        """Run background async tasks"""
        try:
            while self.running:
                # Process upload queue
                if 'upload_queue' in self.services:
                    await self.services['upload_queue'].process_queue()

                # Check server connectivity
                if 'production_client' in self.services:
                    await self.services['production_client'].heartbeat()

                # Update GUI with status if needed
                if self.main_window:
                    self.main_window.update_status()

                # Sleep briefly to prevent high CPU usage
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"❌ Background task error: {e}")

    def run_gui_main_loop(self) -> None:
        """Run the Tkinter main loop"""
        try:
            if self.gui_root:
                self.gui_root.mainloop()
        except Exception as e:
            logger.error(f"❌ GUI main loop error: {e}")

    async def start(self) -> None:
        """Start the document scanner application"""
        try:
            # Set up logging
            logging.basicConfig(
                level=getattr(logging, scanner_settings.log_level),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

            logger.info("🚀 Starting ASR Document Scanner...")
            logger.info(f"📁 Data directory: {scanner_settings.data_dir}")
            logger.info(f"🔧 Configuration: {scanner_settings.dict()}")

            # Initialize services
            await self.initialize_services()

            # Set up signal handlers
            self._setup_signal_handlers()

            # Initialize GUI
            self.initialize_gui()

            # Mark as running
            self.running = True

            # Start background async tasks
            background_task = asyncio.create_task(self.run_async_background())

            # Start GUI in separate thread
            gui_thread = threading.Thread(target=self.run_gui_main_loop, daemon=True)
            gui_thread.start()

            logger.info("✅ ASR Document Scanner started successfully")

            # Wait for shutdown
            await background_task

        except Exception as e:
            logger.error(f"❌ Failed to start scanner: {e}")
            raise

    async def shutdown(self) -> None:
        """Graceful shutdown of the scanner application"""
        try:
            logger.info("🔄 Shutting down ASR Document Scanner...")

            self.running = False

            # Cleanup services
            for service_name, service in self.services.items():
                try:
                    if hasattr(service, 'cleanup'):
                        await service.cleanup()
                    logger.info(f"✅ {service_name} service cleaned up")
                except Exception as e:
                    logger.error(f"❌ Error cleaning up {service_name}: {e}")

            # Close GUI
            if self.gui_root:
                self.gui_root.quit()
                self.gui_root.destroy()

            logger.info("✅ ASR Document Scanner shutdown complete")

        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")

    async def get_health(self) -> ScannerHealth:
        """Get overall scanner health status"""
        try:
            service_health = {}

            # Check each service health
            for service_name, service in self.services.items():
                if hasattr(service, 'get_health'):
                    service_health[service_name] = await service.get_health()
                else:
                    service_health[service_name] = {"status": "unknown"}

            # Determine overall status
            all_healthy = all(
                health.get("status") == "healthy"
                for health in service_health.values()
            )

            return ScannerHealth(
                status="healthy" if all_healthy else "degraded",
                services=service_health,
                gui_active=self.gui_root is not None and self.gui_root.winfo_exists(),
                server_connected=self.services.get('production_client', {}).get('connected', False)
            )

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return ScannerHealth(
                status="error",
                error=str(e),
                services={},
                gui_active=False,
                server_connected=False
            )


async def main():
    """Main entry point for ASR Document Scanner"""
    parser = argparse.ArgumentParser(description="ASR Document Scanner")
    parser.add_argument("--version", action="store_true", help="Show version")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument("--data-dir", type=str, help="Override data directory")
    parser.add_argument("--log-level", type=str, choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log level")
    parser.add_argument("--offline", action="store_true", help="Start in offline mode")

    args = parser.parse_args()

    if args.version:
        print(f"ASR Document Scanner v2.0.0")
        return

    # Update settings from command line args
    if args.data_dir:
        scanner_settings.data_dir = Path(args.data_dir)
    if args.log_level:
        scanner_settings.log_level = args.log_level
    if args.offline:
        scanner_settings.offline_mode = True

    # Create and start scanner
    scanner = ASRDocumentScannerLauncher()

    try:
        # Store async loop reference
        scanner.async_loop = asyncio.get_event_loop()

        await scanner.start()

    except KeyboardInterrupt:
        print("\n🔄 Interrupted by user")
    except Exception as e:
        print(f"❌ Scanner failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())