"""
ASR Production Server - Rate Limiting Middleware
Supports in-memory (default) and Redis-backed sliding window rate limiting.
"""

import logging
import time
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

MAX_TRACKED_CLIENTS = 10_000


class _MemoryBackend:
    """In-memory sliding window rate limit backend."""

    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period
        self.clients: OrderedDict[str, List[float]] = OrderedDict()
        self._cleanup_counter = 0

    def _cleanup(self) -> None:
        now = time.time()
        window_start = now - self.period
        expired_keys = [
            k for k, ts in self.clients.items() if not ts or ts[-1] <= window_start
        ]
        for k in expired_keys:
            del self.clients[k]
        while len(self.clients) > MAX_TRACKED_CLIENTS:
            self.clients.popitem(last=False)

    def is_rate_limited(self, client_id: str) -> Tuple[bool, int]:
        now = time.time()
        window_start = now - self.period

        self._cleanup_counter += 1
        if self._cleanup_counter >= 100:
            self._cleanup_counter = 0
            self._cleanup()

        timestamps = self.clients.get(client_id, [])
        timestamps = [t for t in timestamps if t > window_start]

        request_count = len(timestamps)
        if request_count >= self.calls:
            self.clients[client_id] = timestamps
            self.clients.move_to_end(client_id)
            return True, self.calls - request_count

        timestamps.append(now)
        self.clients[client_id] = timestamps
        self.clients.move_to_end(client_id)
        return False, self.calls - request_count - 1


class _RedisBackend:
    """Redis-backed sliding window rate limit backend."""

    def __init__(self, calls: int, period: int, redis_url: str):
        import redis

        self.calls = calls
        self.period = period
        self._prefix = "asr:ratelimit:"
        self._redis = redis.Redis.from_url(redis_url, decode_responses=True)
        logger.info("Rate limiter using Redis backend at %s", redis_url)

    def is_rate_limited(self, client_id: str) -> Tuple[bool, int]:
        import redis as _redis_mod  # noqa: F811

        key = f"{self._prefix}{client_id}"
        now = time.time()
        window_start = now - self.period

        pipe = self._redis.pipeline(transaction=True)
        try:
            pipe.zremrangebyscore(key, "-inf", window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, self.period)
            results = pipe.execute()
        except _redis_mod.RedisError as e:
            logger.warning("Redis error in rate limiter, allowing request: %s", e)
            return False, self.calls

        request_count = results[1]  # zcard result
        if request_count >= self.calls:
            return True, 0
        return False, self.calls - request_count - 1


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter with pluggable backend (memory or redis)."""

    def __init__(
        self,
        app,
        calls: int = 100,
        period: int = 60,
        backend: str = "memory",
        redis_url: Optional[str] = None,
    ):
        super().__init__(app)
        self.calls = calls
        self.period = period

        if backend == "redis" and redis_url:
            self._backend = _RedisBackend(calls, period, redis_url)
        else:
            if backend == "redis" and not redis_url:
                logger.warning(
                    "RATE_LIMIT_BACKEND=redis but REDIS_URL not set, falling back to memory"
                )
            self._backend = _MemoryBackend(calls, period)

    @staticmethod
    def _get_client_id(request: Request) -> str:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return f"key:{auth_header[7:20]}"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        client = request.client
        return f"ip:{client.host}" if client else "ip:unknown"

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/health", "/"]:
            return await call_next(request)

        client_id = self._get_client_id(request)
        is_limited, remaining = self._backend.is_rate_limited(client_id)

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
