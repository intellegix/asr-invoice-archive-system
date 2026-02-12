"""
Tests for async_retry decorator and CircuitBreaker.
"""

import asyncio
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "production-server"))
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from production_server.utils.retry import CircuitBreaker, async_retry

# ---------------------------------------------------------------------------
# async_retry tests
# ---------------------------------------------------------------------------


class TestAsyncRetry:
    """Tests for the async_retry decorator."""

    @pytest.mark.asyncio
    async def test_succeeds_first_try(self):
        call_count = 0

        @async_retry(max_attempts=3, backoff_seconds=(0.0, 0.0))
        async def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await succeed()
        assert result == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_failure(self):
        call_count = 0

        @async_retry(max_attempts=3, backoff_seconds=(0.0, 0.0))
        async def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "done"

        result = await fail_twice()
        assert result == "done"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_attempts(self):
        call_count = 0

        @async_retry(max_attempts=2, backoff_seconds=(0.0,))
        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            await always_fail()
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_only_retries_matching_exceptions(self):
        call_count = 0

        @async_retry(
            max_attempts=3,
            backoff_seconds=(0.0,),
            retryable_exceptions=(ValueError,),
        )
        async def raise_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("wrong type")

        with pytest.raises(TypeError, match="wrong type"):
            await raise_type_error()
        # Should NOT retry because TypeError is not in retryable_exceptions
        assert call_count == 1


# ---------------------------------------------------------------------------
# CircuitBreaker tests
# ---------------------------------------------------------------------------


class TestCircuitBreaker:
    """Tests for the CircuitBreaker."""

    def test_starts_closed(self):
        cb = CircuitBreaker(failure_threshold=3, reset_timeout=10.0)
        assert cb.state == CircuitBreaker.CLOSED
        assert not cb.is_open

    def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3, reset_timeout=10.0)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitBreaker.OPEN
        assert cb.is_open

    def test_success_resets_count(self):
        cb = CircuitBreaker(failure_threshold=3, reset_timeout=10.0)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        cb.record_failure()
        # Should still be closed — success reset the counter
        assert cb.state == CircuitBreaker.CLOSED

    def test_transitions_to_half_open(self):
        cb = CircuitBreaker(failure_threshold=2, reset_timeout=0.0)
        cb.record_failure()
        cb.record_failure()
        # With reset_timeout=0, it transitions to half_open on the next state check
        assert cb.state == CircuitBreaker.HALF_OPEN

    def test_reset(self):
        cb = CircuitBreaker(failure_threshold=2, reset_timeout=10.0)
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open
        cb.reset()
        assert cb.state == CircuitBreaker.CLOSED
        assert not cb.is_open
