#!/usr/bin/env python3
"""
ASR Production Server Build Script
Creates standalone executable for enterprise deployment
"""

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add the shared modules to the path
sys.path.insert(0, str(Path(__file__).parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent / "production_server"))

import PyInstaller.__main__

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SPEC_TEMPLATE = Path(__file__).parent / "asr_production_server.spec.template"


def _get_git_commit_hash() -> str:
    """Return the short git commit hash, or 'unknown' on failure."""
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


class ProductionServerBuilder:
    """Build ASR Production Server executable"""

    def __init__(self, build_dir: str = "dist/production_server"):
        self.build_dir = Path(build_dir)
        self.spec_file = Path("asr_production_server.spec")
        self.project_root = Path(__file__).parent
        self.git_commit = _get_git_commit_hash()

    def create_spec_file(self) -> None:
        """Create PyInstaller spec file from template, injecting git commit hash."""
        logger.info("Creating PyInstaller spec file...")

        if SPEC_TEMPLATE.exists():
            spec_content = SPEC_TEMPLATE.read_text(encoding="utf-8")
            spec_content = spec_content.replace("{{GIT_COMMIT}}", self.git_commit)
        else:
            logger.warning(
                "Spec template not found at %s, generating inline", SPEC_TEMPLATE
            )
            spec_content = self._generate_spec_content()

        self.spec_file.write_text(spec_content.strip(), encoding="utf-8")
        logger.info(
            "Spec file created: %s (commit: %s)", self.spec_file, self.git_commit
        )

    def _generate_spec_content(self) -> str:
        """Fallback: generate spec content inline when template is missing."""
        return """
# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

project_root = Path(SPECPATH)
production_server_path = project_root / "production_server"
shared_path = project_root / "shared"

a = Analysis(
    [str(production_server_path / "main_server.py")],
    pathex=[
        str(production_server_path),
        str(shared_path),
        str(production_server_path / "api"),
        str(production_server_path / "services"),
        str(production_server_path / "config"),
        str(shared_path / "core"),
        str(shared_path / "api"),
        str(shared_path / "utils")
    ],
    binaries=[],
    datas=[
        (str(production_server_path / "config" / "gl_accounts.json"), "config"),
        (str(production_server_path / "config" / "settings.py"), "config"),
        (str(production_server_path / "api" / "templates"), "api/templates"),
        (str(shared_path / "data"), "shared/data"),
    ],
    hiddenimports=[
        # FastAPI and dependencies
        'fastapi',
        'uvicorn',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'starlette',
        'starlette.applications',
        'starlette.middleware',
        'starlette.routing',

        # Pydantic
        'pydantic',
        'pydantic.main',
        'pydantic.fields',
        'pydantic.types',
        'pydantic.validators',

        # Database
        'sqlalchemy',
        'sqlalchemy.dialects',
        'sqlalchemy.dialects.postgresql',
        'sqlalchemy.dialects.sqlite',
        'psycopg2',
        'aiosqlite',

        # AI Services
        'anthropic',
        'openai',

        # HTTP and networking
        'aiohttp',
        'requests',
        'urllib3',

        # JSON and data processing
        'orjson',
        'ujson',
        'json',

        # Crypto and security
        'cryptography',
        'jwt',
        'passlib',

        # File processing
        'PyPDF2',
        'pdf2image',
        'Pillow',

        # Logging
        'structlog',
        'loguru',

        # Shared modules
        'shared',
        'shared.core',
        'shared.core.models',
        'shared.core.exceptions',
        'shared.api',
        'shared.utils',

        # Production server modules
        'production_server',
        'production_server.services',
        'production_server.api',
        'production_server.config',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'jupyter',
        'IPython',
        # Exclude AWS packages - deep nested data files exceed Windows path limits
        'botocore',
        'boto3',
        'awscli',
        's3transfer',
        'aiobotocore',
        # Exclude other heavy unused packages
        'tensorflow',
        'torch',
        'transformers',
        'pygame',
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
    name='ASR_Production_Server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep console for server monitoring
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path if available
    version_file=None,  # Add version info if available
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ASR_Production_Server'
)
"""

        return spec_content

    def _write_version_file(self) -> None:
        """Write a version metadata file into the dist directory."""
        from shared.core.constants import VERSION

        dist_path = Path("dist/ASR_Production_Server")
        dist_path.mkdir(parents=True, exist_ok=True)
        version_info = {
            "version": VERSION,
            "git_commit": self.git_commit,
        }
        import json

        (dist_path / "version.json").write_text(
            json.dumps(version_info, indent=2), encoding="utf-8"
        )
        logger.info("Version file written: %s", version_info)

    def build_executable(self) -> None:
        """Build the production server executable"""
        logger.info("Building ASR Production Server executable...")

        try:
            PyInstaller.__main__.run(
                [
                    str(self.spec_file),
                    "--clean",
                    "--noconfirm",
                    "--log-level=INFO",
                ]
            )
            self._write_version_file()
            logger.info("Production server executable built successfully")

        except Exception as e:
            logger.error("Build failed: %s", e)
            raise

    def create_config_files(self) -> None:
        """Create default configuration files for distribution"""
        logger.info("⚙️ Creating configuration files...")

        dist_path = Path("dist/ASR_Production_Server")
        config_path = dist_path / "config"
        config_path.mkdir(exist_ok=True)

        # Create .env.template
        env_template = """# ASR Production Server Configuration
# Copy to .env and customize for your environment

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/asr_records
# For SQLite (development): sqlite:///./asr_records.db

# Claude AI Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=2
RELOAD=false

# Storage Configuration
STORAGE_BACKEND=local
STORAGE_PATH=./storage
# For S3: s3://your-bucket-name

# Security
JWT_SECRET_KEY=your-256-bit-secret-key-here
API_RATE_LIMIT=1000

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Multi-tenant Configuration
DEFAULT_TENANT_ID=default
TENANT_ISOLATION=true

# Feature Flags
ENABLE_CLAUDE_VISION=true
ENABLE_PAYMENT_DETECTION=true
ENABLE_ROUTING_AUDIT=true
ENABLE_MANUAL_REVIEW=true
"""

        (config_path / ".env.template").write_text(env_template)

        # Create startup script
        startup_script = '''#!/usr/bin/env python3
"""
ASR Production Server Startup Script
Easy server launch with configuration validation
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("ASR Production Server Startup")
    print("=" * 50)

    # Check for .env file
    if not Path(".env").exists():
        if Path("config/.env.template").exists():
            print("No .env file found!")
            print("Please copy config/.env.template to .env and configure your settings")
            return 1
        else:
            print("No configuration found!")
            return 1

    # Launch server
    print("Starting ASR Production Server...")

    try:
        if os.name == 'nt':  # Windows
            subprocess.run([".\\\\ASR_Production_Server.exe"], check=True)
        else:  # Unix/Linux
            subprocess.run(["./ASR_Production_Server"], check=True)
    except KeyboardInterrupt:
        print("\\nServer shutdown requested")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Server failed to start: {e}")
        return 1
    except FileNotFoundError:
        print("ASR_Production_Server executable not found!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''

        (dist_path / "start_server.py").write_text(startup_script, encoding="utf-8")

        logger.info(f"✅ Configuration files created in: {dist_path}")

    def build(self) -> None:
        """Complete build process"""
        logger.info("🚀 Starting ASR Production Server build...")

        try:
            # Create build directory
            self.build_dir.parent.mkdir(parents=True, exist_ok=True)

            # Build process
            self.create_spec_file()
            self.build_executable()
            self.create_config_files()

            # Success message
            logger.info("=" * 60)
            logger.info("✅ ASR Production Server build completed successfully!")
            logger.info(f"📁 Executable location: dist/ASR_Production_Server/")
            logger.info("📋 Next steps:")
            logger.info("  1. Copy config/.env.template to .env")
            logger.info("  2. Configure your database and API keys")
            logger.info("  3. Run python start_server.py")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ Build failed: {e}")
            raise


def main():
    """Build script entry point"""
    builder = ProductionServerBuilder()
    builder.build()


if __name__ == "__main__":
    main()
