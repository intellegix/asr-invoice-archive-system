"""
ASR Production Server - Prometheus Metrics Middleware
Tracks HTTP request count, duration, and in-progress gauge.
"""

import re
import time
from typing import Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

try:
    from prometheus_client import Counter, Gauge, Histogram

    _HAS_PROM = True
except ImportError:
    _HAS_PROM = False

# Path normalisation patterns — collapse dynamic IDs to {id}
_UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
_HEX_RE = re.compile(r"[0-9a-fA-F]{24,}")
_NUMERIC_RE = re.compile(r"/\d+(?=/|$)")

# Paths that should not be instrumented
SKIP_PATHS: Set[str] = {"/metrics", "/health/live", "/health/ready", "/health"}

if _HAS_PROM:
    from prometheus_client import REGISTRY

    def _get_or_create(cls, name, doc, labels):
        """Return existing collector or create new one (avoids duplicate on dual-import)."""
        existing = REGISTRY._names_to_collectors.get(name)
        if existing is not None:
            return existing
        return cls(name, doc, labels)

    asr_http_requests_total = _get_or_create(
        Counter,
        "asr_http_requests_total",
        "Total HTTP requests",
        ["method", "path_template", "status_code"],
    )
    asr_http_request_duration_seconds = _get_or_create(
        Histogram,
        "asr_http_request_duration_seconds",
        "HTTP request duration in seconds",
        ["method", "path_template"],
    )
    asr_http_requests_in_progress = _get_or_create(
        Gauge,
        "asr_http_requests_in_progress",
        "Number of in-progress HTTP requests",
        ["method"],
    )


def _normalize_path(path: str) -> str:
    """Collapse variable path segments to prevent cardinality explosion."""
    path = _UUID_RE.sub("{id}", path)
    path = _HEX_RE.sub("{id}", path)
    path = _NUMERIC_RE.sub("/{id}", path)
    return path


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that records Prometheus HTTP metrics."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if not _HAS_PROM:
            return await call_next(request)

        path = request.url.path
        if path in SKIP_PATHS:
            return await call_next(request)

        method = request.method
        path_template = _normalize_path(path)

        asr_http_requests_in_progress.labels(method=method).inc()
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            asr_http_requests_total.labels(
                method=method, path_template=path_template, status_code=500
            ).inc()
            raise
        finally:
            duration = time.perf_counter() - start
            asr_http_requests_in_progress.labels(method=method).dec()

        asr_http_requests_total.labels(
            method=method, path_template=path_template, status_code=response.status_code
        ).inc()
        asr_http_request_duration_seconds.labels(
            method=method, path_template=path_template
        ).observe(duration)

        return response
