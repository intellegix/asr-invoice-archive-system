"""
ASR Production Server - FastAPI Application
Enterprise document processing server with sophisticated capabilities
• 79 QuickBooks GL Accounts with keyword matching
• 5-Method Payment Detection with consensus scoring
• 4 Billing Destination routing with audit trails
• Multi-tenant document isolation
• Scanner client API for distributed processing
"""

import asyncio
import collections
import logging
import os

# Import shared components
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from shared.api.schemas import (
    APIErrorResponseSchema,
    APISuccessResponseSchema,
    AuditLogEntrySchema,
    AuditLogListResponseSchema,
    AuthLoginRequestSchema,
    AuthLoginResponseSchema,
    AuthMeResponseSchema,
    ClassificationResponseSchema,
    DeleteDocumentResponseSchema,
    DocumentUploadResponseSchema,
    GLAccountCreateRequestSchema,
    GLAccountUpdateRequestSchema,
    ScannerHeartbeatSchema,
    ScannerRegistrationSchema,
    SettingsResponseSchema,
    SystemHealthResponseSchema,
    VendorCreateRequestSchema,
    VendorImportRequestSchema,
    VendorImportResultSchema,
    VendorUpdateRequestSchema,
    validate_document_id,
)
from shared.core.exceptions import (
    ASRException,
    AuthenticationError,
    DocumentError,
    ValidationError,
    handle_exception,
)
from shared.core.models import (
    BillingDestination,
    DocumentMetadata,
    PaymentConsensusResult,
    PaymentStatus,
    ProcessingStatus,
    SystemHealth,
    SystemType,
)

# Import production server components (with fallbacks for PyInstaller EXE context)
# Add production-server directory to path for absolute import fallbacks
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from ..config.production_settings import production_settings
except (ImportError, SystemError):
    from config.production_settings import production_settings

try:
    from ..services.gl_account_service import GLAccountService
except (ImportError, SystemError):
    from services.gl_account_service import GLAccountService

try:
    from ..services.payment_detection_service import PaymentDetectionService
except (ImportError, SystemError):
    from services.payment_detection_service import PaymentDetectionService

try:
    from ..services.billing_router_service import BillingRouterService
except (ImportError, SystemError):
    from services.billing_router_service import BillingRouterService

try:
    from ..services.document_processor_service import DocumentProcessorService
except (ImportError, SystemError):
    from services.document_processor_service import DocumentProcessorService

try:
    from ..services.storage_service import ProductionStorageService
except (ImportError, SystemError):
    from services.storage_service import ProductionStorageService

try:
    from ..services.scanner_manager_service import (
        ScannerManagerService,
        ScannerUploadRequest,
    )
except (ImportError, SystemError):
    from services.scanner_manager_service import (
        ScannerManagerService,
        ScannerUploadRequest,
    )

try:
    from ..middleware.tenant_middleware import TenantMiddleware
except (ImportError, SystemError):
    from middleware.tenant_middleware import TenantMiddleware

try:
    from ..middleware.rate_limit_middleware import RateLimitMiddleware
except (ImportError, SystemError):
    from middleware.rate_limit_middleware import RateLimitMiddleware

try:
    from ..middleware.csrf_middleware import CSRFMiddleware
except (ImportError, SystemError):
    from middleware.csrf_middleware import CSRFMiddleware

try:
    from ..middleware.request_logging_middleware import RequestLoggingMiddleware
except (ImportError, SystemError):
    from middleware.request_logging_middleware import RequestLoggingMiddleware

try:
    from ..api.dashboard_routes import register_dashboard_routes
except (ImportError, SystemError):
    from api.dashboard_routes import register_dashboard_routes

try:
    from ..config.database import (
        check_database_connectivity,
        close_database,
        init_database,
    )
except (ImportError, SystemError):
    from config.database import (
        check_database_connectivity,
        close_database,
        init_database,
    )

try:
    from ..services.audit_trail_service import AuditTrailService
except (ImportError, SystemError):
    from services.audit_trail_service import AuditTrailService

try:
    from ..services.vendor_service import VendorService
except (ImportError, SystemError):
    from services.vendor_service import VendorService

try:
    from ..services.vendor_import_export import VendorImportExportService
except (ImportError, SystemError):
    from services.vendor_import_export import VendorImportExportService

try:
    from ..middleware.metrics_middleware import PrometheusMiddleware
except (ImportError, SystemError):
    from middleware.metrics_middleware import PrometheusMiddleware

# Configure structured logging
try:
    from ..config.logging_config import configure_logging
except (ImportError, SystemError):
    from config.logging_config import configure_logging

if production_settings:
    configure_logging(production_settings.LOG_LEVEL, production_settings.LOG_FORMAT)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)

# Server start time (set during lifespan startup)
_server_start_time: float = 0.0

# Graceful shutdown flag — set during shutdown to reject new requests
_shutting_down: bool = False

# Service instances (initialized during startup)
gl_account_service: Optional[GLAccountService] = None
payment_detection_service: Optional[PaymentDetectionService] = None
billing_router_service: Optional[BillingRouterService] = None
document_processor_service: Optional[DocumentProcessorService] = None
storage_service: Optional[ProductionStorageService] = None
scanner_manager_service: Optional[ScannerManagerService] = None
audit_trail_service: Optional[AuditTrailService] = None
vendor_service: Optional[VendorService] = None
vendor_import_export_service: Optional[VendorImportExportService] = None

# Per-tenant upload quota tracking: {tenant_id: deque of upload timestamps}
_upload_timestamps: Dict[str, collections.deque] = {}


