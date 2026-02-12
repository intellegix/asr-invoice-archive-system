"""
ASR Production Server - Request Logging Middleware
Adds correlation IDs and structured request/response logging for production observability.
"""

import logging
import time
import uuid
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("asr.requests")

SKIP_LOGGING_PATHS = frozenset({"/health/live"})


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that assigns a correlation ID to every request and logs request/response."""

    def __init__(self, app, log_format: str = "text"):
        super().__init__(app)
        self.log_format = log_format

    async def dispatch(self, request: Request, call_next) -> Response:
        # Use caller-provided ID or generate one
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        path = request.url.path
        method = request.method

        # Skip noisy health-check logging
        if path in SKIP_LOGGING_PATHS:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

        client_ip = _get_client_ip(request)
        start_time = time.perf_counter()

        logger.info(
            "request_started",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "client_ip": client_ip,
                "user_agent": request.headers.get("User-Agent", ""),
            },
        )

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "duration_ms": round(duration_ms, 2),
                },
                exc_info=True,
            )
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
        logger.log(
            log_level,
            "request_completed",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": client_ip,
            },
        )

        return response


def _get_client_ip(request: Request) -> str:
    """Extract client IP from X-Forwarded-For or connection info."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = request.client
    return client.host if client else "unknown"
