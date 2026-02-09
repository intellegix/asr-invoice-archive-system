# ASR Invoice Archive System - Deployment Guide

Enterprise document processing system with 69 GL accounts, 5-method payment detection, and 4 billing destinations.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Deployment Options](#deployment-options)
3. [Source Code Deployment](#source-code-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Windows Executable Deployment](#windows-executable-deployment)
6. [AWS Cloud Deployment](#aws-cloud-deployment)
7. [Environment Variables](#environment-variables)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Fastest Way to Get Running (Source Code)

```bash
# 1. Navigate to asr-systems directory
cd asr-systems

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r production-server/requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# 5. Start the server
python start_server.py
```

Server will be available at: http://localhost:8080

---

## Deployment Options

| Option | Best For | Complexity | Scale |
|--------|----------|------------|-------|
| Source Code | Development, Testing | Low | Single instance |
| Docker | Production, Teams | Medium | Horizontal scaling |
| Windows EXE | Standalone workstations | Low | Single instance |
| AWS ECS | Enterprise, Cloud | High | Auto-scaling |

---

## Source Code Deployment

### Prerequisites
- Python 3.11+
- pip package manager

### Installation

```bash
# Clone or download the repository
cd asr-systems

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r production-server/requirements.txt

# Configure environment
copy .env.example .env
```

### Configuration

Edit `.env` file:

```env
# Required
ANTHROPIC_API_KEY=your-api-key-here

# Optional
DEBUG=false
API_PORT=8000
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./asr_records.db
```

### Running

```bash
# Using start script
python start_server.py

# Or directly with uvicorn
uvicorn production-server.api.main:app --host 0.0.0.0 --port 8000
```

### Verification

```bash
# Health check
curl http://localhost:8000/health

# GL Accounts
curl http://localhost:8000/api/v1/gl-accounts

# API Documentation
# Open in browser: http://localhost:8000/docs
```

---

## Docker Deployment

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Quick Start

```bash
cd asr-systems

# Copy and configure environment
copy .env.example .env
# Edit .env with your settings

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| backend | 8000 | ASR Production Server API |
| frontend | 80 | React web interface |
| postgres | 5432 | PostgreSQL database |
| redis | 6379 | Cache (optional) |

### Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f backend

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d

# Scale backend (if needed)
docker-compose up -d --scale backend=3

# Start with Redis cache
docker-compose --profile with-redis up -d
```

### Building Images Manually

```bash
# Build backend image
docker build -f production-server/Dockerfile -t asr-backend:latest .

# Build frontend image
docker build -t asr-frontend:latest ../asr-records-legacy/legacy-frontend/
```

---

## Windows Executable Deployment

### Prerequisites
- Windows 10/11
- No Python installation required (self-contained)

### Building Executables

```bash
cd asr-systems

# Build Production Server EXE
python build_production_server.py

# Build Document Scanner EXE
python build_document_scanner.py

# Or build all
python build_distribution.py
```

### Running

```bash
# Navigate to distribution
cd dist/ASR_Production_Server

# Configure
copy config\.env.template .env
# Edit .env with your settings

# Run
ASR_Production_Server.exe
```

### Startup Scripts

```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

---

## AWS Cloud Deployment

### Prerequisites
- AWS CLI configured
- Terraform 1.6+
- Docker (for building images)

### Infrastructure Setup

```bash
cd asr-records-legacy/aws-deployment/infrastructure/terraform

# Initialize Terraform
terraform init

# Review plan
terraform plan -var-file=environments/prod/prod.tfvars

# Deploy
terraform apply -var-file=environments/prod/prod.tfvars
```

### Building and Pushing Images

```bash
# Login to ECR
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin <account>.dkr.ecr.us-west-2.amazonaws.com

# Build and push backend
docker build -f production-server/Dockerfile -t asr-records-backend .
docker tag asr-records-backend:latest <account>.dkr.ecr.us-west-2.amazonaws.com/asr-records-backend:latest
docker push <account>.dkr.ecr.us-west-2.amazonaws.com/asr-records-backend:latest

# Build and push frontend
docker build -t asr-records-frontend ../asr-records-legacy/legacy-frontend/
docker tag asr-records-frontend:latest <account>.dkr.ecr.us-west-2.amazonaws.com/asr-records-frontend:latest
docker push <account>.dkr.ecr.us-west-2.amazonaws.com/asr-records-frontend:latest
```

### Secrets Configuration

Store secrets in AWS Secrets Manager or SSM Parameter Store:

```bash
# Store API key
aws ssm put-parameter \
  --name "/asr-records/prod/anthropic-api-key" \
  --value "your-api-key" \
  --type SecureString

# Store database password
aws ssm put-parameter \
  --name "/asr-records/prod/database-password" \
  --value "your-password" \
  --type SecureString
```

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| ANTHROPIC_API_KEY | Claude AI API key | sk-ant-... |

### Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| DEBUG | false | Enable debug mode |
| API_PORT | 8000 | API server port |
| API_HOST | 0.0.0.0 | API bind address |
| LOG_LEVEL | INFO | Logging level |
| API_WORKERS | 4 | Number of worker processes |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | sqlite:///./asr_records.db | Database connection string |
| DB_POOL_SIZE | 10 | Connection pool size |

### Storage

| Variable | Default | Description |
|----------|---------|-------------|
| STORAGE_BACKEND | local | Storage backend (local/s3) |
| DATA_DIR | ./data | Local data directory |
| S3_BUCKET_NAME | - | S3 bucket for documents |

### Security

| Variable | Default | Description |
|----------|---------|-------------|
| JWT_SECRET_KEY | - | JWT signing key (32+ chars) |
| API_RATE_LIMIT | 1000 | Requests per minute |

### Multi-Tenant

| Variable | Default | Description |
|----------|---------|-------------|
| MULTI_TENANT_ENABLED | false | Enable multi-tenancy |
| DEFAULT_TENANT_ID | default | Default tenant ID |

### Scanner API

| Variable | Default | Description |
|----------|---------|-------------|
| SCANNER_API_ENABLED | true | Enable scanner API |
| MAX_SCANNER_CLIENTS | 10 | Max concurrent scanners |

---

## Troubleshooting

### Server Won't Start

1. **Check Python version**: Requires Python 3.11+
   ```bash
   python --version
   ```

2. **Check dependencies**:
   ```bash
   pip install -r production-server/requirements.txt
   ```

3. **Check environment**:
   ```bash
   # Ensure .env file exists
   ls -la .env
   ```

### ModuleNotFoundError: encodings

This occurs with PyInstaller builds. Solution:
- Rebuild EXE with updated spec file (includes encodings collection)
- Run `python build_production_server.py`

### Pydantic Validation Error

This occurs with older EXE builds. Solution:
- Rebuild EXE with updated spec file (includes pydantic_core)
- Run `python build_document_scanner.py`

### Docker Build Fails

1. **Context issues**:
   ```bash
   # Build from asr-systems directory
   cd asr-systems
   docker build -f production-server/Dockerfile -t asr-backend .
   ```

2. **Memory issues**:
   ```bash
   # Increase Docker memory limit in Docker Desktop settings
   ```

### API Returns 500 Error

1. **Check logs**:
   ```bash
   docker-compose logs backend
   # or
   cat asr_production_server.log
   ```

2. **Check Claude API key**:
   ```bash
   # Ensure ANTHROPIC_API_KEY is set
   echo $ANTHROPIC_API_KEY
   ```

### Database Connection Failed

1. **SQLite**: Ensure data directory is writable
2. **PostgreSQL**: Check connection string and credentials
   ```bash
   psql $DATABASE_URL -c "SELECT 1"
   ```

### Scanner Can't Connect

1. **Check Scanner API is enabled**:
   ```bash
   curl http://localhost:8000/api/v1/scanner/status
   ```

2. **Check firewall**: Ensure port 8000 is open

3. **Check scanner config**: Verify server URL in scanner_config.yaml

---

## Support

### Health Endpoints

```bash
# Server health
curl http://localhost:8000/health

# Detailed status
curl http://localhost:8000/api/status

# GL accounts count
curl http://localhost:8000/api/v1/gl-accounts | jq '. | length'
```

### Log Files

- Server logs: `asr_production_server.log`
- Docker logs: `docker-compose logs backend`

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## System Capabilities

- **69 QuickBooks GL Accounts** - Automated classification
- **5-Method Payment Detection** - Claude AI, Regex, Keywords, Amount, OCR
- **4 Billing Destinations** - Open/Closed Payable/Receivable routing
- **Multi-Tenant Architecture** - Document isolation per tenant
- **Scanner Client API** - Distributed document processing
- **Complete Audit Trail** - Confidence scoring and routing history

---

*ASR Invoice Archive System - Enterprise Document Processing*
*Version 1.0.0*
