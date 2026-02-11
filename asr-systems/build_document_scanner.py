#!/usr/bin/env python3
"""
ASR Document Scanner Build Script
Creates standalone desktop application for workplace document scanning
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any

# Add the shared modules to the path
sys.path.insert(0, str(Path(__file__).parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent / "document-scanner"))

import PyInstaller.__main__
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentScannerBuilder:
    """Build ASR Document Scanner desktop application"""

    def __init__(self, build_dir: str = "dist/document-scanner"):
        self.build_dir = Path(build_dir)
        self.spec_file = Path("asr_document_scanner.spec")
        self.project_root = Path(__file__).parent

    def create_spec_file(self) -> None:
        """Create PyInstaller spec file for document scanner"""
        logger.info("📝 Creating PyInstaller spec file...")

        spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

project_root = Path(SPECPATH)
document_scanner_path = project_root / "document-scanner"
shared_path = project_root / "shared"

a = Analysis(
    [str(document_scanner_path / "main_scanner.py")],
    pathex=[
        str(document_scanner_path),
        str(shared_path),
        str(document_scanner_path / "services"),
        str(document_scanner_path / "gui"),
        str(document_scanner_path / "config"),
        str(shared_path / "core"),
        str(shared_path / "api"),
        str(shared_path / "utils")
    ],
    binaries=[],
    datas=[
        (str(document_scanner_path / "config" / "scanner_settings.py"), "config"),
        (str(document_scanner_path / "gui" / "assets"), "gui/assets"),
        (str(shared_path / "data"), "shared/data"),
    ],
    hiddenimports=[
        # Tkinter GUI
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',

        # HTTP client
        'aiohttp',
        'aiohttp.client',
        'aiohttp.connector',
        'requests',
        'urllib3',

        # Async support
        'asyncio',
        'asyncio.tasks',
        'asyncio.events',
        'asyncio.queues',
        'concurrent.futures',

        # Database (SQLite for offline queue)
        'sqlite3',
        'aiosqlite',

        # JSON and data processing
        'json',
        'orjson',
        'ujson',

        # File processing
        'pathlib',
        'mimetypes',
        'tempfile',

        # Image processing for scanner
        'PIL',
        'Pillow',
        'PIL.Image',
        'PIL.ImageTk',

        # Scanner hardware support
        'twain',  # If available
        'winscan',  # Windows scanning

        # Configuration
        'configparser',
        'yaml',
        'pydantic',

        # Crypto for secure communication
        'cryptography',

        # Logging
        'logging',
        'logging.handlers',

        # Shared modules
        'shared',
        'shared.core',
        'shared.core.models',
        'shared.core.exceptions',
        'shared.api',
        'shared.utils',

        # Document scanner modules
        'document_scanner',
        'document_scanner.services',
        'document_scanner.gui',
        'document_scanner.config',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'jupyter',
        'IPython',
        'fastapi',
        'uvicorn',
        'django',
        'flask',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ASR_Document_Scanner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI application, no console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(document_scanner_path / "gui" / "assets" / "scanner_icon.ico") if (document_scanner_path / "gui" / "assets" / "scanner_icon.ico").exists() else None,
    version_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ASR_Document_Scanner'
)
'''

        self.spec_file.write_text(spec_content.strip())
        logger.info(f"✅ Spec file created: {self.spec_file}")

    def build_executable(self) -> None:
        """Build the document scanner executable"""
        logger.info("🏗️ Building ASR Document Scanner executable...")

        try:
            # Run PyInstaller
            PyInstaller.__main__.run([
                str(self.spec_file),
                '--clean',
                '--noconfirm',
                '--log-level=INFO'
            ])

            logger.info("✅ Document scanner executable built successfully")

        except Exception as e:
            logger.error(f"❌ Build failed: {e}")
            raise

    def create_config_files(self) -> None:
        """Create default configuration files for distribution"""
        logger.info("⚙️ Creating configuration files...")

        dist_path = Path("dist/ASR_Document_Scanner")
        config_path = dist_path / "config"
        config_path.mkdir(exist_ok=True)

        # Create scanner_config.yaml template
        scanner_config = '''# ASR Document Scanner Configuration

# Production Server Connection
production_servers:
  - name: "Local Development"
    url: "http://localhost:8000"
    api_key: ""
    enabled: true

  - name: "Production Server"
    url: "https://your-asr-server.com"
    api_key: ""
    enabled: false

# Scanner Settings
scanner:
  auto_discovery: true
  retry_attempts: 3
  timeout_seconds: 30

  # Hardware scanner settings (if available)
  hardware:
    enabled: false
    device_name: "default"
    resolution_dpi: 300
    color_mode: "color"  # color, grayscale, black_white

  # File processing settings
  file_processing:
    supported_formats: ["pdf", "jpg", "jpeg", "png", "tiff", "bmp"]
    max_file_size_mb: 10
    auto_compress: true
    compression_quality: 85

# Upload Queue
upload_queue:
  max_pending_documents: 1000
  retry_interval_seconds: 60
  batch_size: 5
  auto_upload: true

# Local Storage
local_storage:
  data_directory: "./scanner_data"
  queue_database: "./scanner_data/queue.db"
  temp_directory: "./scanner_data/temp"

  # Cleanup settings
  cleanup:
    auto_cleanup: true
    keep_completed_days: 7
    keep_failed_days: 30

# UI Settings
ui:
  theme: "default"  # default, dark, light
  window_size: [800, 600]
  window_position: "center"
  show_preview: true
  auto_refresh_interval: 30

# Logging
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file_logging: true
  log_file: "./scanner_data/scanner.log"
  max_log_size_mb: 10
  backup_count: 5

# Security
security:
  encrypt_local_queue: false
  verify_ssl_certificates: true
  connection_timeout: 30

# Feature Flags
features:
  offline_mode: true
  batch_upload: true
  auto_classification_preview: true
  drag_drop_upload: true
  watch_folder: false  # Enable folder watching for auto-upload
'''

        (config_path / "scanner_config.yaml").write_text(scanner_config)

        # Create startup batch file for Windows
        startup_bat = '''@echo off
title ASR Document Scanner

echo Starting ASR Document Scanner...
echo.

:: Check if config exists
if not exist "config\\scanner_config.yaml" (
    echo Configuration file not found!
    echo Please ensure scanner_config.yaml is properly configured.
    pause
    exit /b 1
)

:: Launch scanner
ASR_Document_Scanner.exe

if errorlevel 1 (
    echo.
    echo Scanner exited with error. Check logs for details.
    pause
)
'''

        (dist_path / "start_scanner.bat").write_text(startup_bat)

        # Create Linux/Mac startup script
        startup_sh = '''#!/bin/bash

echo "Starting ASR Document Scanner..."
echo

# Check if config exists
if [ ! -f "config/scanner_config.yaml" ]; then
    echo "Configuration file not found!"
    echo "Please ensure scanner_config.yaml is properly configured."
    read -p "Press Enter to continue..."
    exit 1
fi

# Make executable if needed
chmod +x ASR_Document_Scanner 2>/dev/null

# Launch scanner
./ASR_Document_Scanner

if [ $? -ne 0 ]; then
    echo
    echo "Scanner exited with error. Check logs for details."
    read -p "Press Enter to continue..."
fi
'''

        (dist_path / "start_scanner.sh").write_text(startup_sh)
        os.chmod(dist_path / "start_scanner.sh", 0o755)

        # Create README
        readme_content = '''# ASR Document Scanner

Desktop application for workplace document scanning and upload to ASR Production Server.

## Features

### Document Processing
- **Drag & Drop Upload** - Simply drag files into the application
- **Scanner Hardware Support** - Connect to TWAIN/WIA compatible scanners
- **Batch Processing** - Upload multiple documents simultaneously
- **Offline Queue** - Continue working when server is unavailable
- **Auto-Discovery** - Automatically find ASR Production Servers on network

### File Support
- **PDF Documents** - Native PDF processing and optimization
- **Image Formats** - JPG, PNG, TIFF, BMP support with compression
- **File Validation** - Size limits and format verification
- **Preview Mode** - Preview documents before upload

### Enterprise Integration
- **Multi-Server Support** - Configure multiple production servers
- **API Key Authentication** - Secure connection to production servers
- **Upload Progress** - Real-time progress tracking and retry logic
- **Audit Logging** - Complete upload history and error tracking

## Quick Start

### Windows
1. **Double-click `start_scanner.bat`** - Launches the scanner application
2. **Configure Servers** - Edit `config/scanner_config.yaml` with your server details
3. **Start Scanning** - Use drag-drop or scanner hardware to add documents

### Linux/Mac
1. **Run `./start_scanner.sh`** - Launches the scanner application
2. **Configure Servers** - Edit `config/scanner_config.yaml` with your server details
3. **Start Scanning** - Use drag-drop to add documents for upload

### Manual Launch
```bash
# Direct executable launch
./ASR_Document_Scanner          # Linux/Mac
ASR_Document_Scanner.exe        # Windows
```

## Configuration

### Production Server Connection
Edit `config/scanner_config.yaml`:

```yaml
production_servers:
  - name: "My ASR Server"
    url: "https://your-asr-server.com"
    api_key: "your-api-key-here"
    enabled: true
```

### Scanner Hardware
If you have a TWAIN/WIA compatible scanner:

```yaml
scanner:
  hardware:
    enabled: true
    device_name: "Your Scanner Name"
    resolution_dpi: 300
    color_mode: "color"
```

### Upload Settings
```yaml
upload_queue:
  auto_upload: true           # Upload immediately when server available
  batch_size: 5              # Number of documents per batch
  retry_interval_seconds: 60  # How often to retry failed uploads
```

## Main Interface

### Upload Area
- **Drag & Drop Zone** - Drop files directly into the main window
- **File Browser** - Click to browse and select files
- **Scanner Button** - Access hardware scanner (if configured)

### Queue Management
- **Pending Queue** - Documents waiting for upload
- **Progress View** - Current upload progress and status
- **History Log** - Completed uploads and any errors

### Server Status
- **Connection Status** - Shows connection to production servers
- **Server Discovery** - Automatically detect servers on network
- **API Health** - Monitor server availability and response times

## Offline Mode

### Queue System
- Documents are stored locally in SQLite database
- Automatic retry when server becomes available
- No data loss during network outages

### Local Storage
- Queue database: `scanner_data/queue.db`
- Temporary files: `scanner_data/temp/`
- Logs: `scanner_data/scanner.log`

## Troubleshooting

### Scanner Won't Start
1. Check configuration file exists: `config/scanner_config.yaml`
2. Verify no other scanner applications are running
3. Check logs in `scanner_data/scanner.log`

### Upload Failures
1. Verify server URL and API key in configuration
2. Check network connectivity to production server
3. Review file size limits (default 10MB max)
4. Check server status at `/health` endpoint

### Scanner Hardware Issues
1. Ensure scanner drivers are installed
2. Check device name in configuration matches actual device
3. Verify no other applications are using the scanner
4. Try disabling hardware scanner and use file upload

### Configuration Issues
1. Verify YAML syntax in `scanner_config.yaml`
2. Check file permissions on configuration directory
3. Reset to default configuration if needed

## Support

### Log Files
- Application logs: `scanner_data/scanner.log`
- Queue database: `scanner_data/queue.db`
- Temporary files: `scanner_data/temp/`

### Network Testing
Test server connectivity:
```bash
curl http://your-asr-server:8000/health
```

### Server Discovery
The scanner automatically discovers ASR Production Servers on the local network.
Manual server configuration is recommended for production environments.

---

ASR Document Scanner - Workplace Document Management
© 2024 ASR Inc. All rights reserved.
'''

        (dist_path / "README.md").write_text(readme_content)

        logger.info(f"✅ Configuration files created in: {dist_path}")

    def create_installer(self) -> None:
        """Create installation package"""
        logger.info("📦 Creating installer package...")

        # Create Windows installer
        installer_script = '''@echo off
echo ASR Document Scanner Installer
echo ====================================

echo Checking system requirements...

:: Check Windows version (Windows 10+ recommended)
for /f "tokens=2 delims=[]" %%i in ('ver') do set winver=%%i
echo Windows Version: %winver%

:: Create installation directory
set INSTALL_DIR=%USERPROFILE%\\ASR_Document_Scanner
echo Installing to: %INSTALL_DIR%

if exist "%INSTALL_DIR%" (
    echo Directory already exists. This will update the installation.
    echo Current files will be backed up to %INSTALL_DIR%_backup
    if exist "%INSTALL_DIR%_backup" rmdir /s /q "%INSTALL_DIR%_backup"
    move "%INSTALL_DIR%" "%INSTALL_DIR%_backup"
)

mkdir "%INSTALL_DIR%" 2>nul
xcopy /E /I /Y "ASR_Document_Scanner\\*" "%INSTALL_DIR%"

echo.
echo Creating desktop shortcut...
powershell -command "& { $WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\ASR Document Scanner.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\start_scanner.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = '%INSTALL_DIR%\\ASR_Document_Scanner.exe'; $Shortcut.Save() }"

echo.
echo Installation completed successfully!
echo.
echo To start the scanner:
echo 1. Double-click "ASR Document Scanner" on your desktop, or
echo 2. Navigate to: %INSTALL_DIR%
echo 3. Configure your server in config\\scanner_config.yaml
echo 4. Run: start_scanner.bat
echo.
echo Installation directory: %INSTALL_DIR%
pause
'''

        installer_path = Path("dist/install_document_scanner.bat")
        installer_path.write_text(installer_script)

        logger.info(f"✅ Installer created: {installer_path}")

    def cleanup(self) -> None:
        """Clean up build artifacts"""
        logger.info("🧹 Cleaning up build artifacts...")

        cleanup_paths = [
            "build",
            "__pycache__",
            "*.pyc",
            self.spec_file
        ]

        for path in cleanup_paths:
            if Path(path).exists():
                if Path(path).is_file():
                    Path(path).unlink()
                else:
                    shutil.rmtree(path, ignore_errors=True)

        logger.info("✅ Cleanup completed")

    def build(self) -> None:
        """Complete build process"""
        logger.info("🚀 Starting ASR Document Scanner build...")

        try:
            # Create build directory
            self.build_dir.parent.mkdir(parents=True, exist_ok=True)

            # Build process
            self.create_spec_file()
            self.build_executable()
            self.create_config_files()
            self.create_installer()

            # Success message
            logger.info("=" * 60)
            logger.info("✅ ASR Document Scanner build completed successfully!")
            logger.info(f"📁 Executable location: dist/ASR_Document_Scanner/")
            logger.info(f"💾 Installer: dist/install_document_scanner.bat")
            logger.info("📋 Next steps:")
            logger.info("  1. Configure production server in config/scanner_config.yaml")
            logger.info("  2. Run start_scanner.bat (Windows) or start_scanner.sh (Linux/Mac)")
            logger.info("  3. Start scanning and uploading documents!")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ Build failed: {e}")
            raise


def main():
    """Build script entry point"""
    builder = DocumentScannerBuilder()
    builder.build()


if __name__ == "__main__":
    main()