def _check_upload_quota(tenant_id: str) -> None:
    """Enforce per-tenant upload quota. Raises HTTPException(429) if exceeded."""
    max_uploads = production_settings.MAX_UPLOADS_PER_TENANT_PER_HOUR
    now = time.time()
    cutoff = now - 3600  # 1 hour window

    if tenant_id not in _upload_timestamps:
        _upload_timestamps[tenant_id] = collections.deque()

    dq = _upload_timestamps[tenant_id]
    # Prune old entries
    while dq and dq[0] < cutoff:
        dq.popleft()

    if len(dq) >= max_uploads:
        raise HTTPException(
            status_code=429,
            detail=f"Upload quota exceeded: {max_uploads} uploads per hour per tenant",
        )
    dq.append(now)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with sophisticated component initialization"""
    global gl_account_service, payment_detection_service, billing_router_service
    global document_processor_service, storage_service, scanner_manager_service
    global audit_trail_service, vendor_service, vendor_import_export_service
    global _server_start_time, _shutting_down

    _shutting_down = False
    _server_start_time = time.time()
    logger.info("🚀 Starting ASR Production Server...")
    logger.info("Initializing sophisticated document processing capabilities...")

    try:
        # Initialize database
        await init_database(
            database_url=production_settings.DATABASE_URL,
            pool_size=production_settings.DB_POOL_SIZE,
            max_overflow=production_settings.DB_POOL_OVERFLOW,
            pool_recycle=production_settings.DB_POOL_RECYCLE,
        )
        logger.info("✅ Database engine initialized")

        # Verify DB connectivity and warn about SQLite in production
        db_check = await check_database_connectivity()
        if db_check["status"] == "connected":
            logger.info(
                "Database connectivity verified: dialect=%s latency=%.1fms",
                db_check["dialect"],
                db_check["latency_ms"],
            )
            if (
                db_check["dialect"] == "sqlite"
                and production_settings.is_production
                and not production_settings.DEBUG
            ):
                logger.warning(
                    "⚠️ SQLite detected in production mode — data will be lost on ECS/Fargate restarts. Use PostgreSQL for durability."
                )
        else:
            logger.error("Database connectivity check failed: %s", db_check)

        # Initialize audit trail service
        audit_trail_service = AuditTrailService(
            enabled=production_settings.AUDIT_TRAIL_ENABLED,
            retention_days=production_settings.AUDIT_RETENTION_DAYS,
        )
        await audit_trail_service.initialize()
        logger.info("✅ Audit Trail Service initialized")

        # Initialize vendor service
        vendor_service = VendorService()
        await vendor_service.initialize()
        logger.info("✅ Vendor Service initialized")

        # Initialize vendor import/export service
        vendor_import_export_service = VendorImportExportService(vendor_service)
        logger.info("✅ Vendor Import/Export Service initialized")

        # Initialize storage service
        storage_service = ProductionStorageService(production_settings.storage_config)
        await storage_service.initialize()
        logger.info("✅ Storage service initialized")

        # Initialize GL Account Service (79 QuickBooks accounts)
        gl_account_service = GLAccountService(
            config_path=production_settings.GL_ACCOUNTS_CONFIG_PATH,
            vendor_service=vendor_service,
        )
        await gl_account_service.initialize()
        account_count = len(gl_account_service.get_all_accounts())
        logger.info(
            f"✅ GL Account Service initialized: {account_count} accounts loaded"
        )

        # Initialize Payment Detection Service (5-method consensus)
        payment_detection_service = PaymentDetectionService(
            production_settings.get_claude_config(),
            production_settings.PAYMENT_DETECTION_METHODS,
        )
        await payment_detection_service.initialize()
        method_count = len(payment_detection_service.get_enabled_methods())
        logger.info(
            f"✅ Payment Detection Service initialized: {method_count} methods enabled"
        )

        # Initialize Billing Router Service (4 destinations)
        billing_router_service = BillingRouterService(
            production_settings.BILLING_DESTINATIONS,
            production_settings.ROUTING_CONFIDENCE_THRESHOLD,
            audit_trail_service=audit_trail_service,
            config_path=production_settings.ROUTING_RULES_CONFIG_PATH,
        )
        await billing_router_service.initialize()
        destination_count = len(billing_router_service.get_available_destinations())
        logger.info(
            f"✅ Billing Router Service initialized: {destination_count} destinations"
        )

        # Initialize Document Processor Service (orchestrates all processing)
        document_processor_service = DocumentProcessorService(
            gl_account_service=gl_account_service,
            payment_detection_service=payment_detection_service,
            billing_router_service=billing_router_service,
            storage_service=storage_service,
        )
        await document_processor_service.initialize()
        logger.info("✅ Document Processor Service initialized")

        # Initialize Scanner Manager Service
        if production_settings.SCANNER_API_ENABLED:
            scanner_manager_service = ScannerManagerService(
                max_clients=production_settings.MAX_SCANNER_CLIENTS
            )
            await scanner_manager_service.initialize()
            logger.info("✅ Scanner Manager Service initialized")

        logger.info("=" * 60)
        logger.info("🎯 Sophisticated Capabilities Ready:")
        logger.info(f"   • {account_count} QuickBooks GL Accounts")
        logger.info(f"   • {method_count} Payment Detection Methods")
        logger.info(f"   • {destination_count} Billing Destinations")
        logger.info(f"   • Multi-tenant: {production_settings.MULTI_TENANT_ENABLED}")
        logger.info(f"   • Scanner API: {production_settings.SCANNER_API_ENABLED}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise

    yield  # Application runs here

    _shutting_down = True
    logger.info(
        "🛑 Shutting down ASR Production Server — draining in-flight requests..."
    )
    # Give in-flight requests a few seconds to complete before tearing down services
    await asyncio.sleep(2)

    # Cleanup services
    services_to_cleanup = [
        storage_service,
        gl_account_service,
        payment_detection_service,
        billing_router_service,
        document_processor_service,
        scanner_manager_service,
        audit_trail_service,
        vendor_service,
    ]

    for service in services_to_cleanup:
        if service:
            try:
                if hasattr(service, "cleanup"):
                    await service.cleanup()
            except Exception as e:
                logger.error(f"Error during service cleanup: {e}")

    await close_database()

    logger.info("✅ ASR Production Server shutdown complete")


# OpenAPI tag metadata
_openapi_tags = [
    {
        "name": "Health",
        "description": "Liveness, readiness, and legacy health-check endpoints.",
    },
    {
        "name": "Auth",
        "description": "Authentication — login and current-user endpoints.",
    },
    {
        "name": "Documents",
        "description": "Document upload, classification, and status.",
    },
    {
        "name": "GL Accounts",
        "description": "QuickBooks GL account listing and search.",
    },
    {
        "name": "Scanner",
        "description": "Scanner client registration, heartbeat, upload, and discovery.",
    },
    {
        "name": "Audit",
        "description": "Audit trail log endpoints.",
    },
    {
        "name": "Vendors",
        "description": "Vendor CRUD and statistics.",
    },
    {
        "name": "System",
        "description": "System info, API status, and dashboard metrics.",
    },
]


# Initialize FastAPI application
app = FastAPI(
    title="ASR Production Server",
    description=production_settings.DESCRIPTION,
    version=production_settings.VERSION,
    lifespan=lifespan,
    docs_url=(
        "/docs"
        if (production_settings.DEBUG or production_settings.ENABLE_DOCS)
        else None
    ),
    redoc_url=(
        "/redoc"
        if (production_settings.DEBUG or production_settings.ENABLE_DOCS)
        else None
    ),
    openapi_tags=_openapi_tags,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=production_settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add request logging middleware (outermost — runs first/last)
app.add_middleware(RequestLoggingMiddleware, log_format=production_settings.LOG_FORMAT)

# Add Prometheus metrics middleware (after request logging, before rate limit)
if production_settings.METRICS_ENABLED:
    app.add_middleware(PrometheusMiddleware)

# Add tenant middleware if multi-tenant enabled
if production_settings.MULTI_TENANT_ENABLED:
    app.add_middleware(TenantMiddleware)

# Add CSRF protection if enabled
if production_settings.CSRF_ENABLED:
    app.add_middleware(
        CSRFMiddleware,
        enabled=production_settings.CSRF_ENABLED,
        secure=production_settings.is_production or production_settings.FORCE_HTTPS,
    )

# Add rate limiting if enabled
if production_settings.RATE_LIMIT_ENABLED:
    app.add_middleware(
        RateLimitMiddleware,
        calls=production_settings.RATE_LIMIT_PER_MINUTE,
        period=60,
        backend=production_settings.RATE_LIMIT_BACKEND,
        redis_url=production_settings.REDIS_URL,
    )

# Register dashboard metrics routes (matches frontend MetricsService.ts calls)
register_dashboard_routes(
    app, Path(production_settings.storage_config.get("base_path", "./storage"))
)


# Authentication dependency
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Authenticate API requests"""
    if not production_settings.API_KEYS_REQUIRED:
        return {
            "tenant_id": production_settings.DEFAULT_TENANT_ID,
            "authenticated": False,
        }

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide a Bearer token in the Authorization header.",
        )

    api_key = credentials.credentials

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )

    return {
        "api_key": api_key,
        "tenant_id": production_settings.DEFAULT_TENANT_ID,
        "authenticated": True,
    }


