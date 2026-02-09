"""
ASR Production Server
Enterprise document processing server with sophisticated capabilities:
• 79 QuickBooks GL Accounts with keyword matching
• 5-Method Payment Detection with consensus scoring
• 4 Billing Destination routing with audit trails
• Multi-tenant document isolation
• Scanner client API for distributed processing
"""

__version__ = "2.0.0"
__description__ = "ASR Production Server - Enterprise Document Processing"

# Export main components (with fallbacks for PyInstaller EXE context)
try:
    from .main_server import ASRProductionServerLauncher, main
except (ImportError, SystemError):
    try:
        from main_server import ASRProductionServerLauncher, main
    except ImportError:
        ASRProductionServerLauncher = None
        main = None

try:
    from .config.production_settings import ProductionSettings, production_settings
except (ImportError, SystemError):
    try:
        from config.production_settings import ProductionSettings, production_settings
    except ImportError:
        ProductionSettings = None
        production_settings = None

__all__ = [
    "ASRProductionServerLauncher",
    "main",
    "ProductionSettings",
    "production_settings"
]