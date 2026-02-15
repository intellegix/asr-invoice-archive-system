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
# --- Backend (675 pytest tests) ---
python -m pytest asr-systems/tests/ -v                        # All tests
python -m pytest asr-systems/tests/ -v --cov=production_server --cov=shared  # With coverage
python -m pytest asr-systems/tests/test_gl_account_service.py -v  # Single file
python -m pytest asr-systems/tests/test_vendor_service.py::TestVendorCRUD -v  # Single class
python -m pytest asr-systems/tests/test_vendor_service.py::TestVendorCRUD::test_create -v  # Single test
python asr-systems/integration_test.py                        # Integration tests
python asr-systems/tests/load_test.py                         # Load tests (50+ concurrent)

# --- Frontend (493 vitest tests) ---
cd asr-records-legacy/legacy-frontend
npm run test                                                  # All tests (watch mode)
npx vitest run                                                # Single run (no watch)
npx vitest run src/components/Header                          # Single component
npx tsc --noEmit                                              # TypeScript type check

# --- E2E / Playwright (99 tests) ---
# Requires backend (port 8000) + frontend (port 3000) running
cd asr-records-legacy/legacy-frontend
npm run test:e2e                                              # All 99 Playwright tests
npm run test:e2e:headed                                       # With visible browser
npm run test:e2e:report                                       # View HTML report

# --- Linting & Formatting ---
python -m black asr-systems/production_server/ asr-systems/tests/   # Format Python
python -m isort asr-systems/production_server/ asr-systems/tests/   # Sort imports
python -m mypy asr-systems/production_server/                       # Type check (blocking in CI)
python -m bandit -r asr-systems/production_server/ -ll              # Security scan
```

## Architecture

### Request Flow

```
Client → FastAPI (api/main.py)
       → PrometheusMiddleware (HTTP metrics, path normalization)
       → TenantMiddleware (X-Tenant-ID header / JWT)
       → RequestLoggingMiddleware (correlation IDs, structlog)
       → RateLimitMiddleware (sliding window, 100 req/min default)
       → HTTPBearer auth
       → DocumentProcessorService (orchestrator)
           ├── GLAccountService (79 QB accounts, DB-backed, keyword-indexed)
           ├── PaymentDetectionService (5-method consensus: Claude Vision,
           │     Claude Text, Regex, Keywords, Amount Analysis)
           ├── BillingRouterService (4 destinations: open/closed × payable/receivable)
           └── ProductionStorageService (local filesystem / S3 via boto3)
       → Audit trail logged with confidence scores
       → Prometheus business metrics recorded
```

### Key Directories

- `asr-systems/production_server/` — Main FastAPI app
  - `api/main.py` — FastAPI app with lifespan manager, all route definitions (~1650 lines)
  - `config/production_settings.py` — Pydantic BaseSettings (env-driven, ~480 lines)
  - `config/database.py` — SQLAlchemy async engine, session factory, connectivity check
  - `services/` — 9 core services (gl_account, payment_detection, billing_router, document_processor, storage, scanner_manager, vendor, vendor_import_export, metrics)
  - `middleware/` — tenant, rate_limit, request_logging, metrics (Prometheus)
  - `models/` — SQLAlchemy ORM models (vendor.py, gl_account.py, audit_trail.py)
  - `utils/` — retry.py (async retry + circuit breaker patterns)
- `asr-systems/shared/` — Shared models used by all components
  - `core/constants.py` — GL_ACCOUNTS dict (79 accounts), PAYMENT_INDICATORS
  - `core/models.py` — Pydantic data models
  - `api/schemas.py` — Request/response schemas
- `asr-systems/document-scanner/` — Desktop scanner client (Tkinter GUI, SQLite offline queue)
- `asr-records-legacy/legacy-frontend/` — React/Vite frontend served by Nginx

### Multi-Tenant Isolation Model

The system uses a **dual-scoping model** for tenant isolation:

- **Vendor CRUD** is tenant-scoped: `get_vendor()`, `update_vendor()`, `delete_vendor()`, `get_vendor_stats()` all accept `tenant_id` and add `.where(VendorRecord.tenant_id == tenant_id)`. API endpoints pass `user.get("tenant_id")` from auth context.
- **GL Account classification is global**: All tenants share the 79 seeded accounts (tenant_id="default") for invoice classification. But **GL CRUD is tenant-owned**: `update/delete_gl_account()` return a `"__FORBIDDEN__"` sentinel when a tenant tries to modify another tenant's account. The API layer maps this to HTTP 403.
- **`list_gl_accounts_from_db()`** uses `sqlalchemy.or_()` to return global ("default") + the calling tenant's own accounts.
- **`create_gl_account`** always overrides the schema's `tenant_id` with the authenticated user's tenant — never trust client-supplied tenant.

### Prometheus Metrics

- `middleware/metrics_middleware.py` — HTTP Counter/Histogram/Gauge with path normalization (`/vendors/abc123` → `/vendors/{id}`)
- `services/metrics_service.py` — Business metrics (documents, GL, payments, vendors)
- `/metrics` endpoint gated by `METRICS_ENABLED` setting (default: False)
- Both modules use `_get_or_create()` guard (originally needed for dual-import, kept as defense-in-depth after P88 rename)

### Important Gotchas

**Directory renamed (P88)**: `production-server/` was renamed to `production_server/` to fix the dual-import bug. The `importlib` hack in `start_server.py` and `main_server.py` is no longer needed for this reason. Prometheus `_get_or_create()` guards are kept as defense-in-depth.

**Route order matters for FastAPI**: Static routes (`/vendors/export`) MUST be defined before path param routes (`/vendors/{vendor_id}`), or FastAPI matches "export" as a vendor_id. The export route is intentionally placed before the `{vendor_id}` route in api/main.py.

**GL accounts are DB-backed**: 79 QB accounts are seeded by Alembic migration 0004 from `shared/core/constants.py`. `GLAccountService.initialize()` loads from DB first, falls back to constants. Vendor→GL classification is DB-only: `GLAccountService._classify_by_vendor()` queries VendorService for `default_gl_account` (seeded by Alembic migration 0003).

**`_shutting_down` global in api/main.py**: The lifespan function resets `_shutting_down = False` at startup. This is critical for TestClient reuse across test classes — without it, the `/health/ready` endpoint returns 503.

**`vendor_import_export_service` must be in globals**: All module-level service variables used inside the lifespan function must be listed in the `global` declaration, or they remain local and the module-level var stays `None`.

**Payment consensus is mean confidence, not majority vote**: `PaymentDetectionService` averages confidence scores across enabled methods.

**Swagger docs require DEBUG=true**: `/docs` and `/redoc` are disabled when `DEBUG=false` (production default).

**asyncpg rejects timezone-aware datetimes**: ORM model defaults use `datetime.now(timezone.utc).replace(tzinfo=None)` to produce naive UTC datetimes. asyncpg strictly enforces `TIMESTAMP WITHOUT TIME ZONE` — do NOT use `datetime.now(timezone.utc)` directly for DB columns.

**Audit trail schema aligned (P91)**: Migration 0006 aligns the `audit_trail` table columns with the ORM model on PostgreSQL (renames entity_id→document_id, created_at→timestamp, adds event_data/system_component, drops legacy columns). SQLite is a no-op since `create_all()` already uses correct ORM columns. 6 Alembic migrations total.

**Git Bash path mangling**: On Windows, Git Bash converts `/health` to a Windows path. Use double-slash: `curl http://localhost:8000//health`.

