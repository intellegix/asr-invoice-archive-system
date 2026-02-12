"""
ASR Production Server - Rate Limiting Middleware
Simple in-memory rate limiter for API request throttling
"""

import logging
import time
from collections import OrderedDict
from typing import Dict, List, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

MAX_TRACKED_CLIENTS = 10_000


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple sliding window rate limiter with bounded memory"""

    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: OrderedDict[str, List[float]] = OrderedDict()
        self._cleanup_counter = 0

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request"""
        # Use API key if available, otherwise use IP
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return f"key:{auth_header[7:20]}"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        client = request.client
        return f"ip:{client.host}" if client else "ip:unknown"

    def _cleanup(self) -> None:
        """Evict expired entries and enforce max client cap."""
        now = time.time()
        window_start = now - self.period

        # Remove entries with no recent timestamps
        expired_keys = [
            k for k, ts in self.clients.items() if not ts or ts[-1] <= window_start
        ]
        for k in expired_keys:
            del self.clients[k]

        # LRU eviction if over cap
        while len(self.clients) > MAX_TRACKED_CLIENTS:
            self.clients.popitem(last=False)

    def _is_rate_limited(self, client_id: str) -> Tuple[bool, int]:
        """Check if client is rate limited"""
        now = time.time()
        window_start = now - self.period

        # Amortized cleanup every 100 requests
        self._cleanup_counter += 1
        if self._cleanup_counter >= 100:
            self._cleanup_counter = 0
            self._cleanup()

        # Get or create timestamps list
        timestamps = self.clients.get(client_id, [])

        # Clean old entries for this client
        timestamps = [t for t in timestamps if t > window_start]

        # Check limit
        request_count = len(timestamps)
        if request_count >= self.calls:
            self.clients[client_id] = timestamps
            # Move to end (most recently accessed)
            self.clients.move_to_end(client_id)
            return True, self.calls - request_count

        # Record request
        timestamps.append(now)
        self.clients[client_id] = timestamps
        self.clients.move_to_end(client_id)
        return False, self.calls - request_count - 1

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/"]:
            return await call_next(request)

        client_id = self._get_client_id(request)
        is_limited, remaining = self._is_rate_limited(client_id)

        if is_limited:
            return JSONResponse(
                status_code=429,
                content={"message": "Rate limit exceeded", "retry_after": self.period},
                headers={
                    "Retry-After": str(self.period),
                    "X-RateLimit-Limit": str(self.calls),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
