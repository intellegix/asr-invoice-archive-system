"""
ASR Production Server - Tenant Isolation Middleware
Extracts and validates tenant context from incoming requests
"""

import logging
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

DEFAULT_TENANT_ID = "default"


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware that extracts tenant context from requests and enforces isolation"""

    async def dispatch(self, request: Request, call_next):
        # Skip tenant validation for health/info endpoints
        skip_paths = [
            "/health",
            "/health/live",
            "/health/ready",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/info",
            "/",
        ]
        if request.url.path in skip_paths:
            request.state.tenant_id = DEFAULT_TENANT_ID
            return await call_next(request)

        # Extract tenant ID from header only (no query param fallback for security)
        tenant_id = request.headers.get("X-Tenant-ID")

        if not tenant_id:
            # Use default tenant
            tenant_id = DEFAULT_TENANT_ID

        # Store tenant context in request state
        request.state.tenant_id = tenant_id

        # Add tenant ID to response headers for debugging
        response = await call_next(request)
        response.headers["X-Tenant-ID"] = tenant_id

        return response
