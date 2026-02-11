"""
ASR Document Scanner
Desktop client for workplace scanning with offline capabilities and server integration

Features:
- Desktop GUI for document scanning and upload
- Offline document queue with retry logic
- Auto-discovery of production servers on network
- Scanner hardware integration (TWAIN/WIA)
- Real-time upload progress and status tracking
"""

__version__ = "2.0.0"
__description__ = "ASR Document Scanner - Desktop Scanning Client"

# Export main components
from .main_scanner import ASRDocumentScannerLauncher, main
from .config.scanner_settings import ScannerSettings, scanner_settings

__all__ = [
    "ASRDocumentScannerLauncher",
    "main",
    "ScannerSettings",
    "scanner_settings"
]