"""
ASR Production Server - FastAPI Application
Enterprise document processing server with sophisticated capabilities
• 79 QuickBooks GL Accounts with keyword matching
• 5-Method Payment Detection with consensus scoring
• 4 Billing Destination routing with audit trails
• Multi-tenant document isolation
• Scanner client API for distributed processing
"""

import os
import time
import logging
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Import shared components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from shared.core.models import (
    DocumentMetadata, ProcessingStatus, PaymentStatus, BillingDestination,
    PaymentConsensusResult, SystemHealth, SystemType
)
from shared.core.exceptions import (
    ASRException, DocumentError, ValidationError, AuthenticationError,
    handle_exception
)
from shared.api.schemas import (
    DocumentUploadResponseSchema, ClassificationResponseSchema,
    SystemHealthResponseSchema, APISuccessResponseSchema, APIErrorResponseSchema,
    ScannerRegistrationSchema, ScannerHeartbeatSchema
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
    from ..services.scanner_manager_service import ScannerManagerService, ScannerUploadRequest
except (ImportError, SystemError):
    from services.scanner_manager_service import ScannerManagerService, ScannerUploadRequest

try:
    from ..middleware.tenant_middleware import TenantMiddleware
except (ImportError, SystemError):
    from middleware.tenant_middleware import TenantMiddleware

try:
    from ..middleware.rate_limit_middleware import RateLimitMiddleware
except (ImportError, SystemError):
    from middleware.rate_limit_middleware import RateLimitMiddleware

try:
    from ..config.database import init_database, close_database
except (ImportError, SystemError):
    from config.database import init_database, close_database

try:
    from ..services.audit_trail_service import AuditTrailService
except (ImportError, SystemError):
    from services.audit_trail_service import AuditTrailService

# Configure logging
_log_level = getattr(logging, production_settings.LOG_LEVEL) if production_settings else logging.INFO
logging.basicConfig(level=_log_level)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)

# Server start time (set during lifespan startup)
_server_start_time: float = 0.0

