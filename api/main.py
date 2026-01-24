"""
ASR Invoice Archive System - FastAPI Main Application
Production-ready web service for document processing and archiving
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import application modules
try:
    from config.settings import Settings
    from services.storage_service import get_storage_backend
    from models.database import init_db, get_session
except ImportError as e:
    # Fallback for minimal deployment
    logging.warning(f"Import error: {e}. Running in minimal mode.")
    Settings = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize settings
settings = Settings() if Settings else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting ASR Invoice Archive System...")

    # Initialize database if available
    if settings:
        try:
            init_db(settings.DATABASE_URL)
            logger.info("✅ Database initialized successfully")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")

    yield

    logger.info("🛑 Shutting down ASR Invoice Archive System...")


# Initialize FastAPI application
app = FastAPI(
    title="ASR Invoice Archive System",
    description="Enterprise document processing and archiving system",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {
        "message": "ASR Invoice Archive System",
        "status": "online",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "service": "ASR Invoice Archive System",
        "version": "1.0.0",
        "checks": {}
    }

    # Check environment
    health_status["environment"] = {
        "render": os.getenv("RENDER", "false").lower() == "true",
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
    }

    # Check database connectivity if available
    if settings and hasattr(settings, 'DATABASE_URL'):
        try:
            session = get_session()
            session.execute("SELECT 1")
            session.close()
            health_status["checks"]["database"] = "connected"
        except Exception as e:
            health_status["checks"]["database"] = f"error: {str(e)}"
            health_status["status"] = "unhealthy"
    else:
        health_status["checks"]["database"] = "not_configured"

    # Check Claude AI service if available
    if settings and hasattr(settings, 'ANTHROPIC_API_KEY'):
        try:
            if settings.ANTHROPIC_API_KEY:
                health_status["checks"]["claude_api"] = "configured"
            else:
                health_status["checks"]["claude_api"] = "not_configured"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["checks"]["claude_api"] = f"error: {str(e)}"
    else:
        health_status["checks"]["claude_api"] = "not_configured"

    # Check storage backend if available
    try:
        storage = get_storage_backend()
        if storage:
            health_status["checks"]["storage"] = "configured"
        else:
            health_status["checks"]["storage"] = "not_configured"
    except Exception as e:
        health_status["checks"]["storage"] = f"error: {str(e)}"

    # Check persistent disk mount (Render specific)
    if os.getenv("RENDER") == "true":
        data_mount = os.getenv("RENDER_DISK_MOUNT", "/data")
        if os.path.exists(data_mount) and os.access(data_mount, os.W_OK):
            health_status["checks"]["persistent_disk"] = "mounted_writable"
        elif os.path.exists(data_mount):
            health_status["checks"]["persistent_disk"] = "mounted_readonly"
        else:
            health_status["checks"]["persistent_disk"] = "not_mounted"

    return health_status


@app.get("/api/status")
async def api_status() -> Dict[str, Any]:
    """API status endpoint for monitoring"""
    return {
        "api_status": "operational",
        "endpoints_available": [
            "/",
            "/health",
            "/api/status"
        ],
        "timestamp": "2026-01-19T22:30:00Z"
    }


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "detail": "The requested endpoint does not exist"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "An unexpected error occurred"}
    )


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))

    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)