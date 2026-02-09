# ASR Production Server Settings
# This file imports from production_settings.py

try:
    from .production_settings import *  # Import all production settings
except (ImportError, SystemError):
    from production_settings import *

# Additional build-time settings
BUILD_INFO = {
    "version": "1.0.0",
    "build_type": "production",
    "description": "ASR Invoice Archive System - Production Server"
}