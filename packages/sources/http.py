"""Shared HTTP utilities for source plugins.

Provides rate limiting, resilient requests with retry/backoff, and a
configured httpx client factory.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()

USER_AGENT = "Atlas/0.1.0 (research intelligence platform; mailto:atlas@localhost)"


class RateLimiter:
    """Async rate limiter with configurable requests-per-second."""

    def __init__(self, requests_per_second: float = 1.0) -> None:
        self._min_interval = 1.0 / requests_per_second
        self._last_request = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = self._min_interval - (now - self._last_request)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request = time.monotonic()


class CircuitBreaker:
    """Simple circuit breaker: opens after N consecutive failures, resets after cooldown."""

    def __init__(self, failure_threshold: int = 5, cooldown_seconds: float = 60.0) -> None:
        self._failure_threshold = failure_threshold
        self._cooldown = cooldown_seconds
        self._failures = 0
        self._opened_at: float | None = None

    @property
    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if time.monotonic() - self._opened_at > self._cooldown:
            self._opened_at = None
            self._failures = 0
            return False
        return True

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self._failure_threshold:
            self._opened_at = time.monotonic()


def create_client(timeout: float = 30.0, **kwargs: Any) -> httpx.AsyncClient:
    """Create an httpx.AsyncClient with standard Atlas headers."""
    return httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        timeout=httpx.Timeout(timeout),
        follow_redirects=True,
        **kwargs,
    )


async def resilient_get(
    client: httpx.AsyncClient,
    url: str,
    rate_limiter: RateLimiter | None = None,
    circuit_breaker: CircuitBreaker | None = None,
    max_retries: int = 5,
    backoff_base: float = 1.0,
    **kwargs: Any,
) -> httpx.Response:
    """GET with rate limiting, exponential backoff, and circuit breaker.

    Raises httpx.HTTPStatusError on non-retryable errors.
    Raises RuntimeError if circuit breaker is open.
    """
    if circuit_breaker and circuit_breaker.is_open:
        raise RuntimeError(f"Circuit breaker open for {url}")

    if rate_limiter:
        await rate_limiter.acquire()

    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            resp = await client.get(url, **kwargs)

            # Retry on 429 and 5xx
            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", backoff_base * (2**attempt)))
                logger.warning("rate_limited", url=url, retry_after=retry_after)
                await asyncio.sleep(retry_after)
                continue
            if resp.status_code >= 500:
                logger.warning("server_error", url=url, status=resp.status_code, attempt=attempt)
                await asyncio.sleep(backoff_base * (2**attempt))
                continue

            resp.raise_for_status()
            if circuit_breaker:
                circuit_breaker.record_success()
            return resp

        except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            last_error = e
            logger.warning("http_error", url=url, error=str(e), attempt=attempt)
            await asyncio.sleep(backoff_base * (2**attempt))

    if circuit_breaker:
        circuit_breaker.record_failure()
    raise last_error or RuntimeError(f"Failed to GET {url} after {max_retries} retries")
