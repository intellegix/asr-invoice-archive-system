"""
ASR Production Server - CSRF Protection Middleware
Double-submit cookie pattern: the server sets a random CSRF token in a
cookie; the client must echo it back in the X-CSRF-Token header on every
state-changing request (POST/PUT/DELETE/PATCH).
"""

import logging
import secrets
from typing import Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"
SAFE_METHODS: Set[str] = {"GET", "HEAD", "OPTIONS"}

# Paths that are exempt from CSRF checks (public/auth endpoints)
CSRF_EXEMPT_PATHS: Set[str] = {
    "/health",
    "/",
    "/auth/login",
    "/api/info",
    "/api/status",
    "/api/scanner/discovery",
    "/api/v1/system/info",
}


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF protection."""

    def __init__(self, app, enabled: bool = True, secure: bool = False):
        super().__init__(app)
        self.enabled = enabled
        self.secure = secure

    @staticmethod
    def _generate_token() -> str:
        return secrets.token_hex(32)

    @staticmethod
    def _is_exempt(path: str) -> bool:
        return (
            path in CSRF_EXEMPT_PATHS
            or path.startswith("/docs")
            or path.startswith("/redoc")
        )

    def _set_csrf_cookie(self, response: Response, token: str) -> None:
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=token,
            httponly=False,  # JS must be able to read it
            samesite="lax",
            secure=self.secure,
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.enabled:
            return await call_next(request)

        # Always ensure a CSRF cookie exists
        csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
        new_token = None
        if not csrf_cookie:
            new_token = self._generate_token()
            csrf_cookie = new_token

        # Safe methods and exempt paths skip validation
        if request.method in SAFE_METHODS or self._is_exempt(request.url.path):
            response = await call_next(request)
            if new_token:
                self._set_csrf_cookie(response, new_token)
            return response

        # State-changing request: validate header matches cookie
        csrf_header = request.headers.get(CSRF_HEADER_NAME)
        if not csrf_header or csrf_header != csrf_cookie:
            logger.warning(
                "CSRF validation failed for %s %s from %s",
                request.method,
                request.url.path,
                request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                status_code=403,
                content={"message": "CSRF token missing or invalid"},
            )

        response = await call_next(request)
        if new_token:
            self._set_csrf_cookie(response, new_token)
        return response
