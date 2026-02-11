#!/usr/bin/env python3
"""
ASR System Distribution Builder
Creates complete distribution package with both applications and documentation
"""

import os
import sys
import shutil
import subprocess
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BuildResult:
    """Build step result"""
    component: str
    success: bool
    execution_time: float
    message: str
    details: Optional[Dict[str, Any]] = None


class ASRDistributionBuilder:
    """Complete ASR system distribution package builder"""

    def __init__(self, output_dir: str = "dist/ASR_Complete_Package"):
        self.output_dir = Path(output_dir)
        self.project_root = Path(__file__).parent
        self.build_results: List[BuildResult] = []
        self.build_start_time = time.time()

    def record_result(self, component: str, success: bool, execution_time: float,
                     message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Record build step result"""
        result = BuildResult(
            component=component,
            success=success,
            execution_time=execution_time,
            message=message,
            details=details
        )
        self.build_results.append(result)

        status_icon = "✅" if success else "❌"
        logger.info(f"{status_icon} {component}: {message} ({execution_time:.2f}s)")

    def clean_build_environment(self) -> None:
        """Clean previous build artifacts"""
        logger.info("🧹 Cleaning build environment...")
        start_time = time.time()

        try:
            # Remove existing distribution directory
            if self.output_dir.exists():
                shutil.rmtree(self.output_dir)

            # Remove build artifacts
            cleanup_paths = [
                "build",
                "dist/ASR_Production_Server",
                "dist/ASR_Document_Scanner",
                "__pycache__"
            ]

            for path_str in cleanup_paths:
                path = Path(path_str)
                if path.exists():
                    if path.is_file():
                        path.unlink()
                    else:
                        shutil.rmtree(path, ignore_errors=True)

            execution_time = time.time() - start_time
            self.record_result("clean_environment", True, execution_time, "Build environment cleaned")

        except Exception as e:
            execution_time = time.time() - start_time
            self.record_result("clean_environment", False, execution_time, f"Cleanup failed: {e}")

    def build_production_server(self) -> bool:
        """Build production server executable"""
        logger.info("🏭 Building Production Server...")
        start_time = time.time()

        try:
            result = subprocess.run([
                sys.executable, "build_production_server.py"
            ], capture_output=True, text=True, timeout=600)

            execution_time = time.time() - start_time

            if result.returncode == 0:
                # Verify build output exists
                server_exe = Path("dist/ASR_Production_Server/ASR_Production_Server.exe")
                server_unix = Path("dist/ASR_Production_Server/ASR_Production_Server")

                if server_exe.exists() or server_unix.exists():
                    self.record_result(
                        "production_server_build", True, execution_time,
                        "Production server executable built successfully",
                        {"output_size": len(result.stdout)}
                    )
                    return True
                else:
                    self.record_result(
                        "production_server_build", False, execution_time,
                        "Executable not found after build",
                        {"stdout": result.stdout[-200:], "stderr": result.stderr[-200:]}
                    )
                    return False
            else:
                self.record_result(
                    "production_server_build", False, execution_time,
                    f"Build failed with exit code {result.returncode}",
                    {"stdout": result.stdout[-200:], "stderr": result.stderr[-200:]}
                )
                return False

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            self.record_result(
                "production_server_build", False, execution_time,
                "Build timeout (10 minutes)"
            )
            return False
        except Exception as e:
            execution_time = time.time() - start_time
            self.record_result(
                "production_server_build", False, execution_time,
                f"Build error: {e}"
            )
            return False

    def build_document_scanner(self) -> bool:
        """Build document scanner executable"""
        logger.info("📱 Building Document Scanner...")
        start_time = time.time()

        try:
            result = subprocess.run([
                sys.executable, "build_document_scanner.py"
            ], capture_output=True, text=True, timeout=600)

            execution_time = time.time() - start_time

            if result.returncode == 0:
                # Verify build output exists
                scanner_exe = Path("dist/ASR_Document_Scanner/ASR_Document_Scanner.exe")
                scanner_unix = Path("dist/ASR_Document_Scanner/ASR_Document_Scanner")

                if scanner_exe.exists() or scanner_unix.exists():
                    self.record_result(
                        "document_scanner_build", True, execution_time,
                        "Document scanner executable built successfully"
                    )
                    return True
                else:
                    self.record_result(
                        "document_scanner_build", False, execution_time,
                        "Executable not found after build"
                    )
                    return False
            else:
                self.record_result(
                    "document_scanner_build", False, execution_time,
                    f"Build failed with exit code {result.returncode}",
                    {"stdout": result.stdout[-200:], "stderr": result.stderr[-200:]}
                )
                return False

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            self.record_result(
                "document_scanner_build", False, execution_time,
                "Build timeout (10 minutes)"
            )
            return False
        except Exception as e:
            execution_time = time.time() - start_time
            self.record_result(
                "document_scanner_build", False, execution_time,
                f"Build error: {e}"
            )
            return False

    def create_distribution_package(self) -> None:
        """Create complete distribution package"""
        logger.info("📦 Creating distribution package...")
        start_time = time.time()

        try:
            # Create main distribution directory
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Copy production server
            server_src = Path("dist/ASR_Production_Server")
            server_dst = self.output_dir / "Production_Server"
            if server_src.exists():
                shutil.copytree(server_src, server_dst, dirs_exist_ok=True)

            # Copy document scanner
            scanner_src = Path("dist/ASR_Document_Scanner")
            scanner_dst = self.output_dir / "Document_Scanner"
            if scanner_src.exists():
                shutil.copytree(scanner_src, scanner_dst, dirs_exist_ok=True)

            # Copy documentation and configuration
            self.copy_documentation()
            self.create_master_installer()
            self.create_deployment_guide()

            execution_time = time.time() - start_time
            self.record_result(
                "distribution_package", True, execution_time,
                "Distribution package created successfully",
                {"package_size_mb": self.get_directory_size(self.output_dir) / (1024 * 1024)}
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.record_result(
                "distribution_package", False, execution_time,
                f"Package creation failed: {e}"
            )

    def copy_documentation(self) -> None:
        """Copy all documentation to distribution package"""
        logger.info("📚 Copying documentation...")

        # Create docs directory
        docs_dir = self.output_dir / "Documentation"
        docs_dir.mkdir(exist_ok=True)

        # Documentation files to include
        doc_files = {
            "README.md": "Master README for the complete ASR system",
            "ARCHITECTURE.md": "System architecture documentation",
            "DEPLOYMENT_GUIDE.md": "Complete deployment guide",
            "API_REFERENCE.md": "API documentation",
            "TROUBLESHOOTING.md": "Troubleshooting guide"
        }

        # Create master README
        master_readme = '''# ASR Invoice Archive System - Complete Package

## Overview

The ASR Invoice Archive System separation provides two specialized applications for enterprise document processing:

1. **ASR Production Server** - Enterprise document processing with 79 QuickBooks GL accounts, 5-method payment detection, and 4 billing destinations
2. **ASR Document Scanner** - Desktop application for workplace document scanning with offline capabilities

## Quick Start

### Production Server Setup
1. Navigate to `Production_Server/`
2. Copy `config/.env.template` to `.env`
3. Configure your database and API keys
4. Run: `python start_server.py`
5. Access at: http://localhost:8000

### Document Scanner Setup
1. Navigate to `Document_Scanner/`
2. Edit `config/scanner_config.yaml` with your server details
3. Run: `start_scanner.bat` (Windows) or `start_scanner.sh` (Linux/Mac)
4. Start scanning and uploading documents

## Key Features Preserved

### Enterprise Document Processing (Production Server)
- **79 QuickBooks GL Accounts** with sophisticated keyword matching and expense categorization
- **5-Method Payment Detection** using Claude Vision, Claude Text, Regex, Keywords, and Amount Analysis
- **4 Billing Destinations** (Open/Closed Payable/Receivable) with enhanced routing logic and complete audit trails
- **Multi-tenant Architecture** with complete data isolation and tenant-specific configurations
- **Claude AI Integration** for advanced document analysis, classification, and fraud detection

### Workplace Scanning (Document Scanner)
- **Desktop GUI Application** with drag-drop upload interface
- **Scanner Hardware Support** for TWAIN/WIA compatible scanners
- **Offline Queue Management** with automatic retry when server becomes available
- **Auto-Discovery** of production servers on the network
- **Batch Processing** with progress tracking and error handling

## System Requirements

### Production Server
- Python 3.8+ with FastAPI, SQLAlchemy, and Anthropic dependencies
- PostgreSQL database (or SQLite for development)
- Claude AI API key for document analysis
- 4GB+ RAM, 20GB+ storage for production deployment
- Network access for scanner client communication

### Document Scanner
- Windows 10+ (primary), Linux, or macOS
- Scanner hardware (optional) with TWAIN/WIA drivers
- Network access to production server
- 2GB+ RAM, 1GB+ storage for local queue

## Architecture

```
┌─────────────────────┐    ┌──────────────────────────┐
│  Document Scanner   │    │   Production Server      │
│  (Desktop Client)   │◄──►│  (Enterprise Backend)    │
├─────────────────────┤    ├──────────────────────────┤
│ • Drag-drop Upload  │    │ • 79 GL Classifications  │
│ • Scanner Hardware  │    │ • 5-Method Payment Det.  │
│ • Offline Queue     │    │ • 4 Billing Destinations │
│ • Auto-discovery    │    │ • Claude AI Integration  │
│ • Batch Processing  │    │ • Multi-tenant Support   │
└─────────────────────┘    └──────────────────────────┘
```

## Package Contents

```
ASR_Complete_Package/
├── Production_Server/          # Enterprise processing server
│   ├── ASR_Production_Server   # Server executable
│   ├── config/                 # Configuration templates
│   ├── start_server.py        # Easy startup script
│   └── README.md              # Server-specific documentation
├── Document_Scanner/           # Desktop scanning application
│   ├── ASR_Document_Scanner   # Scanner executable
│   ├── config/               # Scanner configuration
│   ├── start_scanner.*       # Platform startup scripts
│   └── README.md            # Scanner-specific documentation
├── Documentation/            # Complete system documentation
├── install_complete.bat     # Windows master installer
├── install_complete.sh      # Unix/Linux master installer
└── README.md               # This file

```

## Business Value

### Immediate Benefits
- **Simplified Deployment**: Single executable distribution instead of complex setup
- **Workplace Efficiency**: Dedicated scanning app for staff document upload
- **Offline Capability**: Work continues when network unavailable
- **Preserved Intelligence**: All existing classification and routing sophistication maintained

### Enterprise Capabilities
- **Complete Feature Preservation**: 79 GL accounts, 5-method payment detection, audit trails
- **Scalable Architecture**: Production server supports multiple scanner clients
- **Multi-tenant Ready**: Foundation for SaaS deployment with client isolation
- **API Integration**: RESTful API with automatic documentation and validation

## Support

### Getting Started
1. Follow the deployment guide in `Documentation/DEPLOYMENT_GUIDE.md`
2. Configure both applications according to your environment
3. Test with sample documents to verify functionality
4. Scale up with additional scanner clients as needed

### Troubleshooting
- Check the troubleshooting guide in `Documentation/TROUBLESHOOTING.md`
- Review application logs for error details
- Verify network connectivity between scanner and server
- Ensure all configuration files are properly set up

### Professional Services
For enterprise deployment, custom configuration, or technical support:
- Complete system architecture consulting
- Multi-tenant SaaS deployment assistance
- Custom GL account and routing rule configuration
- Integration with existing business systems

---

ASR Invoice Archive System - Enterprise Document Processing Platform
© 2024 ASR Inc. All rights reserved.

Built with Python, FastAPI, Claude AI, and modern desktop technologies.
Designed for enterprise scalability while maintaining workplace simplicity.
'''

        (docs_dir / "README.md").write_text(master_readme)

        # Create architecture documentation
        architecture_doc = '''# ASR System Architecture

## System Separation Overview

The ASR Invoice Archive System has been separated into two focused applications:

### 1. ASR Production Server
**Purpose**: Enterprise document processing engine
**Technology**: Python + FastAPI + Claude AI
**Deployment**: Standalone executable or containerized service

**Core Capabilities**:
- 79 QuickBooks GL Accounts with keyword matching
- 5-Method Payment Detection (Claude Vision + Text + Regex + Keywords + Amount)
- 4 Billing Destinations with routing logic (Open/Closed Payable/Receivable)
- Complete audit trails with confidence scoring
- Multi-tenant data isolation
- RESTful API for scanner communication

### 2. ASR Document Scanner
**Purpose**: Desktop scanning and upload client
**Technology**: Python + Tkinter + aiohttp
**Deployment**: Desktop executable with GUI

**Core Capabilities**:
- Drag-and-drop document upload interface
- TWAIN/WIA scanner hardware integration
- Offline queue with automatic retry logic
- Auto-discovery of production servers
- Batch upload with progress tracking

## Communication Architecture

```
┌─────────────────┐  HTTP/JSON API   ┌─────────────────┐
│                 │◄────────────────►│                 │
│  Document       │                  │  Production     │
│  Scanner        │  Document Upload │  Server         │
│  (Client)       │                  │  (Server)       │
│                 │◄────────────────►│                 │
└─────────────────┘  Status Updates  └─────────────────┘
        │                                      │
        │                                      │
        ▼                                      ▼
┌─────────────────┐                  ┌─────────────────┐
│ SQLite Queue    │                  │ PostgreSQL DB   │
│ (Offline)       │                  │ (Enterprise)    │
└─────────────────┘                  └─────────────────┘
```

## API Communication Protocol

### Scanner Registration
```
POST /api/scanner/register
{
  "scanner_name": "Office Scanner 1",
  "capabilities": ["pdf", "jpg", "batch_upload"],
  "version": "1.0.0"
}
```

### Document Upload
```
POST /api/scanner/upload
Content-Type: multipart/form-data

file: [binary data]
metadata: {
  "scanner_id": "scanner_001",
  "timestamp": 1640995200
}
```

### Server Discovery
```
GET /api/scanner/discovery
Response: {
  "server_name": "ASR Production Server",
  "version": "1.0.0",
  "capabilities": {
    "gl_accounts": 79,
    "payment_methods": 5,
    "billing_destinations": 4
  }
}
```

## Data Flow Architecture

### Document Processing Pipeline

1. **Scanner Client**:
   - User drags document into interface OR
   - Scanner hardware captures document OR
   - Batch folder processing detects new files

2. **Upload Queue** (Local):
   - Document stored in SQLite queue
   - Metadata extracted and validated
   - Upload attempted when server available

3. **Production Server** (Remote):
   - Document received and stored
   - OCR and text extraction performed
   - Claude AI analysis initiated

4. **Classification Engine**:
   - GL account classification (79 options)
   - Payment status detection (5 methods)
   - Routing decision (4 destinations)
   - Confidence scoring and validation

5. **Storage & Audit**:
   - Document filed in appropriate destination
   - Complete audit trail logged
   - Status update sent to scanner client

## Shared Components

### Core Data Models
Located in `shared/core/models.py`:

- **DocumentMetadata**: Universal document information
- **UploadResult**: Processing results and status
- **GLAccount**: GL account definitions and keywords
- **BillingDestination**: Routing destination configuration
- **ScannerInfo**: Scanner client identification

### API Schemas
Located in `shared/api/schemas.py`:

- Request/response models for all API endpoints
- Validation rules and data constraints
- Error response standardization

### Utility Functions
Located in `shared/utils/`:

- File validation and processing
- Cryptographic functions for security
- Network communication helpers
- Configuration management utilities

## Security Architecture

### Authentication
- API key-based authentication for scanner clients
- JWT tokens for session management
- Bearer token authentication for API requests

### Data Isolation
- Tenant-based data separation in database
- S3 folder-level isolation for document storage
- API-level tenant context validation

### Network Security
- HTTPS-only communication in production
- Request rate limiting and throttling
- Input validation and sanitization

## Scalability Design

### Horizontal Scaling
- Multiple scanner clients → Single production server
- Load balancer support for multiple server instances
- Database connection pooling and optimization

### Vertical Scaling
- Async processing for I/O operations
- Worker process scaling based on load
- Memory-efficient document processing

### Multi-Tenant Scaling
- Database schema isolation by tenant
- Storage backend abstraction (local/S3)
- Configurable resource limits per tenant

## Deployment Architectures

### Small Business (Single Server)
```
Scanner Clients (2-5) → Production Server (SQLite) → Local Storage
```

### Enterprise (Multi-Server)
```
Scanner Clients (10-50) → Load Balancer → Production Servers (N) → PostgreSQL → S3
```

### SaaS (Multi-Tenant)
```
Tenant A Scanners → API Gateway → Tenant-Isolated Services → Isolated Storage
Tenant B Scanners → API Gateway → Tenant-Isolated Services → Isolated Storage
```

## Technology Stack

### Production Server
- **Framework**: FastAPI (async Python web framework)
- **Database**: SQLAlchemy ORM with PostgreSQL/SQLite
- **AI Integration**: Anthropic Claude API
- **Document Processing**: PyPDF2, pdf2image, Pillow
- **Authentication**: JWT with passlib
- **Configuration**: Pydantic settings management

### Document Scanner
- **GUI Framework**: Tkinter (cross-platform desktop)
- **HTTP Client**: aiohttp for async API communication
- **Database**: aiosqlite for offline queue
- **File Processing**: pathlib, mimetypes
- **Configuration**: YAML-based configuration
- **Hardware**: TWAIN integration for scanner support

### Shared Infrastructure
- **Build System**: PyInstaller for executable distribution
- **Testing**: pytest with async support
- **Documentation**: Markdown with code examples
- **Version Control**: Git with conventional commits

## Performance Characteristics

### Production Server
- **Startup Time**: <30 seconds with database initialization
- **Document Processing**: <10 seconds average for typical invoice
- **Concurrent Uploads**: 50+ simultaneous scanner connections
- **Database Performance**: <100ms average query response

### Document Scanner
- **Application Startup**: <5 seconds GUI initialization
- **File Upload**: Progress tracking with retry logic
- **Offline Queue**: 1000+ documents without performance degradation
- **Memory Usage**: <100MB typical, <500MB with large batches

## Future Architecture Considerations

### Cloud Native Deployment
- Docker containerization for both applications
- Kubernetes orchestration for production server
- Cloud storage integration (AWS S3, Azure Blob)
- Managed database services (RDS, Cloud SQL)

### Advanced AI Integration
- Enhanced Claude Vision processing
- Custom ML model training for specialized documents
- Advanced fraud detection algorithms
- Automated quality assurance validation

### Enterprise Integration
- SSO authentication (LDAP, Active Directory)
- ERP system integration (SAP, Oracle)
- Advanced reporting and analytics
- API ecosystem for third-party integrations

---

This architecture provides the foundation for scalable, reliable document processing while maintaining the sophistication of the original monolithic system.
'''

        (docs_dir / "ARCHITECTURE.md").write_text(architecture_doc)

    def create_master_installer(self) -> None:
        """Create master installer for both applications"""
        logger.info("🎯 Creating master installer...")

        # Windows installer
        windows_installer = '''@echo off
echo ASR Invoice Archive System - Complete Installation
echo ================================================

echo.
echo This installer will set up both components:
echo 1. ASR Production Server (Enterprise processing)
echo 2. ASR Document Scanner (Desktop application)
echo.

pause

echo.
echo Installing ASR Production Server...
echo ----------------------------------
cd Production_Server
call install_production_server.bat
cd ..

echo.
echo Installing ASR Document Scanner...
echo ---------------------------------
cd Document_Scanner
call install_document_scanner.bat
cd ..

echo.
echo.
echo ================================================
echo ASR Invoice Archive System Installation Complete
echo ================================================
echo.
echo Next Steps:
echo 1. Configure Production Server:
echo    - Edit Production_Server\\.env with your settings
echo    - Start with: Production_Server\\start_server.py
echo.
echo 2. Configure Document Scanner:
echo    - Edit Document_Scanner\\config\\scanner_config.yaml
echo    - Start with: Document_Scanner\\start_scanner.bat
echo.
echo 3. Access Web Interface:
echo    - Production Server: http://localhost:8000
echo    - API Documentation: http://localhost:8000/docs
echo.
echo For detailed setup instructions, see Documentation\\README.md
echo.
pause
'''

        (self.output_dir / "install_complete.bat").write_text(windows_installer)

        # Unix installer
        unix_installer = '''#!/bin/bash

echo "ASR Invoice Archive System - Complete Installation"
echo "================================================"
echo
echo "This installer will set up both components:"
echo "1. ASR Production Server (Enterprise processing)"
echo "2. ASR Document Scanner (Desktop application)"
echo

read -p "Press Enter to continue..."

echo
echo "Installing ASR Production Server..."
echo "----------------------------------"
cd Production_Server
if [ -f "install_production_server.sh" ]; then
    chmod +x install_production_server.sh
    ./install_production_server.sh
else
    echo "Production server installer not found"
fi
cd ..

echo
echo "Installing ASR Document Scanner..."
echo "---------------------------------"
cd Document_Scanner
if [ -f "install_document_scanner.sh" ]; then
    chmod +x install_document_scanner.sh
    ./install_document_scanner.sh
else
    echo "Document scanner installer not found"
fi
cd ..

echo
echo
echo "================================================"
echo "ASR Invoice Archive System Installation Complete"
echo "================================================"
echo
echo "Next Steps:"
echo "1. Configure Production Server:"
echo "   - Edit Production_Server/.env with your settings"
echo "   - Start with: python Production_Server/start_server.py"
echo
echo "2. Configure Document Scanner:"
echo "   - Edit Document_Scanner/config/scanner_config.yaml"
echo "   - Start with: ./Document_Scanner/start_scanner.sh"
echo
echo "3. Access Web Interface:"
echo "   - Production Server: http://localhost:8000"
echo "   - API Documentation: http://localhost:8000/docs"
echo
echo "For detailed setup instructions, see Documentation/README.md"
echo

read -p "Press Enter to exit..."
'''

        installer_path = self.output_dir / "install_complete.sh"
        installer_path.write_text(unix_installer)
        os.chmod(installer_path, 0o755)

    def create_deployment_guide(self) -> None:
        """Create comprehensive deployment guide"""
        logger.info("📋 Creating deployment guide...")

        deployment_guide = '''# ASR System Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the ASR Invoice Archive System in various environments.

## Pre-Deployment Checklist

### System Requirements
- [ ] Python 3.8+ installed and accessible via command line
- [ ] Network connectivity between scanner clients and production server
- [ ] Database setup (PostgreSQL recommended, SQLite for development)
- [ ] Claude AI API key for document analysis
- [ ] Adequate storage space (20GB+ for production environments)

### Infrastructure Planning
- [ ] Identify production server host (dedicated server or cloud instance)
- [ ] Plan network topology for scanner client communication
- [ ] Configure firewall rules (default: port 8000 for HTTP API)
- [ ] Set up backup strategy for database and document storage
- [ ] Plan monitoring and alerting for production operations

## Deployment Scenarios

### Scenario 1: Small Business (Single Server)
**Use Case**: 2-10 users, moderate document volume, local network
**Architecture**: SQLite + Local Storage + Windows/Linux Server

#### Step 1: Production Server Setup
1. Copy `Production_Server/` to your server machine
2. Configure environment:
   ```bash
   cd Production_Server/config
   cp .env.template ../.env
   # Edit .env with your settings
   ```
3. Database configuration (SQLite):
   ```env
   DATABASE_URL=sqlite:///./asr_records.db
   ```
4. Start the server:
   ```bash
   python start_server.py
   ```
5. Verify at: http://your-server:8000/health

#### Step 2: Scanner Client Setup
1. Install on each workstation: run `Document_Scanner/start_scanner.bat`
2. Configure server connection in `config/scanner_config.yaml`:
   ```yaml
   production_servers:
     - name: "Main Server"
       url: "http://your-server:8000"
       enabled: true
   ```
3. Test document upload functionality

### Scenario 2: Enterprise (Multi-Server)
**Use Case**: 50+ users, high volume, multiple locations
**Architecture**: PostgreSQL + Load Balancer + Multiple Servers

#### Step 1: Database Setup
1. Install PostgreSQL server
2. Create database and user:
   ```sql
   CREATE DATABASE asr_records;
   CREATE USER asr_admin WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE asr_records TO asr_admin;
   ```

#### Step 2: Production Server Cluster
1. Deploy multiple server instances
2. Configure each server with shared database:
   ```env
   DATABASE_URL=postgresql://asr_admin:password@db-server:5432/asr_records
   ```
3. Set up load balancer (nginx, AWS ALB, etc.)
4. Configure health checks and monitoring

#### Step 3: Enterprise Scanner Deployment
1. Create MSI/package for mass deployment
2. Use Group Policy or deployment tools
3. Configure centrally via domain controller
4. Monitor and manage scanner fleet

### Scenario 3: Cloud Deployment (AWS/Azure)
**Use Case**: SaaS offering, multi-tenant, global scale
**Architecture**: Managed Database + Container Orchestration + Cloud Storage

#### AWS Deployment
1. **Database**: Amazon RDS PostgreSQL
2. **Compute**: ECS Fargate or EKS
3. **Storage**: S3 with bucket-level tenant isolation
4. **Load Balancing**: Application Load Balancer
5. **Monitoring**: CloudWatch + X-Ray
6. **Security**: VPC, IAM roles, encryption at rest/transit

#### Configuration Example:
```env
DATABASE_URL=postgresql://username:password@rds-endpoint:5432/asr_records
STORAGE_BACKEND=s3
S3_BUCKET=your-tenant-isolated-bucket
AWS_REGION=us-west-2
ANTHROPIC_API_KEY=your-claude-api-key
```

## Configuration Details

### Production Server Configuration (.env)
```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
# For SQLite: sqlite:///./asr_records.db

# Claude AI
ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4
RELOAD=false

# Security
JWT_SECRET_KEY=generate-256-bit-key-here
API_RATE_LIMIT=1000

# Storage
STORAGE_BACKEND=local
STORAGE_PATH=./storage
# For S3: STORAGE_BACKEND=s3, S3_BUCKET=your-bucket

# Features
ENABLE_CLAUDE_VISION=true
ENABLE_PAYMENT_DETECTION=true
ENABLE_ROUTING_AUDIT=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Scanner Configuration (scanner_config.yaml)
```yaml
production_servers:
  - name: "Primary Server"
    url: "https://your-server.com"
    api_key: "optional-api-key"
    enabled: true

scanner:
  auto_discovery: true
  retry_attempts: 3
  timeout_seconds: 30

upload_queue:
  max_pending_documents: 1000
  retry_interval_seconds: 60
  batch_size: 5
  auto_upload: true

ui:
  theme: "default"
  window_size: [1000, 700]
  show_preview: true
```

## Security Configuration

### Network Security
1. **HTTPS Only**: Use SSL certificates for production
2. **Firewall Rules**: Restrict API port access to scanner subnets
3. **VPN Access**: Consider VPN for remote scanners
4. **Rate Limiting**: Configure appropriate API rate limits

### Authentication & Authorization
1. **API Keys**: Generate unique keys for each scanner client
2. **JWT Tokens**: Configure secure token signing keys
3. **Database Access**: Use dedicated database users with minimal privileges
4. **File System**: Ensure proper file permissions for storage directories

### Data Protection
1. **Encryption at Rest**: Enable database and storage encryption
2. **Encryption in Transit**: HTTPS/TLS for all API communication
3. **Data Backup**: Automated backup with encryption
4. **Audit Logging**: Complete audit trail for compliance

## Performance Optimization

### Production Server Tuning
1. **Worker Processes**: Scale based on CPU cores (2 × cores)
2. **Database Connections**: Configure connection pooling
3. **Memory Management**: Monitor and adjust memory limits
4. **Caching**: Implement Redis caching for frequent queries

### Scanner Client Optimization
1. **Batch Size**: Adjust based on network capacity
2. **Compression**: Enable image compression for large files
3. **Queue Management**: Configure retention policies
4. **Hardware**: Optimize scanner settings for speed vs quality

## Monitoring & Maintenance

### Health Monitoring
1. **Server Health**: `/health` endpoint monitoring
2. **Database Performance**: Query time and connection monitoring
3. **Storage Utilization**: Disk space and I/O monitoring
4. **API Performance**: Response time and error rate tracking

### Log Management
1. **Centralized Logging**: Ship logs to centralized system
2. **Log Rotation**: Configure rotation and retention policies
3. **Error Alerting**: Set up alerts for critical errors
4. **Audit Trail**: Ensure complete audit log retention

### Backup Strategy
1. **Database Backups**: Daily automated backups with retention
2. **Document Storage**: Incremental backup of all documents
3. **Configuration Backup**: Version-controlled configuration
4. **Disaster Recovery**: Documented recovery procedures

## Troubleshooting Common Issues

### Production Server Issues

**Problem**: Server won't start
```bash
# Check Python version
python --version  # Should be 3.8+

# Check dependencies
pip install -r requirements.txt

# Check database connectivity
python -c "import sqlalchemy; print('SQLAlchemy OK')"

# Check configuration
python -c "from config.settings import settings; print(settings.DATABASE_URL)"
```

**Problem**: High memory usage
```bash
# Monitor memory usage
top -p $(pgrep -f ASR_Production_Server)

# Check database connections
# Reduce worker count in .env
WORKERS=2

# Enable memory profiling
ENABLE_MEMORY_PROFILING=true
```

### Scanner Client Issues

**Problem**: Can't connect to server
```yaml
# Test connectivity
curl http://your-server:8000/health

# Check configuration
production_servers:
  - name: "Test"
    url: "http://your-server:8000"  # Ensure correct URL
    enabled: true
```

**Problem**: Upload failures
```yaml
# Increase timeout
scanner:
  timeout_seconds: 60

# Reduce batch size
upload_queue:
  batch_size: 3

# Enable debug logging
logging:
  level: "DEBUG"
```

## Deployment Validation

### Pre-Production Testing
1. **Unit Tests**: Run test suite on target environment
2. **Integration Tests**: Verify scanner-server communication
3. **Load Testing**: Test with expected document volumes
4. **Security Testing**: Vulnerability assessment and penetration testing

### Production Validation
1. **Health Check**: Verify all components responding
2. **Document Upload**: Test end-to-end document processing
3. **Classification**: Verify GL account and payment detection accuracy
4. **Audit Trail**: Confirm complete audit logging
5. **Performance**: Validate response times within SLA

### Go-Live Checklist
- [ ] All servers deployed and health checks passing
- [ ] Scanner clients installed and configured
- [ ] Database properly initialized with schema
- [ ] SSL certificates installed and validated
- [ ] Monitoring and alerting active
- [ ] Backup and recovery procedures tested
- [ ] User training completed
- [ ] Support escalation procedures documented

## Support & Maintenance

### Regular Maintenance Tasks
- **Weekly**: Review error logs and performance metrics
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Review and update configuration
- **Annually**: Disaster recovery testing and security audit

### Support Resources
- System logs: `/var/log/asr/` or `C:\\ProgramData\\ASR\\logs\\`
- Configuration: `.env` and `scanner_config.yaml`
- Database: Connection and query performance tools
- API Documentation: `http://your-server:8000/docs`

### Professional Services
For complex deployments or custom requirements:
- Enterprise deployment consulting
- Performance optimization services
- Custom integration development
- 24/7 support and monitoring services

---

This deployment guide ensures successful installation and operation of the ASR Invoice Archive System across various environments and scales.
'''

        (self.output_dir / "Documentation" / "DEPLOYMENT_GUIDE.md").write_text(deployment_guide)

    def get_directory_size(self, path: Path) -> int:
        """Calculate directory size in bytes"""
        total_size = 0
        for file_path in path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size

    def run_validation_tests(self) -> bool:
        """Run validation tests on built distribution"""
        logger.info("🧪 Running validation tests...")
        start_time = time.time()

        try:
            # Test that executables exist
            server_exe = self.output_dir / "Production_Server" / "ASR_Production_Server"
            scanner_exe = self.output_dir / "Document_Scanner" / "ASR_Document_Scanner"
            server_exe_win = self.output_dir / "Production_Server" / "ASR_Production_Server.exe"
            scanner_exe_win = self.output_dir / "Document_Scanner" / "ASR_Document_Scanner.exe"

            executables_found = (
                server_exe.exists() or server_exe_win.exists()
            ) and (
                scanner_exe.exists() or scanner_exe_win.exists()
            )

            # Test that configuration files exist
            server_config = self.output_dir / "Production_Server" / "config" / ".env.template"
            scanner_config = self.output_dir / "Document_Scanner" / "config" / "scanner_config.yaml"

            configs_found = server_config.exists() and scanner_config.exists()

            # Test that documentation exists
            docs_found = (self.output_dir / "Documentation" / "README.md").exists()

            execution_time = time.time() - start_time

            validation_success = executables_found and configs_found and docs_found

            self.record_result(
                "validation_tests", validation_success, execution_time,
                "Distribution validation completed" if validation_success else "Validation failed",
                {
                    "executables_found": executables_found,
                    "configs_found": configs_found,
                    "docs_found": docs_found
                }
            )

            return validation_success

        except Exception as e:
            execution_time = time.time() - start_time
            self.record_result(
                "validation_tests", False, execution_time,
                f"Validation error: {e}"
            )
            return False

    def build_complete_distribution(self) -> bool:
        """Build complete ASR system distribution"""
        logger.info("🚀 Starting ASR Complete Distribution Build")
        logger.info("=" * 70)

        try:
            # Clean environment
            self.clean_build_environment()

            # Build both applications
            server_success = self.build_production_server()
            scanner_success = self.build_document_scanner()

            if not (server_success and scanner_success):
                logger.error("❌ Build failed - stopping distribution creation")
                return False

            # Create distribution package
            self.create_distribution_package()

            # Run validation tests
            validation_success = self.run_validation_tests()

            # Calculate overall success
            total_build_time = time.time() - self.build_start_time
            success_count = len([r for r in self.build_results if r.success])
            total_tests = len(self.build_results)
            success_rate = success_count / total_tests if total_tests > 0 else 0

            overall_success = success_rate >= 0.8 and validation_success

            # Print results
            self.print_build_report(total_build_time, overall_success)

            return overall_success

        except Exception as e:
            logger.error(f"❌ Distribution build failed: {e}")
            return False

    def print_build_report(self, total_build_time: float, overall_success: bool) -> None:
        """Print comprehensive build report"""
        logger.info("=" * 70)
        logger.info("📊 ASR DISTRIBUTION BUILD REPORT")
        logger.info("=" * 70)

        # Overall status
        status_icon = "✅" if overall_success else "❌"
        logger.info(f"{status_icon} Overall Build Status: {'SUCCESS' if overall_success else 'FAILED'}")
        logger.info(f"⏱️ Total Build Time: {total_build_time:.2f} seconds")

        # Component results
        logger.info(f"\n📋 BUILD COMPONENTS:")
        for result in self.build_results:
            status_icon = "✅" if result.success else "❌"
            logger.info(f"   {status_icon} {result.component}: {result.message} ({result.execution_time:.2f}s)")

        # Package information
        if self.output_dir.exists():
            package_size_mb = self.get_directory_size(self.output_dir) / (1024 * 1024)
            logger.info(f"\n📦 DISTRIBUTION PACKAGE:")
            logger.info(f"   📁 Location: {self.output_dir}")
            logger.info(f"   💾 Size: {package_size_mb:.1f} MB")
            logger.info(f"   📋 Contents:")
            logger.info(f"      • Production Server (Enterprise processing)")
            logger.info(f"      • Document Scanner (Desktop application)")
            logger.info(f"      • Complete documentation and guides")
            logger.info(f"      • Installation and startup scripts")

        # Next steps
        logger.info(f"\n💡 NEXT STEPS:")
        if overall_success:
            logger.info("   ✅ Distribution package built successfully")
            logger.info("   📋 Review deployment guide in Documentation/")
            logger.info("   🚀 Deploy to target environments")
            logger.info("   🧪 Run performance validation after deployment")
        else:
            logger.info("   ⚠️ Review build failures and resolve issues")
            logger.info("   🔧 Check system requirements and dependencies")
            logger.info("   🔄 Re-run build after addressing problems")

        logger.info("=" * 70)


def main():
    """Distribution build entry point"""
    print("🏗️ ASR System Complete Distribution Builder")
    print("Building production-ready package with both applications")
    print("=" * 70)

    builder = ASRDistributionBuilder()
    success = builder.build_complete_distribution()

    print("\n" + "=" * 70)
    if success:
        print("✅ ASR Distribution build completed successfully!")
        print(f"📦 Package location: {builder.output_dir}")
        print("🚀 Ready for deployment to production environments")
    else:
        print("❌ ASR Distribution build failed!")
        print("🔧 Please review the build report and resolve issues")

    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🔄 Distribution build interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Distribution build failed: {e}")
        sys.exit(1)