# Auth endpoints
@app.post("/auth/login", response_model=AuthLoginResponseSchema, tags=["Auth"])
async def auth_login(request: AuthLoginRequestSchema):
    """Authenticate with API key. No Bearer token required."""
    # Dev mode: accept any key when API_KEYS_REQUIRED=false
    if not production_settings.API_KEYS_REQUIRED:
        return AuthLoginResponseSchema(
            authenticated=True,
            tenant_id=request.tenant_id,
            message="Authenticated (dev mode — API keys not required)",
            server_version=production_settings.VERSION,
            capabilities={
                "gl_accounts": 79,
                "payment_methods": len(production_settings.PAYMENT_DETECTION_METHODS),
                "billing_destinations": len(production_settings.BILLING_DESTINATIONS),
                "multi_tenant": production_settings.MULTI_TENANT_ENABLED,
                "scanner_api": production_settings.SCANNER_API_ENABLED,
            },
        )

    # Validate key length
    if len(request.api_key) < 10:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return AuthLoginResponseSchema(
        authenticated=True,
        tenant_id=request.tenant_id,
        message="Authenticated successfully",
        server_version=production_settings.VERSION,
        capabilities={
            "gl_accounts": 79,
            "payment_methods": len(production_settings.PAYMENT_DETECTION_METHODS),
            "billing_destinations": len(production_settings.BILLING_DESTINATIONS),
            "multi_tenant": production_settings.MULTI_TENANT_ENABLED,
            "scanner_api": production_settings.SCANNER_API_ENABLED,
        },
    )


@app.get("/auth/me", response_model=AuthMeResponseSchema, tags=["Auth"])
async def auth_me(user: Dict[str, Any] = Depends(get_current_user)):
    """Get current authenticated user info."""
    return AuthMeResponseSchema(
        authenticated=user.get("authenticated", False),
        tenant_id=user.get("tenant_id", production_settings.DEFAULT_TENANT_ID),
        api_keys_required=production_settings.API_KEYS_REQUIRED,
    )


# Root endpoint
@app.get("/", response_model=APISuccessResponseSchema, tags=["System"])
async def root():
    """Root endpoint with system information"""
    return APISuccessResponseSchema(
        message="ASR Production Server",
        data={
            "system_type": "production_server",
            "version": production_settings.VERSION,
            "git_commit": production_settings.GIT_COMMIT,
            "capabilities": {
                "gl_accounts": 79,
                "payment_methods": len(production_settings.PAYMENT_DETECTION_METHODS),
                "billing_destinations": len(production_settings.BILLING_DESTINATIONS),
                "multi_tenant": production_settings.MULTI_TENANT_ENABLED,
                "scanner_api": production_settings.SCANNER_API_ENABLED,
            },
            "status": "online",
        },
    )


# ---------------------------------------------------------------------------
# Health check endpoints — split into liveness and readiness
# ---------------------------------------------------------------------------


@app.get("/health/live", tags=["Health"])
async def health_live():
    """Liveness probe — always returns 200 if the process is running."""
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - _server_start_time, 2),
    }


@app.get("/health/ready", response_model=SystemHealthResponseSchema, tags=["Health"])
async def health_ready():
    """Readiness probe — checks that all services are initialised and the DB is reachable."""
    if _shutting_down:
        return JSONResponse(
            status_code=503,
            content={
                "overall_status": "shutting_down",
                "message": "Server is draining",
            },
        )

    return await _build_health_response()


@app.get("/health", response_model=SystemHealthResponseSchema, tags=["Health"])
async def health_check():
    """Backwards-compatible health endpoint (alias for /health/ready)."""
    return await _build_health_response()


