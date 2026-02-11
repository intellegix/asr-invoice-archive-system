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
# --- Backend (139 pytest tests) ---
python -m pytest asr-systems/tests/ -v                        # All 139 tests
python -m pytest asr-systems/tests/ -v --cov=production-server --cov=shared  # With coverage
python -m pytest asr-systems/tests/test_gl_account_service.py -v  # GL account tests only
python asr-systems/integration_test.py                        # Integration tests
python asr-systems/tests/load_test.py                         # Load tests (50+ concurrent)
python asr-systems/performance_validation.py                  # Performance benchmarks
python asr-systems/system_verification.py                     # Deployment readiness check

# --- Frontend (298 vitest tests) ---
cd asr-records-legacy/legacy-frontend
npm run test                                                  # All 298 tests
npx vitest run                                                # Single run (no watch)
npx tsc --noEmit                                              # TypeScript type check
```

### Backend Test Files (139 tests)

| File | Tests | Coverage |
|------|-------|----------|
| `test_api_endpoints.py` | 10 | FastAPI routes via TestClient |
| `test_audit_trail_service.py` | 5 | Audit trail persistence |
| `test_billing_router_service.py` | 12 | Routing logic + destinations |
| `test_document_processor_service.py` | 8 | Pipeline orchestration |
| `test_gl_account_service.py` | 6 | GL classification |
| `test_multi_tenant_isolation.py` | 9 | Storage/API/scanner tenant scoping |
| `test_payment_detection_service.py` | 13 | 5-method consensus |
| `test_rate_limit_middleware.py` | 16 | Sliding window, 429s, client ID extraction |
| `test_scanner_manager_service.py` | 8 | Scanner registration/heartbeat |
| `test_service_error_scenarios.py` | 22 | GL/payment/router/processor/storage edge cases |
| `test_storage_service.py` | 10 | Local CRUD + tenant isolation |
| `test_tenant_middleware.py` | 12 | Header extraction, fallback, response headers |

### Frontend Test Files (298 tests)

| Category | Files | Tests | Coverage |
|----------|-------|-------|----------|
| Zustand Stores | 3 | 69 | auth (14), documents (32), ui (23) |
| API Services | 5 | 51 | ApiClient (18), queryClient (7), documents (10), metrics (10), vendors (6) |
| Custom Hooks | 4 | 48 | useDashboard (12), useDocuments (16), useVendors (6), useFileUpload (14) |
| Components | 4 | 62 | Button (20), MetricCard (20), Header (9), Navigation (13) |
| Pages + App | 4 | 63 | Dashboard (18), Upload (18), Documents (20), App routing (7) |
| Infrastructure | 2 | — | renderWithProviders wrapper, mock data fixtures |

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
           └── ProductionStorageService (local filesystem / S3 via boto3)
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

**ECS uses Secrets Manager for API key**: The `backend-task-def.json` pulls `ANTHROPIC_API_KEY` from AWS Secrets Manager via `valueFrom`. The task role (`ecsTaskRole`) must have `secretsmanager:GetSecretValue` permission.

**Docker Compose requires JWT_SECRET_KEY**: `docker-compose.yml` uses `${JWT_SECRET_KEY:?...}` — the container will fail to start if this env var is not set.

**CORS restricted to localhost**: Production settings default CORS origins to `["http://localhost:3000", "http://localhost:5173"]`. Add your domain to `CORS_ALLOWED_ORIGINS` env var for other deployments.

**Default port differs by entry point**: `start_server.py` defaults to port 8080 (`API_PORT` env var). Docker Compose maps to 8000 internally.

## Required Environment Variables

```env
ANTHROPIC_API_KEY=sk-ant-...    # Required - Claude AI for document analysis
```

Key optional vars: `DEBUG` (false), `API_PORT` (8000), `DATABASE_URL` (sqlite default), `STORAGE_BACKEND` (local/s3), `MULTI_TENANT_ENABLED` (false), `JWT_SECRET_KEY` (required for Docker), `SCANNER_API_ENABLED` (true). Full list in `asr-systems/.env.example`.

## Dependencies

Install from `asr-systems/production-server/requirements.txt`. Core: FastAPI, uvicorn, anthropic, pydantic + pydantic-settings, SQLAlchemy, PyPDF2, pdfplumber, Pillow, structlog, python-jose, aiofiles, boto3. Dev: pytest, pytest-asyncio, pytest-cov, black, isort, mypy, bandit, pip-audit.

## CI Pipeline

CI runs on push/PR to `master` via `.github/workflows/ci.yml`:
- **Lint**: black, isort
- **Type check**: mypy (continue-on-error due to hyphenated directory)
- **Security**: bandit (advisory), pip-audit (advisory)
- **Tests**: pytest with coverage on Python 3.11 + 3.12 (139 tests)
- **Docker**: builds backend image after tests pass

## Deployment Status

| Option | Status | Commit |
|--------|--------|--------|
| Source Code | Working | — |
| Windows EXE | Working | `802008f` |
| Docker | Working | `a0d36e9` |
| AWS ECS | Working | `b351af7` |
| CI Pipeline | Green | `ff81cad` |
| System Review | Complete | `a35dfb5` |
| Full-Stack Tests | 437 tests | `8f6ad11` |
