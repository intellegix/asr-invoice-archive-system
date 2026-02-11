#!/usr/bin/env python3
"""
ASR Invoice Archive System - Deployment Script
Deploys the system using the most stable method (source code)
"""

import os
import sys
import json
import subprocess
from pathlib import Path
import shutil
from datetime import datetime

class ASRDeployment:
    def __init__(self, deployment_type="source"):
        self.deployment_type = deployment_type
        self.project_root = Path(__file__).parent
        self.deploy_dir = self.project_root / "deployment"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def create_deployment_directory(self):
        """Create clean deployment directory"""
        print("📁 Creating deployment directory...")

        if self.deploy_dir.exists():
            shutil.rmtree(self.deploy_dir)

        self.deploy_dir.mkdir(exist_ok=True)

        # Create subdirectories
        (self.deploy_dir / "production-server").mkdir()
        (self.deploy_dir / "document-scanner").mkdir()
        (self.deploy_dir / "shared").mkdir()
        (self.deploy_dir / "config").mkdir()

        print(f"✅ Deployment directory created: {self.deploy_dir}")

    def copy_source_code(self):
        """Copy source code for deployment"""
        print("📋 Copying source code...")

        # Copy shared components
        shutil.copytree(
            self.project_root / "shared",
            self.deploy_dir / "shared",
            dirs_exist_ok=True
        )

        # Copy production server
        shutil.copytree(
            self.project_root / "production-server",
            self.deploy_dir / "production-server",
            dirs_exist_ok=True
        )

        # Copy document scanner
        shutil.copytree(
            self.project_root / "document-scanner",
            self.deploy_dir / "deployment" / "document-scanner",
            dirs_exist_ok=True
        )

        print("✅ Source code copied successfully")

    def create_requirements_file(self):
        """Create requirements.txt for deployment"""
        print("📦 Creating requirements.txt...")

        requirements = """# ASR Invoice Archive System - Requirements
# Production Server Dependencies
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
sqlalchemy>=2.0.23
aiosqlite>=0.19.0
psycopg2-binary>=2.9.9
anthropic>=0.7.7
python-multipart>=0.0.6
python-dotenv>=1.0.0
structlog>=23.2.0

# Document Scanner Dependencies
tkinter  # Usually included with Python
requests>=2.31.0
pillow>=10.1.0
watchdog>=3.0.0

# Shared Dependencies
pydantic>=2.5.0
aiofiles>=23.2.0
python-dateutil>=2.8.2

# Optional: For advanced features
redis>=5.0.1
boto3>=1.29.0  # For S3 storage
cryptography>=41.0.7  # For enhanced security
"""

        (self.deploy_dir / "requirements.txt").write_text(requirements)
        print("✅ Requirements file created")

    def create_startup_scripts(self):
        """Create startup scripts"""
        print("🚀 Creating startup scripts...")

        # Production Server startup script
        server_startup = """#!/usr/bin/env python3
\"\"\"
ASR Production Server - Startup Script
\"\"\"

import os
import sys
import uvicorn
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent / "production-server"))

def main():
    print("🚀 Starting ASR Production Server...")
    print("=" * 50)

    # Check environment
    if not Path(".env").exists():
        print("⚠️  Warning: .env file not found!")
        print("📋 Using default configuration")

    # Import and start server
    try:
        from production_server.main_server import app

        print("✅ Application loaded successfully")
        print("🌐 Starting server on http://localhost:8000")
        print("📊 API documentation: http://localhost:8000/docs")
        print("🔍 Health check: http://localhost:8000/health")
        print("")
        print("Press Ctrl+C to stop the server")
        print("=" * 50)

        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,
            workers=1
        )

    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
"""

        (self.deploy_dir / "start_production_server.py").write_text(server_startup)

        # Document Scanner startup script
        scanner_startup = """#!/usr/bin/env python3
\"\"\"
ASR Document Scanner - Startup Script
\"\"\"

import os
import sys
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent / "document-scanner"))

def main():
    print("📱 Starting ASR Document Scanner...")
    print("=" * 50)

    try:
        from document_scanner.main_scanner import main as scanner_main
        print("✅ Document Scanner loaded successfully")
        return scanner_main()

    except Exception as e:
        print(f"❌ Failed to start Document Scanner: {e}")
        print("💡 Make sure you have a display available for the GUI")
        return 1

if __name__ == "__main__":
    sys.exit(main())
"""

        (self.deploy_dir / "start_document_scanner.py").write_text(scanner_startup)

        print("✅ Startup scripts created")

    def create_configuration(self):
        """Create deployment configuration"""
        print("⚙️ Creating configuration files...")

        # Environment template
        env_template = """# ASR Invoice Archive System - Production Configuration
# Copy this file to .env and customize for your environment

# === PRODUCTION SERVER CONFIGURATION ===

# Database Configuration
DATABASE_URL=sqlite:///./asr_records.db
# For PostgreSQL: DATABASE_URL=postgresql://user:password@localhost:5432/asr_records

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
# For S3: STORAGE_BACKEND=s3, S3_BUCKET=your-bucket-name

# Security
JWT_SECRET_KEY=your-secure-256-bit-secret-key-here
API_RATE_LIMIT=1000

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Multi-tenant Configuration
DEFAULT_TENANT_ID=default
TENANT_ISOLATION=true

# === DOCUMENT SCANNER CONFIGURATION ===

# Production Server Connection
PRODUCTION_SERVER_URL=http://localhost:8000
API_KEY=your_api_key_here

# Scanner Configuration
WATCH_FOLDERS=./watch,./inbox
UPLOAD_ON_DETECTION=true
RETRY_ATTEMPTS=3
BATCH_SIZE=10

# === FEATURE FLAGS ===
ENABLE_CLAUDE_VISION=true
ENABLE_PAYMENT_DETECTION=true
ENABLE_ROUTING_AUDIT=true
ENABLE_MANUAL_REVIEW=true
"""

        (self.deploy_dir / "config" / ".env.template").write_text(env_template)

        # Deployment info
        deploy_info = {
            "deployment_timestamp": self.timestamp,
            "deployment_type": self.deployment_type,
            "version": "1.0.0",
            "system_name": "ASR Invoice Archive System",
            "components": {
                "production_server": {
                    "type": "FastAPI Application",
                    "features": ["79+ GL Accounts", "5-Method Payment Detection", "4 Billing Destinations", "Claude AI Integration"],
                    "startup_command": "python start_production_server.py"
                },
                "document_scanner": {
                    "type": "Tkinter GUI Application",
                    "features": ["Drag-Drop Upload", "Offline Queue", "Server Integration", "Scanner Hardware Support"],
                    "startup_command": "python start_document_scanner.py"
                }
            },
            "urls": {
                "production_server": "http://localhost:8000",
                "api_documentation": "http://localhost:8000/docs",
                "health_check": "http://localhost:8000/health"
            }
        }

        with open(self.deploy_dir / "config" / "deployment_info.json", 'w') as f:
            json.dump(deploy_info, f, indent=2)

        print("✅ Configuration files created")

    def create_installation_guide(self):
        """Create installation and usage guide"""
        print("📖 Creating installation guide...")

        guide = """# ASR Invoice Archive System - Deployment Guide

## 🚀 Quick Start

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy template and customize
cp config/.env.template .env
# Edit .env file with your settings
```

### 3. Start Production Server
```bash
python start_production_server.py
```

### 4. Start Document Scanner (separate terminal)
```bash
python start_document_scanner.py
```

## 📊 System URLs

- **Production Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🔧 Configuration

### Required Settings

1. **ANTHROPIC_API_KEY**: Your Claude AI API key for document processing
2. **DATABASE_URL**: Database connection (SQLite default, PostgreSQL for production)
3. **JWT_SECRET_KEY**: Secure secret key for API authentication

### Optional Settings

- **Storage Backend**: Local filesystem or AWS S3
- **Multi-tenant**: Enable for client isolation
- **Feature Flags**: Enable/disable specific features

## 🏗️ System Architecture

```
┌─────────────────────┐    ┌─────────────────────┐
│   Document Scanner  │    │   Production Server │
│                     │    │                     │
│ • Drag-Drop Upload  │────│ • FastAPI Backend   │
│ • Offline Queue     │    │ • 79+ GL Accounts   │
│ • Server Discovery  │    │ • Payment Detection │
│ • Hardware Support  │    │ • Billing Routing   │
└─────────────────────┘    └─────────────────────┘
           │                           │
           └───────────────────────────┘
                    │
           ┌─────────────────────┐
           │   Shared Components │
           │                     │
           │ • Data Models       │
           │ • API Client        │
           │ • Common Utilities  │
           └─────────────────────┘
```

## 📋 Key Features

### Production Server
- **79+ QuickBooks GL Accounts** with intelligent keyword matching
- **5-Method Payment Detection** consensus system
- **4 Billing Destinations** with automated routing
- **Claude AI Integration** for document classification
- **Complete Audit Trails** with confidence scoring
- **Multi-tenant Architecture** for client isolation

### Document Scanner
- **Professional GUI** with drag-drop interface
- **Offline Document Queue** for network resilience
- **Automatic Server Discovery** and integration
- **Scanner Hardware Support** (TWAIN/WIA)
- **Batch Processing** capabilities

## 🔍 Verification

Test the deployment:

```bash
# Test production server health
curl http://localhost:8000/health

# Test API endpoints
curl http://localhost:8000/api/status

# View API documentation
open http://localhost:8000/docs
```

## 🎯 Next Steps

1. **Configure API Keys**: Add your Anthropic API key to .env
2. **Test Document Processing**: Upload sample invoice through scanner
3. **Customize GL Accounts**: Modify production-server/config/gl_accounts.json
4. **Set Up Monitoring**: Configure logging and health checks
5. **Production Database**: Switch to PostgreSQL for production use

## 📞 Support

For issues or questions:
- Check the health endpoint: http://localhost:8000/health
- Review logs in the console output
- Verify configuration in .env file
- Test individual components separately

---

🎉 **Your ASR Invoice Archive System is ready for production!**
"""

        (self.deploy_dir / "README.md").write_text(guide)
        print("✅ Installation guide created")

    def deploy(self):
        """Execute complete deployment"""
        print("🚀 DEPLOYING ASR INVOICE ARCHIVE SYSTEM")
        print("=" * 60)

        try:
            self.create_deployment_directory()
            self.copy_source_code()
            self.create_requirements_file()
            self.create_startup_scripts()
            self.create_configuration()
            self.create_installation_guide()

            print("\n" + "=" * 60)
            print("✅ DEPLOYMENT SUCCESSFUL!")
            print("=" * 60)
            print(f"📁 Deployment Location: {self.deploy_dir}")
            print(f"🕒 Deployment Time: {self.timestamp}")
            print("\n🚀 Quick Start Commands:")
            print(f"   cd {self.deploy_dir}")
            print("   pip install -r requirements.txt")
            print("   cp config/.env.template .env")
            print("   # Edit .env with your API keys")
            print("   python start_production_server.py")
            print("\n📊 System URLs:")
            print("   Production Server: http://localhost:8000")
            print("   API Docs: http://localhost:8000/docs")
            print("   Health Check: http://localhost:8000/health")
            print("\n🎉 Your ASR system is ready for production!")

            return True

        except Exception as e:
            print(f"\n❌ DEPLOYMENT FAILED: {e}")
            return False

def main():
    """Main deployment function"""
    deployer = ASRDeployment("source")
    success = deployer.deploy()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())