# Service instances (initialized during startup)
gl_account_service: Optional[GLAccountService] = None
payment_detection_service: Optional[PaymentDetectionService] = None
billing_router_service: Optional[BillingRouterService] = None
document_processor_service: Optional[DocumentProcessorService] = None
storage_service: Optional[ProductionStorageService] = None
scanner_manager_service: Optional[ScannerManagerService] = None
audit_trail_service: Optional[AuditTrailService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with sophisticated component initialization"""
    global gl_account_service, payment_detection_service, billing_router_service
    global document_processor_service, storage_service, scanner_manager_service
    global audit_trail_service, _server_start_time

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

        # Initialize audit trail service
        audit_trail_service = AuditTrailService(
            enabled=production_settings.AUDIT_TRAIL_ENABLED,
            retention_days=production_settings.AUDIT_RETENTION_DAYS,
        )
        await audit_trail_service.initialize()
        logger.info("✅ Audit Trail Service initialized")

        # Initialize storage service
        storage_service = ProductionStorageService(production_settings.storage_config)
        await storage_service.initialize()
        logger.info("✅ Storage service initialized")

        # Initialize GL Account Service (79 QuickBooks accounts)
        gl_account_service = GLAccountService()
        await gl_account_service.initialize()
        account_count = len(gl_account_service.get_all_accounts())
        logger.info(f"✅ GL Account Service initialized: {account_count} accounts loaded")

        # Initialize Payment Detection Service (5-method consensus)
        payment_detection_service = PaymentDetectionService(
            production_settings.get_claude_config(),
            production_settings.PAYMENT_DETECTION_METHODS
        )
        await payment_detection_service.initialize()
        method_count = len(payment_detection_service.get_enabled_methods())
        logger.info(f"✅ Payment Detection Service initialized: {method_count} methods enabled")

        # Initialize Billing Router Service (4 destinations)
        billing_router_service = BillingRouterService(
            production_settings.BILLING_DESTINATIONS,
            production_settings.ROUTING_CONFIDENCE_THRESHOLD,
            audit_trail_service=audit_trail_service,
        )
        await billing_router_service.initialize()
        destination_count = len(billing_router_service.get_available_destinations())
        logger.info(f"✅ Billing Router Service initialized: {destination_count} destinations")

        # Initialize Document Processor Service (orchestrates all processing)
        document_processor_service = DocumentProcessorService(
            gl_account_service=gl_account_service,
            payment_detection_service=payment_detection_service,
            billing_router_service=billing_router_service,
            storage_service=storage_service
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

    logger.info("🛑 Shutting down ASR Production Server services...")

    # Cleanup services
    services_to_cleanup = [
        storage_service,
        gl_account_service,
        payment_detection_service,
        billing_router_service,
        document_processor_service,
        scanner_manager_service,
        audit_trail_service,
    ]

    for service in services_to_cleanup:
        if service:
            try:
                if hasattr(service, 'cleanup'):
                    await service.cleanup()
            except Exception as e:
                logger.error(f"Error during service cleanup: {e}")

    await close_database()

    logger.info("✅ ASR Production Server shutdown complete")


# Initialize FastAPI application
app = FastAPI(
    title="ASR Production Server",
    description=production_settings.DESCRIPTION,
    version=production_settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs" if production_settings.DEBUG else None,
    redoc_url="/redoc" if production_settings.DEBUG else None
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=production_settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add tenant middleware if multi-tenant enabled
if production_settings.MULTI_TENANT_ENABLED:
    app.add_middleware(TenantMiddleware)

# Add rate limiting if enabled
if production_settings.RATE_LIMIT_ENABLED:
    app.add_middleware(
        RateLimitMiddleware,
        calls=production_settings.RATE_LIMIT_PER_MINUTE,
        period=60
    )


# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Authenticate API requests"""
    if not production_settings.API_KEYS_REQUIRED:
        return {"tenant_id": production_settings.DEFAULT_TENANT_ID, "authenticated": False}

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide a Bearer token in the Authorization header."
        )

    api_key = credentials.credentials

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return {
        "api_key": api_key,
        "tenant_id": production_settings.DEFAULT_TENANT_ID,
        "authenticated": True
    }


# Root endpoint
@app.get("/", response_model=APISuccessResponseSchema)
async def root():
    """Root endpoint with system information"""
    return APISuccessResponseSchema(
        message="ASR Production Server",
        data={
            "system_type": "production_server",
            "version": production_settings.VERSION,
            "capabilities": {
                "gl_accounts": 79,
                "payment_methods": len(production_settings.PAYMENT_DETECTION_METHODS),
                "billing_destinations": len(production_settings.BILLING_DESTINATIONS),
                "multi_tenant": production_settings.MULTI_TENANT_ENABLED,
                "scanner_api": production_settings.SCANNER_API_ENABLED
            },
            "status": "online"
        }
    )


# Health check endpoint
@app.get("/health", response_model=SystemHealthResponseSchema)
async def health_check():
    """Comprehensive health check with sophisticated component status"""
    health_status = SystemHealthResponseSchema(
        system_type=SystemType.PRODUCTION_SERVER,
        overall_status="healthy",
        components={},
        metrics={},
        uptime_seconds=time.time() - _server_start_time,
        timestamp=datetime.utcnow()
    )

    # Check services
    try:
        # GL Account Service
        if gl_account_service:
            accounts = gl_account_service.get_all_accounts()
            health_status.components["gl_accounts"] = {
                "status": "healthy",
                "count": len(accounts),
                "expected": 79
            }
        else:
            health_status.components["gl_accounts"] = {"status": "not_initialized"}

        # Payment Detection Service
        if payment_detection_service:
            methods = payment_detection_service.get_enabled_methods()
            health_status.components["payment_detection"] = {
                "status": "healthy",
                "methods": len(methods),
                "enabled_methods": methods
            }
        else:
            health_status.components["payment_detection"] = {"status": "not_initialized"}

        # Billing Router Service
        if billing_router_service:
            destinations = billing_router_service.get_available_destinations()
            health_status.components["billing_router"] = {
                "status": "healthy",
                "destinations": len(destinations),
                "available_destinations": destinations
            }
        else:
            health_status.components["billing_router"] = {"status": "not_initialized"}

        # Storage Service
        if storage_service:
            storage_health = await storage_service.get_health()
            storage_healthy = storage_health.get("status") == "healthy" if isinstance(storage_health, dict) else bool(storage_health)
            health_status.components["storage"] = {
                "status": "healthy" if storage_healthy else "unhealthy",
                "backend": production_settings.STORAGE_BACKEND
            }
        else:
            health_status.components["storage"] = {"status": "not_initialized"}

        # Scanner Manager
        if scanner_manager_service and production_settings.SCANNER_API_ENABLED:
            active_scanners = len(await scanner_manager_service.get_connected_scanners())
            health_status.components["scanner_manager"] = {
                "status": "healthy",
                "active_scanners": active_scanners,
                "max_scanners": production_settings.MAX_SCANNER_CLIENTS
            }

        # Audit Trail
        if audit_trail_service:
            health_status.components["audit_trail"] = audit_trail_service.get_statistics()
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