async def _build_health_response() -> SystemHealthResponseSchema:
    """Shared logic for readiness & legacy health endpoints."""
    health_status = SystemHealthResponseSchema(
        system_type=SystemType.PRODUCTION_SERVER,
        overall_status="healthy",
        components={},
        metrics={},
        uptime_seconds=time.time() - _server_start_time,
        timestamp=datetime.utcnow(),
    )

    try:
        # Database connectivity
        db_health = await check_database_connectivity()
        health_status.components["database"] = db_health
        if db_health.get("status") not in ("connected",):
            health_status.overall_status = "unhealthy"
        elif (
            db_health.get("dialect") in ("sqlite", "aiosqlite")
            and production_settings.is_production
            and not production_settings.DEBUG
        ):
            db_health["degraded"] = True
            db_health["warning"] = "SQLite in production — ephemeral storage risk"
            health_status.overall_status = "degraded"

        # GL Account Service
        if gl_account_service:
            accounts = gl_account_service.get_all_accounts()
            health_status.components["gl_accounts"] = {
                "status": "healthy",
                "count": len(accounts),
                "expected": 79,
            }
        else:
            health_status.components["gl_accounts"] = {"status": "not_initialized"}

        # Payment Detection Service
        if payment_detection_service:
            methods = payment_detection_service.get_enabled_methods()
            health_status.components["payment_detection"] = {
                "status": "healthy",
                "methods": len(methods),
                "enabled_methods": methods,
            }
        else:
            health_status.components["payment_detection"] = {
                "status": "not_initialized"
            }

        # Billing Router Service
        if billing_router_service:
            destinations = billing_router_service.get_available_destinations()
            health_status.components["billing_router"] = {
                "status": "healthy",
                "destinations": len(destinations),
                "available_destinations": destinations,
            }
        else:
            health_status.components["billing_router"] = {"status": "not_initialized"}

        # Storage Service (with timeout to prevent health check from hanging)
        if storage_service:
            try:
                storage_health = await asyncio.wait_for(
                    storage_service.get_health(), timeout=2.0
                )
                storage_healthy = (
                    storage_health.get("status") == "healthy"
                    if isinstance(storage_health, dict)
                    else bool(storage_health)
                )
                health_status.components["storage"] = {
                    "status": "healthy" if storage_healthy else "unhealthy",
                    "backend": production_settings.STORAGE_BACKEND,
                }
            except asyncio.TimeoutError:
                health_status.components["storage"] = {
                    "status": "degraded",
                    "reason": "health check timed out",
                    "backend": production_settings.STORAGE_BACKEND,
                }
        else:
            health_status.components["storage"] = {"status": "not_initialized"}

        # Scanner Manager
        if scanner_manager_service and production_settings.SCANNER_API_ENABLED:
            active_scanners = len(
                await scanner_manager_service.get_connected_scanners()
            )
            health_status.components["scanner_manager"] = {
                "status": "healthy",
                "active_scanners": active_scanners,
                "max_scanners": production_settings.MAX_SCANNER_CLIENTS,
            }

        # Audit Trail
        if audit_trail_service:
            health_status.components["audit_trail"] = (
                audit_trail_service.get_statistics()
            )
        else:
            health_status.components["audit_trail"] = {"status": "not_initialized"}

        # Claude AI
        if production_settings.ANTHROPIC_API_KEY:
            health_status.components["claude_ai"] = {"status": "configured"}
        else:
            health_status.components["claude_ai"] = {"status": "not_configured"}
            health_status.overall_status = "degraded"

    except Exception as e:
        logger.error(f"Health check error: {e}")
        health_status.overall_status = "unhealthy"

    return health_status


# ---------------------------------------------------------------------------
# Prometheus metrics endpoint
# ---------------------------------------------------------------------------

if production_settings.METRICS_ENABLED:

    @app.get(production_settings.METRICS_PATH, tags=["System"])
    async def prometheus_metrics():
        """Expose Prometheus metrics in text format."""
        try:
            from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
            from starlette.responses import Response as StarletteResponse

            return StarletteResponse(
                content=generate_latest(),
                media_type=CONTENT_TYPE_LATEST,
            )
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="prometheus-client not installed",
            )


# Document processing endpoints
@app.post(
    "/api/v1/documents/upload",
    response_model=DocumentUploadResponseSchema,
    tags=["Documents"],
)
async def upload_document(
    file: UploadFile = File(...), user: Dict[str, Any] = Depends(get_current_user)
):
    """Upload and process document through sophisticated pipeline"""
    try:
        if not document_processor_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Document processor service not available",
            )

        # Enforce per-tenant upload quota
        _check_upload_quota(user["tenant_id"])

        # Validate file
        if not file.filename:
            raise ValidationError("Filename is required")

        # Read file content
        file_content = await file.read()
        if len(file_content) == 0:
            raise ValidationError("File is empty")

        # Process document through sophisticated pipeline
        result = await document_processor_service.process_document(
            filename=file.filename,
            file_content=file_content,
            content_type=file.content_type or "application/octet-stream",
            tenant_id=user["tenant_id"],
            uploaded_by=user.get("user_id"),
        )

        return DocumentUploadResponseSchema(
            document_id=result.document_id,
            status=result.status,
            message=f"Document uploaded and processing started",
            processing_time_estimate=result.estimated_processing_time,
        )

    except ASRException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process document upload",
        )


@app.get("/api/v1/documents/{document_id}/status", tags=["Documents"])
async def get_document_status(
    document_id: str, user: Dict[str, Any] = Depends(get_current_user)
):
    """Get document processing status"""
    try:
        validate_document_id(document_id)
        if not document_processor_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Document processor service not available",
            )

        status_info = await document_processor_service.get_document_status(
            document_id=document_id, tenant_id=user["tenant_id"]
        )

        return APISuccessResponseSchema(
            message="Document status retrieved", data=status_info
        )

    except DocumentError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Get document status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document status",
        )


@app.post(
    "/api/v1/documents/{document_id}/classify",
    response_model=ClassificationResponseSchema,
    tags=["Documents"],
)
async def classify_document(
    document_id: str, user: Dict[str, Any] = Depends(get_current_user)
):
    """Trigger document classification through sophisticated pipeline"""
    try:
        validate_document_id(document_id)
        if not document_processor_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Document processor service not available",
            )

        result = await document_processor_service.classify_document(
            document_id=document_id, tenant_id=user["tenant_id"]
        )

        return ClassificationResponseSchema(
            document_id=document_id,
            classification_successful=result.classification_successful,
            gl_account_code=result.gl_account,
            gl_account_name=result.gl_account_name,
            gl_confidence=result.gl_confidence,
            gl_reasoning=result.gl_reasoning,
            payment_status=result.payment_status,
            payment_consensus=result.payment_consensus,
            vendor_name=result.vendor_name,
            amount=result.amount,
            invoice_date=result.invoice_date,
            processing_time=result.processing_time,
            classification_timestamp=result.classification_timestamp,
            quality_score=result.quality_score,
        )

    except DocumentError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Document classification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to classify document",
        )


