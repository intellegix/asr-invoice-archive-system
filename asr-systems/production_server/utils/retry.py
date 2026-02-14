"""
ASR Production Server - Retry & Circuit Breaker Utilities
Async retry decorator with exponential backoff + simple circuit breaker.
"""

import asyncio
import functools
import logging
import time
from typing import Callable, Sequence, Tuple, Type

logger = logging.getLogger(__name__)


def async_retry(
    max_attempts: int = 3,
    backoff_seconds: Tuple[float, ...] = (1.0, 2.0, 4.0),
    retryable_exceptions: Sequence[Type[BaseException]] = (Exception,),
) -> Callable:
    """Decorator that retries an async function with exponential backoff.

    Args:
        max_attempts: Total number of attempts (1 = no retry).
        backoff_seconds: Sleep duration between retries (index = attempt - 1).
                         If fewer entries than retries, the last value is reused.
        retryable_exceptions: Exception types that should trigger a retry.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc: BaseException | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except tuple(retryable_exceptions) as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        logger.warning(
                            "retry_exhausted func=%s attempts=%d error=%s",
                            func.__qualname__,
                            max_attempts,
                            exc,
                        )
                        raise
                    delay_idx = min(attempt - 1, len(backoff_seconds) - 1)
                    delay = backoff_seconds[delay_idx]
                    logger.info(
                        "retry_attempt func=%s attempt=%d/%d delay=%.1fs error=%s",
                        func.__qualname__,
                        attempt,
                        max_attempts,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
            # Unreachable, but keeps mypy happy
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator


class CircuitBreaker:
    """Simple circuit breaker that opens after consecutive failures.

    States:
        CLOSED  — requests pass through.
        OPEN    — requests are rejected immediately for ``reset_timeout`` seconds.
        HALF_OPEN — one probe request is allowed; success closes, failure re-opens.
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(self, failure_threshold: int = 5, reset_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._state = self.CLOSED
        self._failure_count = 0
        self._opened_at: float = 0.0

    @property
    def state(self) -> str:
        if self._state == self.OPEN:
            if time.monotonic() - self._opened_at >= self.reset_timeout:
                self._state = self.HALF_OPEN
        return self._state

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = self.CLOSED

    def record_failure(self) -> None:
        self._failure_count += 1
        if self._failure_count >= self.failure_threshold:
            self._state = self.OPEN
            self._opened_at = time.monotonic()
            logger.warning(
                "circuit_breaker_opened failures=%d threshold=%d",
                self._failure_count,
                self.failure_threshold,
            )

    @property
    def is_open(self) -> bool:
        return self.state == self.OPEN

    def reset(self) -> None:
        self._failure_count = 0
        self._state = self.CLOSED
        self._opened_at = 0.0