**Docker Compose requires JWT_SECRET_KEY**: `docker-compose.yml` uses `${JWT_SECRET_KEY:?...}` — the container will fail to start without it.

**Default port differs by entry point**: `start_server.py` defaults to 8080 (`API_PORT`). Docker Compose maps to 8000.

## Required Environment Variables

```env
ANTHROPIC_API_KEY=sk-ant-...    # Required - Claude AI for document analysis
```

Key optional vars: `DEBUG` (false), `API_PORT` (8000), `DATABASE_URL` (sqlite default), `STORAGE_BACKEND` (local/s3), `MULTI_TENANT_ENABLED` (false), `JWT_SECRET_KEY` (required for Docker), `SCANNER_API_ENABLED` (true), `LOG_FORMAT` (text/json), `METRICS_ENABLED` (false), `METRICS_PATH` (/metrics), `REQUIRE_POSTGRESQL` (false), `ENABLE_DOCS` (false). Full list in `asr-systems/.env.example`.

## Dependencies

Install from `asr-systems/production_server/requirements.txt`. Core: FastAPI, uvicorn, anthropic, pydantic + pydantic-settings, SQLAlchemy, PyPDF2, pdfplumber, Pillow, structlog, python-jose, aiofiles, boto3, prometheus-client. Dev: pytest, pytest-asyncio, pytest-cov, black, isort, mypy, bandit, pip-audit.

## CI Pipeline

CI runs on push/PR to `master` via `.github/workflows/ci.yml`:
- **Backend tests** (`test` job): black, isort, mypy (blocking), bandit (blocks on medium+), pip-audit (blocking), pytest with coverage >= 72% on Python 3.11 + 3.12
- **PostgreSQL tests** (`test-pg` job, **required**): migrations, DB health, tenant isolation against PostgreSQL 15 (110 pass, 2 skipped)
- **Frontend tests** (`frontend-test` job): TypeScript type check (`tsc --noEmit`), vitest on Node 18
- **Docker**: builds backend + frontend images, backend smoke test (`/health/live`), after all test jobs pass (including test-pg)

Deploy pipeline (`.github/workflows/deploy.yml`) triggers on push to `master` after CI passes:
- Builds + pushes backend/frontend images to ECR
- Updates ECS services (`backend-service`, `frontend-service`) with new task definitions
- Task-def validation (no duplicate env vars, secrets check, Alembic chain linearity)
- Post-deploy health checks + smoke tests (readiness, GL accounts=79, API status)

## Operational Runbook (AWS ECS)

```bash
# CloudWatch logs
aws logs tail /ecs/asr-records-legacy-backend-dev --follow --region us-west-2

# Manual deployment
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 206362095382.dkr.ecr.us-west-2.amazonaws.com
docker build -f production_server/Dockerfile -t 206362095382.dkr.ecr.us-west-2.amazonaws.com/asr-records-backend-dev:latest .
docker push 206362095382.dkr.ecr.us-west-2.amazonaws.com/asr-records-backend-dev:latest
aws ecs register-task-definition --cli-input-json file://backend-task-def.json --region us-west-2
aws ecs update-service --cluster asr-records-legacy-cluster-dev --service backend-service --force-new-deployment --region us-west-2

# Health checks via ALB
curl http://asr-records-alb-757932068.us-west-2.elb.amazonaws.com/health/live
curl http://asr-records-alb-757932068.us-west-2.elb.amazonaws.com/health/ready

# ECS Exec (interactive shell)
aws ecs execute-command --cluster asr-records-legacy-cluster-dev --task <TASK_ID> --container backend --interactive --command "/bin/sh" --region us-west-2
```
