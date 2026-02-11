# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ASR Invoice Archive System — a FastAPI-based enterprise document processing server (v2.0.0) that classifies invoices into 79 QuickBooks GL accounts using 5-method payment detection and routes them to 4 billing destinations. Includes a distributed document scanner client and a React/Vite legacy frontend.

## Build & Run Commands

```bash
# --- Source Code (from asr-systems/) ---
python start_server.py                    # Start server (port 8080 by default)
bash start.sh                             # Linux/Mac with venv auto-setup
start.bat                                 # Windows with venv auto-setup

# --- Docker (from asr-systems/) ---
docker compose up -d                      # Backend + frontend (SQLite)
docker compose --profile with-postgres up -d   # With PostgreSQL
docker compose --profile with-redis up -d      # With Redis cache
docker compose logs -f backend            # View backend logs

# --- Windows EXE ---
python build_production_server.py         # Build → dist/ASR_Production_Server/
python build_document_scanner.py          # Build scanner → dist/ASR_Document_Scanner/

# --- AWS ECS (us-west-2) ---
# ECR repos: 206362095382.dkr.ecr.us-west-2.amazonaws.com/asr-records-{backend,frontend}-dev
# ALB: http://asr-records-alb-757932068.us-west-2.elb.amazonaws.com
# Cluster: asr-records-legacy-cluster-dev
```

## Testing

```bash
python -m pytest asr-systems/tests/ -v                        # All tests
python -m pytest asr-systems/tests/test_gl_account_service.py -v  # GL account tests only
python asr-systems/integration_test.py                        # Integration tests
python asr-systems/tests/load_test.py                         # Load tests (50+ concurrent)
python asr-systems/performance_validation.py                  # Performance benchmarks
python asr-systems/system_verification.py                     # Deployment readiness check
```

## Architecture

### Request Flow

```
Client → FastAPI (api/main.py)
       → TenantMiddleware (X-Tenant-ID header / JWT)
       → RateLimitMiddleware (slowapi, 100 req/min default)
       → HTTPBearer auth
       → DocumentProcessorService (orchestrator)
           ├── GLAccountService (79 QB accounts, keyword-indexed, in-memory)
           ├── PaymentDetectionService (5-method consensus: Claude Vision,
           │     Claude Text, Regex, Keywords, Amount Analysis)
           ├── BillingRouterService (4 destinations: open/closed × payable/receivable)
           └── ProductionStorageService (local / S3 / Render disk)
       → Audit trail logged with confidence scores
```

### Key Directories

- `asr-systems/production-server/` — Main FastAPI app
  - `api/main.py` — FastAPI app with lifespan manager, all route definitions
  - `config/production_settings.py` — Pydantic BaseSettings (env-driven)
  - `services/` — 6 core services (gl_account, payment_detection, billing_router, document_processor, storage, scanner_manager)
  - `middleware/` — tenant_middleware.py, rate_limit_middleware.py
- `asr-systems/shared/` — Shared models used by all components
  - `core/constants.py` — GL_ACCOUNTS dict (79 accounts), PAYMENT_INDICATORS
  - `core/models.py` — Pydantic data models
  - `api/schemas.py` — Request/response schemas
- `asr-systems/document-scanner/` — Desktop scanner client (Tkinter GUI, SQLite offline queue)
- `asr-records-legacy/legacy-frontend/` — React/Vite frontend served by Nginx

### Important Gotchas

**Hyphenated directory imports**: `production-server/` and `document-scanner/` use hyphens but Python needs underscores. `start_server.py` and `main_server.py` handle this via `importlib.util.spec_from_file_location()` to register modules as `production_server.*`. Never try to `import production-server` directly.

**GL accounts are static constants**: The 79 QB accounts live in `shared/core/constants.py` as an in-memory dict indexed by keyword. No database lookup. To add accounts, edit that dict.

**Payment consensus is mean confidence, not majority vote**: `PaymentDetectionService` averages confidence scores across enabled methods. Method order and thresholds matter.

**Swagger docs require DEBUG=true**: `/docs` and `/redoc` endpoints are disabled when `DEBUG=false` (production default).

**Git Bash path mangling**: On Windows, Git Bash converts `/health` to a Windows path. Use double-slash: `curl http://localhost:8000//health`.

**ECS crash if no API key**: The backend container crash-loops on AWS ECS if `ANTHROPIC_API_KEY` is empty/missing in the task definition.

**Default port differs by entry point**: `start_server.py` defaults to port 8080 (`API_PORT` env var). Docker Compose maps to 8000 internally.

## Required Environment Variables

```env
ANTHROPIC_API_KEY=sk-ant-...    # Required - Claude AI for document analysis
```

Key optional vars: `DEBUG` (false), `API_PORT` (8000), `DATABASE_URL` (sqlite default), `STORAGE_BACKEND` (local/s3/render_disk), `MULTI_TENANT_ENABLED` (false), `JWT_SECRET_KEY`, `SCANNER_API_ENABLED` (true). Full list in `asr-systems/.env.example`.

## Dependencies

Install from `asr-systems/production-server/requirements.txt`. Core: FastAPI, uvicorn, anthropic, pydantic + pydantic-settings, SQLAlchemy, PyPDF2, pdfplumber, Pillow, structlog, python-jose. Dev: pytest, pytest-asyncio, black, isort, mypy.

## Deployment Status

| Option | Status | Commit |
|--------|--------|--------|
| Source Code | Working | — |
| Windows EXE | Working | `802008f` |
| Docker | Working | `a0d36e9` |
| AWS ECS | Working | `b351af7` |
| Docs Update | Working | `d2a5115` |