# Document processing endpoints
@app.post("/api/v1/documents/upload", response_model=DocumentUploadResponseSchema)
async def upload_document(
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Upload and process document through sophisticated pipeline"""
    try:
        if not document_processor_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Document processor service not available"
            )

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
            uploaded_by=user.get("user_id")
        )

        return DocumentUploadResponseSchema(
            document_id=result.document_id,
            status=result.status,
            message=f"Document uploaded and processing started",
            processing_time_estimate=result.estimated_processing_time
        )

    except ASRException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process document upload"
        )


@app.get("/api/v1/documents/{document_id}/status")
async def get_document_status(
    document_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get document processing status"""
    try:
        if not document_processor_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Document processor service not available"
            )

        status_info = await document_processor_service.get_document_status(
            document_id=document_id,
            tenant_id=user["tenant_id"]
        )

        return APISuccessResponseSchema(
            message="Document status retrieved",
            data=status_info
        )

    except DocumentError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Get document status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document status"
        )


@app.post("/api/v1/documents/{document_id}/classify", response_model=ClassificationResponseSchema)
async def classify_document(
    document_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Trigger document classification through sophisticated pipeline"""
    try:
        if not document_processor_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Document processor service not available"
            )

        result = await document_processor_service.classify_document(
            document_id=document_id,
            tenant_id=user["tenant_id"]
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
            quality_score=result.quality_score
        )

    except DocumentError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Document classification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to classify document"
        )


# GL Account endpoints
@app.get("/api/v1/gl-accounts")
async def list_gl_accounts(
    category: Optional[str] = None,
    search: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """List available GL accounts with filtering"""
    try:
        if not gl_account_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GL Account service not available"
            )

        accounts = gl_account_service.get_accounts(category=category, search=search)

        return APISuccessResponseSchema(
            message="GL accounts retrieved",
            data={
                "accounts": accounts,
                "total_count": len(accounts),
                "categories": gl_account_service.get_categories()
            }
        )

    except Exception as e:
        logger.error(f"List GL accounts error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve GL accounts"
        )


# Scanner API endpoints (if enabled)
if production_settings.SCANNER_API_ENABLED:

    @app.post("/api/v1/scanner/register")
    async def register_scanner(
        request: ScannerRegistrationSchema,
        user: Dict[str, Any] = Depends(get_current_user)
    ):
        """Register a new scanner client"""
        try:
            if not scanner_manager_service:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Scanner manager service not available"
                )

            result = await scanner_manager_service.register_scanner(
                scanner_name=request.scanner_name,
                tenant_id=request.tenant_id,
                api_key=request.api_key,
                capabilities=request.capabilities
            )

            return APISuccessResponseSchema(
                message="Scanner registered successfully",
                data=result
            )

        except Exception as e:
            logger.error(f"Scanner registration error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register scanner"
            )

    @app.post("/api/v1/scanner/heartbeat")
    async def scanner_heartbeat(
        request: ScannerHeartbeatSchema,
        user: Dict[str, Any] = Depends(get_current_user)
    ):
        """Process scanner heartbeat"""
        try:
            if not scanner_manager_service:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Scanner manager service not available"
                )

            await scanner_manager_service.process_heartbeat(
                scanner_id=request.scanner_id,
                status=request.status,
                queued_documents=request.queued_documents,
                metrics=request.metrics
            )

            return APISuccessResponseSchema(
                message="Heartbeat processed"
            )

        except Exception as e:
            logger.error(f"Scanner heartbeat error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process scanner heartbeat"
            )


# Error handlers
@app.exception_handler(ASRException)
async def asr_exception_handler(request, exc: ASRException):
    """Handle ASR-specific exceptions"""
    return JSONResponse(
        status_code=400,
        content=APIErrorResponseSchema(
            message=exc.message,
            errors=[exc.to_dict()]
        ).dict()
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc: ValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=422,
        content=APIErrorResponseSchema(
            message="Validation error",
            errors=[{"error_type": "ValidationError", "message": str(exc)}]
        ).dict()
    )


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "message": "Endpoint not found",
            "errors": [{"error_code": "NOT_FOUND", "error_type": "routing", "message": str(exc.detail) if hasattr(exc, 'detail') else "Not found"}],
            "timestamp": datetime.utcnow().isoformat()
        }
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
            "errors": [{"error_code": "INTERNAL_ERROR", "error_type": "server", "message": str(exc)}],
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.get("/api/status")
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
        services_status["payment_detection"] = {"status": "active", "methods": len(methods)}
    else:
        services_status["payment_detection"] = {"status": "not_initialized"}

    if billing_router_service:
        destinations = billing_router_service.get_available_destinations()
        services_status["billing_router"] = {"status": "active", "destinations": len(destinations)}
    else:
        services_status["billing_router"] = {"status": "not_initialized"}

    if storage_service:
        services_status["storage"] = {"status": "active", "backend": production_settings.STORAGE_BACKEND}
    else:
        services_status["storage"] = {"status": "not_initialized"}

    if scanner_manager_service:
        active = len(await scanner_manager_service.get_connected_scanners())
        services_status["scanner_manager"] = {"status": "active", "active_scanners": active}
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
            "claude_ai": "configured" if production_settings.ANTHROPIC_API_KEY else "not_configured"
        }
    )


# Additional endpoints for system management
@app.get("/api/v1/system/info")
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
                    "enabled": production_settings.GL_ACCOUNTS_ENABLED
                },
                "payment_detection": {
                    "methods": production_settings.PAYMENT_DETECTION_METHODS,
                    "consensus_enabled": True
                },
                "billing_router": {
                    "destinations": production_settings.BILLING_DESTINATIONS,
                    "audit_trails": production_settings.AUDIT_TRAIL_ENABLED
                },
                "multi_tenant": production_settings.MULTI_TENANT_ENABLED,
                "scanner_api": production_settings.SCANNER_API_ENABLED
            },
            "limits": {
                "max_file_size_mb": production_settings.MAX_FILE_SIZE_MB,
                "max_batch_size": production_settings.MAX_BATCH_SIZE,
                "max_scanner_clients": production_settings.MAX_SCANNER_CLIENTS
            }
        }
    )


# Legacy API info endpoint for scanner compatibility
@app.get("/api/info")
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
            "multi_tenant"
        ],
        "gl_accounts_count": 79,
        "supported_formats": ["pdf", "jpg", "jpeg", "png", "tiff", "gif"],
        "max_file_size_mb": production_settings.MAX_FILE_SIZE_MB
    }


# Enhanced Scanner API Endpoints
if production_settings.SCANNER_API_ENABLED:

    @app.get("/api/scanner/discovery")
    async def scanner_discovery():
        """Scanner server discovery endpoint"""
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
                        "batch_upload"
                    ],
                    "api_endpoints": {
                        "upload": "/api/scanner/upload",
                        "batch": "/api/scanner/batch",
                        "status": "/api/scanner/status",
                        "register": "/api/v1/scanner/register",
                        "heartbeat": "/api/v1/scanner/heartbeat"
                    },
                    "limits": {
                        "max_file_size_mb": production_settings.MAX_FILE_SIZE_MB,
                        "max_batch_size": production_settings.MAX_BATCH_SIZE,
                        "supported_formats": ["pdf", "jpg", "jpeg", "png", "tiff", "gif"]
                    },
                    "gl_accounts": {
                        "total": 79,
                        "categories": ["ASSETS", "LIABILITIES", "EQUITY", "INCOME", "EXPENSES"]
                    },
                    "payment_detection": {
                        "methods": production_settings.PAYMENT_DETECTION_METHODS,
                        "consensus_enabled": True
                    }
                }
            )
        except Exception as e:
            logger.error(f"❌ Scanner discovery failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/scanner/upload")
    async def scanner_upload(
        file: UploadFile = File(...),
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Document upload endpoint for scanner clients"""
        try:
            # Extract scanner info from form data
            form_data = {}
            if hasattr(file, 'metadata'):
                form_data['metadata'] = file.metadata
            if hasattr(file, 'scanner_info'):
                form_data['scanner_info'] = file.scanner_info

            # Get scanner ID from scanner_info or generate one
            scanner_info = form_data.get('scanner_info', {})
            scanner_id = scanner_info.get('scanner_id', 'unknown_scanner')

            # Read file content
            file_content = await file.read()

            # Create upload request
            upload_request = ScannerUploadRequest(
                scanner_id=scanner_id,
                filename=file.filename,
                file_content=file_content,
                metadata=form_data.get('metadata'),
                scanner_info=scanner_info
            )

            # Process upload
            result = await scanner_manager_service.process_scanner_upload(
                upload_request,
                document_processor_service
            )

            if result.success:
                return APISuccessResponseSchema(
                    message="Document uploaded successfully",
                    data={
                        "document_id": result.document_id,
                        "status": result.processing_status,
                        "processing_time_ms": result.processing_time_ms,
                        "classification": result.classification_result
                    }
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=result.error_message
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Scanner upload failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/scanner/status/{session_id}")
    async def get_scanner_upload_status(
        session_id: str,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Get upload status for scanner clients"""
        try:
            status = await scanner_manager_service.get_upload_status(session_id)

            if status:
                return APISuccessResponseSchema(
                    message="Upload status retrieved",
                    data=status
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Upload session not found"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Failed to get upload status: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/scanner/batch")
    async def scanner_batch_upload(
        files: List[UploadFile] = File(...),
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Batch document upload endpoint for scanner clients"""
        try:
            if len(files) > production_settings.MAX_BATCH_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"Batch size exceeds limit ({production_settings.MAX_BATCH_SIZE})"
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
                    scanner_info={"batch_upload": True}
                )
                upload_requests.append(upload_request)

            # Process batch upload
            results = await scanner_manager_service.process_batch_upload(
                scanner_id,
                upload_requests,
                document_processor_service
            )

            # Prepare response
            successful_uploads = len([r for r in results if r.success])
            response_data = {
                "batch_size": len(files),
                "successful_uploads": successful_uploads,
                "failed_uploads": len(files) - successful_uploads,
                "results": []
            }

            for i, result in enumerate(results):
                response_data["results"].append({
                    "filename": files[i].filename,
                    "success": result.success,
                    "document_id": result.document_id,
                    "error_message": result.error_message,
                    "processing_time_ms": result.processing_time_ms
                })

            return APISuccessResponseSchema(
                message=f"Batch upload completed: {successful_uploads}/{len(files)} successful",
                data=response_data
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Batch upload failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/scanner/connected")
    async def get_connected_scanners(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Get list of connected scanner clients"""
        try:
            scanners = await scanner_manager_service.get_connected_scanners()

            return APISuccessResponseSchema(
                message="Connected scanners retrieved",
                data={
                    "count": len(scanners),
                    "scanners": scanners
                }
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