# Document deletion endpoint
@app.delete(
    "/api/v1/documents/{document_id}",
    response_model=APISuccessResponseSchema,
    tags=["Documents"],
)
async def delete_document(
    document_id: str, user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a document by ID"""
    try:
        validate_document_id(document_id)
        if not storage_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Storage service not available",
            )

        deleted = await storage_service.delete_document(
            document_id, tenant_id=user.get("tenant_id")
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )

        # Log to audit trail
        if audit_trail_service:
            from shared.core.models import AuditTrailEntry

            await audit_trail_service.record(
                AuditTrailEntry(
                    document_id=document_id,
                    event_type="document_deleted",
                    event_data={"deleted_by": user.get("tenant_id")},
                    system_component="api",
                    tenant_id=user.get("tenant_id", "unknown"),
                )
            )

        return APISuccessResponseSchema(
            message="Document deleted",
            data={"document_id": document_id, "success": True},
        )

    except HTTPException:
        raise
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Document deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        )


# GL Account endpoints
@app.get("/api/v1/gl-accounts", tags=["GL Accounts"])
async def list_gl_accounts(
    category: Optional[str] = None,
    search: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """List available GL accounts with filtering"""
    try:
        if not gl_account_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GL Account service not available",
            )

        accounts = gl_account_service.get_accounts(category=category, search=search)

        return APISuccessResponseSchema(
            message="GL accounts retrieved",
            data={
                "accounts": accounts,
                "total_count": len(accounts),
                "categories": gl_account_service.get_categories(),
            },
        )

    except Exception as e:
        logger.error(f"List GL accounts error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve GL accounts",
        )


@app.post("/api/v1/gl-accounts", status_code=201, tags=["GL Accounts"])
async def create_gl_account(
    request: GLAccountCreateRequestSchema,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Create a new GL account."""
    try:
        if not gl_account_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GL Account service not available",
            )
        # Override schema tenant_id with the authenticated user's tenant
        auth_tenant = user.get("tenant_id", production_settings.DEFAULT_TENANT_ID)
        result = await gl_account_service.create_gl_account(
            code=request.code,
            name=request.name,
            category=request.category,
            keywords=request.keywords,
            description=request.description or "",
            tenant_id=auth_tenant,
        )
        return APISuccessResponseSchema(message="GL account created", data=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create GL account error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create GL account",
        )


@app.put("/api/v1/gl-accounts/{code}", tags=["GL Accounts"])
async def update_gl_account_endpoint(
    code: str,
    request: GLAccountUpdateRequestSchema,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Update an existing GL account."""
    try:
        if not gl_account_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GL Account service not available",
            )
        updates = request.model_dump(exclude_none=True)
        auth_tenant = user.get("tenant_id", production_settings.DEFAULT_TENANT_ID)
        result = await gl_account_service.update_gl_account(
            code, updates, tenant_id=auth_tenant
        )
        if result == "__FORBIDDEN__":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot modify GL account {code} — owned by another tenant",
            )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"GL account {code} not found",
            )
        return APISuccessResponseSchema(message="GL account updated", data=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update GL account error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update GL account",
        )


@app.delete("/api/v1/gl-accounts/{code}", tags=["GL Accounts"])
async def delete_gl_account_endpoint(
    code: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Delete a GL account."""
    try:
        if not gl_account_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GL Account service not available",
            )
        auth_tenant = user.get("tenant_id", production_settings.DEFAULT_TENANT_ID)
        deleted = await gl_account_service.delete_gl_account(
            code, tenant_id=auth_tenant
        )
        if deleted == "__FORBIDDEN__":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot delete GL account {code} — owned by another tenant",
            )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"GL account {code} not found",
            )
        return APISuccessResponseSchema(
            message="GL account deleted", data={"code": code}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete GL account error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete GL account",
        )


# ---------------------------------------------------------------------------
# Audit trail endpoints
# ---------------------------------------------------------------------------


@app.get(
    "/api/v1/audit-logs",
    response_model=APISuccessResponseSchema,
    tags=["Audit"],
)
async def list_audit_logs(
    tenant_id: str = "default",
    event_type: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = 100,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """List audit trail entries for a tenant with optional filters."""
    try:
        if not audit_trail_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Audit trail service not available",
            )

        since_dt = None
        if since:
            since_dt = datetime.fromisoformat(since)

        entries = await audit_trail_service.query_by_tenant(
            tenant_id=tenant_id,
            event_type=event_type,
            since=since_dt,
            limit=limit,
        )

        return APISuccessResponseSchema(
            message="Audit logs retrieved",
            data=AuditLogListResponseSchema(
                entries=[AuditLogEntrySchema(**e) for e in entries],
                total_count=len(entries),
            ).model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audit log query error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs",
        )


@app.get(
    "/api/v1/audit-logs/{document_id}",
    response_model=APISuccessResponseSchema,
    tags=["Audit"],
)
async def get_document_audit_logs(
    document_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Get audit trail entries for a specific document."""
    try:
        validate_document_id(document_id)
        if not audit_trail_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Audit trail service not available",
            )

        tenant_id = user.get("tenant_id")
        entries = await audit_trail_service.query_by_document(
            document_id=document_id,
            tenant_id=tenant_id,
        )

        return APISuccessResponseSchema(
            message="Document audit logs retrieved",
            data=AuditLogListResponseSchema(
                entries=[AuditLogEntrySchema(**e) for e in entries],
                total_count=len(entries),
            ).model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document audit log query error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document audit logs",
        )


# ---------------------------------------------------------------------------
# Reprocess / extract detail endpoints (match frontend DocumentService.ts)
# ---------------------------------------------------------------------------


@app.post("/extract/invoice/{document_id}", tags=["Documents"])
async def reprocess_document(
    document_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Reprocess an existing document through the classification pipeline."""
    try:
        validate_document_id(document_id)
        if not document_processor_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Document processor service not available",
            )

        result = await document_processor_service.reprocess_document(
            document_id=document_id,
            tenant_id=user.get("tenant_id"),
        )

        return APISuccessResponseSchema(
            message="Document reprocessing started",
            data={
                "document_id": result.document_id,
                "status": result.processing_status,
            },
        )

    except DocumentError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Document reprocess error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reprocess document",
        )


@app.get("/extract/invoice/{document_id}/details", tags=["Documents"])
async def get_extract_details(
    document_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Get classification details for a document."""
    try:
        validate_document_id(document_id)
        if not document_processor_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Document processor service not available",
            )

        status_info = await document_processor_service.get_processing_status(
            document_id=document_id,
            tenant_id=user.get("tenant_id"),
        )

        if not status_info:
            raise HTTPException(status_code=404, detail="Document not found")

        return APISuccessResponseSchema(
            message="Classification details retrieved",
            data=status_info,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extract details error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve classification details",
        )


# ---------------------------------------------------------------------------
# Search endpoint (matches frontend DocumentService.ts /search/quick)
# ---------------------------------------------------------------------------


@app.get("/search/quick", tags=["Documents"])
async def quick_search(
    q: str = "",
    status_filter: Optional[str] = None,
    limit: int = 20,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Quick search across documents by filename or vendor."""
    try:
        results = []
        if q.strip() and storage_service:
            results = await storage_service.search_documents(
                q.strip(), limit=limit, tenant_id=user.get("tenant_id")
            )

        return APISuccessResponseSchema(
            message="Search results",
            data={"results": results, "total": len(results), "query": q},
        )

    except Exception as e:
        logger.error(f"Quick search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed",
        )


# ---------------------------------------------------------------------------
# Vendor CRUD endpoints (matches frontend VendorService.ts)
# ---------------------------------------------------------------------------


@app.get("/vendors", tags=["Vendors"])
async def list_vendors(user: Dict[str, Any] = Depends(get_current_user)):
    """List all vendors."""
    try:
        if not vendor_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vendor service not available",
            )
        vendors = await vendor_service.list_vendors(tenant_id=user.get("tenant_id"))
        return vendors
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List vendors error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list vendors",
        )


