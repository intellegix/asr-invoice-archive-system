# ASR Invoice Archive System - Deployment Guide

Enterprise document processing system with 79 GL accounts, 5-method payment detection, and 4 billing destinations.

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
# Edit .env - ANTHROPIC_API_KEY is required

# Start all services (backend + frontend with SQLite)
docker compose up -d

# View logs
docker compose logs -f
```

### Services

| Service | Port | Profile | Description |
|---------|------|---------|-------------|
| backend | 8000 | default | ASR Production Server API |
| frontend | 80 | default | React/Vite web interface (Nginx) |
| postgres | 5432 | `with-postgres` | PostgreSQL database (optional) |
| redis | 6379 | `with-redis` | Redis cache (optional) |

### Commands

```bash
# Start default services (backend + frontend)
docker compose up -d

# Start with PostgreSQL
docker compose --profile with-postgres up -d

# Start with Redis cache
docker compose --profile with-redis up -d

# Full stack (all services)
docker compose --profile with-postgres --profile with-redis up -d

# Stop services
docker compose down

# View logs
docker compose logs -f backend

# Rebuild after code changes
docker compose build --no-cache
docker compose up -d
```

### Building Images Manually

```bash
# Build backend image (from asr-systems directory)
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

### AWS Infrastructure

| Resource | Value |
|----------|-------|
| **Region** | us-west-2 |
| **Cluster** | asr-records-legacy-cluster-dev |
| **ALB URL** | http://asr-records-alb-757932068.us-west-2.elb.amazonaws.com |
| **Backend ECR** | 206362095382.dkr.ecr.us-west-2.amazonaws.com/asr-records-backend-dev |
| **Frontend ECR** | 206362095382.dkr.ecr.us-west-2.amazonaws.com/asr-records-frontend-dev |
| **Backend Task** | asr-records-backend-working (512 CPU / 1024 MB) |
| **Frontend Task** | asr-records-frontend-working (256 CPU / 512 MB) |
| **Log Groups** | /ecs/asr-records-legacy-backend-dev, /ecs/asr-records-legacy-frontend-dev |

### Building and Pushing Images

```bash
# Login to ECR
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin 206362095382.dkr.ecr.us-west-2.amazonaws.com

# Build and push backend (from asr-systems directory)
docker build -f production-server/Dockerfile -t asr-records-backend .
docker tag asr-records-backend:latest 206362095382.dkr.ecr.us-west-2.amazonaws.com/asr-records-backend-dev:latest
docker push 206362095382.dkr.ecr.us-west-2.amazonaws.com/asr-records-backend-dev:latest

# Build and push frontend
docker build -t asr-records-frontend ../asr-records-legacy/legacy-frontend/
docker tag asr-records-frontend:latest 206362095382.dkr.ecr.us-west-2.amazonaws.com/asr-records-frontend-dev:latest
docker push 206362095382.dkr.ecr.us-west-2.amazonaws.com/asr-records-frontend-dev:latest
```

### Update ECS Services

```bash
# Force new deployment after pushing images
aws ecs update-service --cluster asr-records-legacy-cluster-dev \
  --service asr-records-backend-service --force-new-deployment --region us-west-2

aws ecs update-service --cluster asr-records-legacy-cluster-dev \
  --service asr-records-frontend-service --force-new-deployment --region us-west-2
```

### ECS Environment Variables

The `ANTHROPIC_API_KEY` must be set in the task definition environment. If missing, the backend container will crash on startup. Update the task definition JSON and re-register:

```bash
# Register updated task definition
aws ecs register-task-definition --cli-input-json file://backend-task-def.json --region us-west-2

# Update service to use new task definition
aws ecs update-service --cluster asr-records-legacy-cluster-dev \
  --service asr-records-backend-service \
  --task-definition asr-records-backend-working --region us-west-2
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

### Health Check from Git Bash (Windows)

Git Bash on Windows converts paths starting with `/` to Windows paths. Use a double-slash to prevent this:

```bash
# This will fail in Git Bash (converts /health to C:/Program Files/Git/health)
curl http://localhost:8000/health

# This works in Git Bash
curl http://localhost:8000//health
```

### Swagger Docs Not Available

Swagger UI (`/docs`) and ReDoc (`/redoc`) are only available when `DEBUG=true`. In production (`DEBUG=false`), these endpoints are disabled for security.

### ECS Container Keeps Crashing

If the backend container enters a crash loop on ECS, check:

1. **Missing ANTHROPIC_API_KEY**: The server will crash on startup if this env var is empty or missing in the task definition. Update `backend-task-def.json` with your actual key and re-register the task definition.

2. **Check CloudWatch logs**:
   ```bash
   aws logs tail /ecs/asr-records-legacy-backend-dev --follow --region us-west-2
   ```

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

- Swagger UI: http://localhost:8000/docs (requires `DEBUG=true`)
- ReDoc: http://localhost:8000/redoc (requires `DEBUG=true`)
- AWS: http://asr-records-alb-757932068.us-west-2.elb.amazonaws.com/health

---

## System Capabilities

- **79 QuickBooks GL Accounts** - Automated classification
- **5-Method Payment Detection** - Claude AI, Regex, Keywords, Amount, OCR
- **4 Billing Destinations** - Open/Closed Payable/Receivable routing
- **Multi-Tenant Architecture** - Document isolation per tenant
- **Scanner Client API** - Distributed document processing
- **Complete Audit Trail** - Confidence scoring and routing history

---

*ASR Invoice Archive System - Enterprise Document Processing*
*Version 2.0.0*