@app.get("/vendors/export", tags=["Vendors"])
async def export_vendors(
    format: str = "json",
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Export all vendors in JSON or CSV format."""
    try:
        if not vendor_import_export_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Import/export service not available",
            )
        tenant_id = user.get("tenant_id", production_settings.DEFAULT_TENANT_ID)

        if format == "csv":
            csv_data = await vendor_import_export_service.export_vendors_csv(
                tenant_id=tenant_id
            )
            return JSONResponse(
                content={"success": True, "format": "csv", "data": csv_data},
            )
        else:
            json_data = await vendor_import_export_service.export_vendors_json(
                tenant_id=tenant_id
            )
            return {"success": True, "format": "json", "data": json_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export vendors error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export vendors",
        )


@app.get("/vendors/{vendor_id}", tags=["Vendors"])
async def get_vendor(vendor_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    """Get a single vendor by ID."""
    try:
        if not vendor_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vendor service not available",
            )
        vendor = await vendor_service.get_vendor(
            vendor_id, tenant_id=user.get("tenant_id")
        )
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor {vendor_id} not found",
            )
        return vendor
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get vendor error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get vendor",
        )


@app.post("/vendors", status_code=201, tags=["Vendors"])
async def create_vendor(
    request: VendorCreateRequestSchema,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Create a new vendor."""
    try:
        if not vendor_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vendor service not available",
            )
        vendor = await vendor_service.create_vendor(
            name=request.name,
            tenant_id=request.tenant_id or user.get("tenant_id", "default"),
            display_name=request.display_name,
            contact_info=request.contact_info,
            notes=request.notes,
            tags=request.tags,
        )
        # Apply optional DB fields not in base create_vendor signature
        extra_fields = {}
        for field in (
            "default_gl_account",
            "aliases",
            "payment_terms",
            "payment_terms_days",
            "vendor_type",
        ):
            val = getattr(request, field, None)
            if val is not None:
                extra_fields[field] = val
        if extra_fields:
            vendor = await vendor_service.update_vendor(
                vendor["id"], extra_fields, tenant_id=user.get("tenant_id")
            )
        return vendor
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create vendor error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create vendor",
        )


@app.put("/vendors/{vendor_id}", tags=["Vendors"])
async def update_vendor(
    vendor_id: str,
    request: VendorUpdateRequestSchema,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Update an existing vendor."""
    try:
        if not vendor_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vendor service not available",
            )
        updates = request.model_dump(exclude_none=True)
        vendor = await vendor_service.update_vendor(
            vendor_id, updates, tenant_id=user.get("tenant_id")
        )
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor {vendor_id} not found",
            )
        return vendor
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update vendor error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update vendor",
        )


@app.delete("/vendors/{vendor_id}", tags=["Vendors"])
async def delete_vendor_endpoint(
    vendor_id: str, user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a vendor by ID."""
    try:
        if not vendor_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vendor service not available",
            )
        deleted = await vendor_service.delete_vendor(
            vendor_id, tenant_id=user.get("tenant_id")
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor {vendor_id} not found",
            )
        return {"success": True, "message": "Vendor deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete vendor error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete vendor",
        )


@app.get("/vendors/{vendor_id}/stats", tags=["Vendors"])
async def get_vendor_stats(
    vendor_id: str, user: Dict[str, Any] = Depends(get_current_user)
):
    """Get statistics for a specific vendor."""
    try:
        if not vendor_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vendor service not available",
            )
        stats = await vendor_service.get_vendor_stats(
            vendor_id, tenant_id=user.get("tenant_id")
        )
        if stats is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor {vendor_id} not found",
            )
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get vendor stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get vendor stats",
        )


# ---------------------------------------------------------------------------
# Vendor Import/Export endpoints (export route moved above {vendor_id})
# ---------------------------------------------------------------------------


@app.post(
    "/vendors/import",
    response_model=VendorImportResultSchema,
    tags=["Vendors"],
)
async def import_vendors(
    body: VendorImportRequestSchema,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Import vendors from JSON payload."""
    try:
        if not vendor_import_export_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Import/export service not available",
            )
        tenant_id = user.get("tenant_id", production_settings.DEFAULT_TENANT_ID)

        # Collect valid GL codes for validation
        gl_codes: set = set()
        if gl_account_service and gl_account_service.gl_accounts:
            gl_codes = set(gl_account_service.gl_accounts.keys())

        result = await vendor_import_export_service.import_vendors_json(
            data=body.vendors,
            mode=body.mode,
            tenant_id=tenant_id,
            gl_codes=gl_codes if gl_codes else None,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Import vendors error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to import vendors",
        )


@app.post("/vendors/import/validate", tags=["Vendors"])
async def validate_vendor_import(
    body: VendorImportRequestSchema,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Dry-run validation of vendor import data."""
    try:
        if not vendor_import_export_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Import/export service not available",
            )
        gl_codes: set = set()
        if gl_account_service and gl_account_service.gl_accounts:
            gl_codes = set(gl_account_service.gl_accounts.keys())

        tenant_id = user.get("tenant_id", production_settings.DEFAULT_TENANT_ID)
        result = vendor_import_export_service.validate_import_data(
            data=body.vendors,
            gl_codes=gl_codes if gl_codes else None,
            tenant_id=tenant_id,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validate vendor import error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate import data",
        )


# ---------------------------------------------------------------------------
# Settings endpoint
# ---------------------------------------------------------------------------


@app.get(
    "/api/v1/settings",
    response_model=APISuccessResponseSchema,
    tags=["System"],
)
async def get_settings(
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Get unified system settings and configuration."""
    tenant_id = user.get("tenant_id", production_settings.DEFAULT_TENANT_ID)

    settings_data = SettingsResponseSchema(
        tenant_id=tenant_id,
        system_type="production_server",
        version=production_settings.VERSION,
        capabilities={
            "gl_accounts": {
                "total": 79,
                "enabled": production_settings.GL_ACCOUNTS_ENABLED,
            },
            "payment_detection": {
                "methods": production_settings.PAYMENT_DETECTION_METHODS,
                "consensus_enabled": True,
            },
            "billing_destinations": production_settings.BILLING_DESTINATIONS,
            "multi_tenant": production_settings.MULTI_TENANT_ENABLED,
            "scanner_api": production_settings.SCANNER_API_ENABLED,
        },
        limits={
            "max_file_size_mb": production_settings.MAX_FILE_SIZE_MB,
            "max_batch_size": production_settings.MAX_BATCH_SIZE,
            "max_scanner_clients": production_settings.MAX_SCANNER_CLIENTS,
            "rate_limit_per_minute": production_settings.RATE_LIMIT_PER_MINUTE,
        },
        security={
            "api_keys_required": production_settings.API_KEYS_REQUIRED,
            "csrf_enabled": production_settings.CSRF_ENABLED,
            "rate_limit_enabled": production_settings.RATE_LIMIT_ENABLED,
            "cors_origins": production_settings.cors_origins_list,
        },
        storage={
            "backend": production_settings.STORAGE_BACKEND,
            "base_path": production_settings.storage_config.get(
                "base_path", "./storage"
            ),
        },
    )

    return APISuccessResponseSchema(
        message="Settings retrieved",
        data=settings_data.model_dump(),
    )


# Scanner API endpoints (if enabled)
if production_settings.SCANNER_API_ENABLED:

    @app.post("/api/v1/scanner/register", tags=["Scanner"])
    async def register_scanner(
        request: ScannerRegistrationSchema,
        user: Dict[str, Any] = Depends(get_current_user),
    ):
        """Register a new scanner client"""
        try:
            if not scanner_manager_service:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Scanner manager service not available",
                )

            result = await scanner_manager_service.register_scanner(
                scanner_name=request.scanner_name,
                tenant_id=request.tenant_id,
                api_key=request.api_key,
                capabilities=request.capabilities,
            )

            return APISuccessResponseSchema(
                message="Scanner registered successfully", data=result
            )

        except Exception as e:
            logger.error(f"Scanner registration error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register scanner",
            )

    @app.post("/api/v1/scanner/heartbeat", tags=["Scanner"])
    async def scanner_heartbeat(
        request: ScannerHeartbeatSchema,
        user: Dict[str, Any] = Depends(get_current_user),
    ):
        """Process scanner heartbeat"""
        try:
            if not scanner_manager_service:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Scanner manager service not available",
                )

            await scanner_manager_service.process_heartbeat(
                scanner_id=request.scanner_id,
                status=request.status,
                queued_documents=request.queued_documents,
                metrics=request.metrics,
            )

            return APISuccessResponseSchema(message="Heartbeat processed")

        except Exception as e:
            logger.error(f"Scanner heartbeat error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process scanner heartbeat",
            )


# Error handlers
@app.exception_handler(ASRException)
async def asr_exception_handler(request, exc: ASRException):
    """Handle ASR-specific exceptions"""
    return JSONResponse(
        status_code=400,
        content=APIErrorResponseSchema(
            message=exc.message, errors=[exc.to_dict()]
        ).model_dump(),
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc: ValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=422,
        content=APIErrorResponseSchema(
            message="Validation error",
            errors=[{"error_type": "ValidationError", "message": str(exc)}],
        ).model_dump(),
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    """Handle ValueError (e.g. document ID validation failures)."""
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation error",
            "errors": [
                {
                    "error_code": "VALIDATION_ERROR",
                    "error_type": "ValueError",
                    "message": str(exc),
                }
            ],
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """Catch-all handler — returns structured JSON for any unhandled exception."""
    request_id = getattr(getattr(request, "state", None), "request_id", None)
    logger.error(
        "unhandled_exception request_id=%s path=%s error=%s",
        request_id,
        request.url.path,
        exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content=APIErrorResponseSchema(
            message="Internal server error",
            errors=[
                {
                    "error_code": "INTERNAL_ERROR",
                    "error_type": "server",
                    "message": "An unexpected error occurred",
                }
            ],
        ).model_dump(),
        headers={"X-Request-ID": request_id or ""},
    )


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "message": "Endpoint not found",
            "errors": [
                {
                    "error_code": "NOT_FOUND",
                    "error_type": "routing",
                    "message": (
                        str(exc.detail) if hasattr(exc, "detail") else "Not found"
                    ),
                }
            ],
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "errors": [
                {
                    "error_code": "INTERNAL_ERROR",
                    "error_type": "server",
                    "message": str(exc),
                }
            ],
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.get("/api/status", tags=["System"])
async def api_status():
    """API status endpoint with service health summary"""
    services_status = {}

    if gl_account_service:
        accounts = gl_account_service.get_all_accounts()
        services_status["gl_accounts"] = {"status": "active", "count": len(accounts)}
    else:
        services_status["gl_accounts"] = {"status": "not_initialized"}

    if payment_detection_service:
        methods = payment_detection_service.get_enabled_methods()
        services_status["payment_detection"] = {
            "status": "active",
            "methods": len(methods),
        }
    else:
        services_status["payment_detection"] = {"status": "not_initialized"}

    if billing_router_service:
        destinations = billing_router_service.get_available_destinations()
        services_status["billing_router"] = {
            "status": "active",
            "destinations": len(destinations),
        }
    else:
        services_status["billing_router"] = {"status": "not_initialized"}

    if storage_service:
        services_status["storage"] = {
            "status": "active",
            "backend": production_settings.STORAGE_BACKEND,
        }
    else:
        services_status["storage"] = {"status": "not_initialized"}

    if scanner_manager_service:
        active = len(await scanner_manager_service.get_connected_scanners())
        services_status["scanner_manager"] = {
            "status": "active",
            "active_scanners": active,
        }
    else:
        services_status["scanner_manager"] = {"status": "not_initialized"}

    all_active = all(s.get("status") == "active" for s in services_status.values())

    return APISuccessResponseSchema(
        message="API status",
        data={
            "system_type": "production_server",
            "version": production_settings.VERSION,
            "status": "operational" if all_active else "degraded",
            "services": services_status,
            "claude_ai": (
                "configured"
                if production_settings.ANTHROPIC_API_KEY
                else "not_configured"
            ),
        },
    )


# Additional endpoints for system management
@app.get("/api/v1/system/info", tags=["System"])
async def get_system_info():
    """Get system information and capabilities"""
    return APISuccessResponseSchema(
        message="System information",
        data={
            "system_type": "production_server",
            "version": production_settings.VERSION,
            "capabilities": {
                "gl_accounts": {
                    "total": 79,
                    "enabled": production_settings.GL_ACCOUNTS_ENABLED,
                },
                "payment_detection": {
                    "methods": production_settings.PAYMENT_DETECTION_METHODS,
                    "consensus_enabled": True,
                },
                "billing_router": {
                    "destinations": production_settings.BILLING_DESTINATIONS,
                    "audit_trails": production_settings.AUDIT_TRAIL_ENABLED,
                },
                "multi_tenant": production_settings.MULTI_TENANT_ENABLED,
                "scanner_api": production_settings.SCANNER_API_ENABLED,
            },
            "limits": {
                "max_file_size_mb": production_settings.MAX_FILE_SIZE_MB,
                "max_batch_size": production_settings.MAX_BATCH_SIZE,
                "max_scanner_clients": production_settings.MAX_SCANNER_CLIENTS,
            },
        },
    )


# Legacy API info endpoint for scanner compatibility
@app.get("/api/info", tags=["Scanner"])
async def get_api_info():
    """Legacy API info endpoint for scanner client compatibility"""
    return {
        "name": "ASR Production Server",
        "version": production_settings.VERSION,
        "capabilities": [
            "document_processing",
            "gl_account_classification",
            "payment_detection",
            "billing_routing",
            "scanner_upload",
            "batch_upload",
            "multi_tenant",
        ],
        "gl_accounts_count": 79,
        "supported_formats": ["pdf", "jpg", "jpeg", "png", "tiff", "gif"],
        "max_file_size_mb": production_settings.MAX_FILE_SIZE_MB,
    }


# Enhanced Scanner API Endpoints
if production_settings.SCANNER_API_ENABLED:

    @app.get("/api/scanner/discovery", tags=["Scanner"])
    async def scanner_discovery(
        user: Dict[str, Any] = Depends(get_current_user),
    ):
        """Scanner server discovery endpoint (requires authentication)"""
        try:
            return APISuccessResponseSchema(
                message="Server discovery successful",
                data={
                    "server_url": f"http://localhost:{production_settings.API_PORT}",
                    "server_name": "ASR Production Server",
                    "version": production_settings.VERSION,
                    "capabilities": [
                        "document_processing",
                        "gl_account_classification",
                        "payment_detection",
                        "billing_routing",
                        "scanner_upload",
                        "batch_upload",
                    ],
                    "api_endpoints": {
                        "upload": "/api/scanner/upload",
                        "batch": "/api/scanner/batch",
                        "status": "/api/scanner/status",
                        "register": "/api/v1/scanner/register",
                        "heartbeat": "/api/v1/scanner/heartbeat",
                    },
                    "limits": {
                        "max_file_size_mb": production_settings.MAX_FILE_SIZE_MB,
                        "max_batch_size": production_settings.MAX_BATCH_SIZE,
                        "supported_formats": [
                            "pdf",
                            "jpg",
                            "jpeg",
                            "png",
                            "tiff",
                            "gif",
                        ],
                    },
                    "gl_accounts": {
                        "total": 79,
                        "categories": [
                            "ASSETS",
                            "LIABILITIES",
                            "EQUITY",
                            "INCOME",
                            "EXPENSES",
                        ],
                    },
                    "payment_detection": {
                        "methods": production_settings.PAYMENT_DETECTION_METHODS,
                        "consensus_enabled": True,
                    },
                },
            )
        except Exception as e:
            logger.error(f"❌ Scanner discovery failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/scanner/upload", tags=["Scanner"])
    async def scanner_upload(
        file: UploadFile = File(...),
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ):
        """Document upload endpoint for scanner clients"""
        try:
            # Extract scanner info from form data
            form_data = {}
            if hasattr(file, "metadata"):
                form_data["metadata"] = file.metadata
            if hasattr(file, "scanner_info"):
                form_data["scanner_info"] = file.scanner_info

            # Get scanner ID from scanner_info or generate one
            scanner_info = form_data.get("scanner_info", {})
            scanner_id = scanner_info.get("scanner_id", "unknown_scanner")

            # Read file content
            file_content = await file.read()

            # Create upload request
            upload_request = ScannerUploadRequest(
                scanner_id=scanner_id,
                filename=file.filename,
                file_content=file_content,
                metadata=form_data.get("metadata"),
                scanner_info=scanner_info,
            )

            # Process upload
            result = await scanner_manager_service.process_scanner_upload(
                upload_request, document_processor_service
            )

            if result.success:
                return APISuccessResponseSchema(
                    message="Document uploaded successfully",
                    data={
                        "document_id": result.document_id,
                        "status": result.processing_status,
                        "processing_time_ms": result.processing_time_ms,
                        "classification": result.classification_result,
                    },
                )
            else:
                raise HTTPException(status_code=400, detail=result.error_message)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Scanner upload failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/scanner/status/{session_id}", tags=["Scanner"])
    async def get_scanner_upload_status(
        session_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Get upload status for scanner clients"""
        try:
            status = await scanner_manager_service.get_upload_status(session_id)

            if status:
                return APISuccessResponseSchema(
                    message="Upload status retrieved", data=status
                )
            else:
                raise HTTPException(status_code=404, detail="Upload session not found")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Failed to get upload status: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/scanner/batch", tags=["Scanner"])
    async def scanner_batch_upload(
        files: List[UploadFile] = File(...),
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ):
        """Batch document upload endpoint for scanner clients"""
        try:
            if len(files) > production_settings.MAX_BATCH_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"Batch size exceeds limit ({production_settings.MAX_BATCH_SIZE})",
                )

            # Create upload requests
            upload_requests = []
            scanner_id = "batch_scanner_client"  # Default for batch uploads

            for file in files:
                file_content = await file.read()

                upload_request = ScannerUploadRequest(
                    scanner_id=scanner_id,
                    filename=file.filename,
                    file_content=file_content,
                    metadata={},
                    scanner_info={"batch_upload": True},
                )
                upload_requests.append(upload_request)

            # Process batch upload
            results = await scanner_manager_service.process_batch_upload(
                scanner_id, upload_requests, document_processor_service
            )

            # Prepare response
            successful_uploads = len([r for r in results if r.success])
            response_data = {
                "batch_size": len(files),
                "successful_uploads": successful_uploads,
                "failed_uploads": len(files) - successful_uploads,
                "results": [],
            }

            for i, result in enumerate(results):
                response_data["results"].append(
                    {
                        "filename": files[i].filename,
                        "success": result.success,
                        "document_id": result.document_id,
                        "error_message": result.error_message,
                        "processing_time_ms": result.processing_time_ms,
                    }
                )

            return APISuccessResponseSchema(
                message=f"Batch upload completed: {successful_uploads}/{len(files)} successful",
                data=response_data,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Batch upload failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/scanner/connected", tags=["Scanner"])
    async def get_connected_scanners(
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ):
        """Get list of connected scanner clients"""
        try:
            scanners = await scanner_manager_service.get_connected_scanners()

            return APISuccessResponseSchema(
                message="Connected scanners retrieved",
                data={"count": len(scanners), "scanners": scanners},
            )

        except Exception as e:
            logger.error(f"❌ Failed to get connected scanners: {e}")
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    host = production_settings.get_api_host
    port = production_settings.API_PORT

    logger.info(f"Starting ASR Production Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
