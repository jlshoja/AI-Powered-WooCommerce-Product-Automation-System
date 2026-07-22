"""
Rate Limiter for the WooCommerce Product Automation System.

Implements token bucket algorithm for rate limiting API requests.
"""

import time
import threading
from typing import Optional


class TokenBucketRateLimiter:
    """Token bucket rate limiter for API requests."""

    def __init__(self, rate: float, burst: int = 1):
        """
        Initialize the rate limiter.

        Args:
            rate: Requests per second (e.g., 1.0 for 1 req/sec)
            burst: Maximum burst size (tokens in bucket)
        """
        self.rate = rate
        self.burst = burst
        self._tokens = float(burst)
        self._last_update = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait in seconds (None = wait indefinitely)

        Returns:
            True if tokens acquired, False if timeout
        """
        start_time = time.monotonic()
        while True:
            with self._lock:
                now = time.monotonic()
                elapsed = now - self._last_update
                self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
                self._last_update = now

                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True

            if timeout is not None:
                elapsed_total = time.monotonic() - start_time
                if elapsed_total >= timeout:
                    return False

            # Sleep a small amount to avoid busy waiting
            time.sleep(0.01)

    def try_acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without blocking.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens acquired, False otherwise
        """
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_update
            self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
            self._last_update = now

            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def get_available_tokens(self) -> float:
        """Get the current number of available tokens."""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_update
            self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
            self._last_update = now
            return self._tokens


class RateLimiter:
    """Rate limiter with configurable limits per endpoint."""

    def __init__(
        self,
        default_rate: float = 1.0,
        default_burst: int = 1,
        endpoint_limits: dict[str, tuple[float, int]] = None,
    ):
        """
        Initialize the rate limiter.

        Args:
            default_rate: Default requests per second
            default_burst: Default burst size
            endpoint_limits: Dict of endpoint -> (rate, burst) overrides
        """
        self.default_rate = default_rate
        self.default_burst = default_burst
        self.endpoint_limits = endpoint_limits or {}
        self._limiters: dict[str, TokenBucketRateLimiter] = {}
        self._lock = threading.Lock()

    def _get_limiter(self, endpoint: str) -> TokenBucketRateLimiter:
        """Get or create a rate limiter for an endpoint."""
        with self._lock:
            if endpoint not in self._limiters:
                rate, burst = self.endpoint_limits.get(endpoint, (self.default_rate, self.default_burst))
                self._limiters[endpoint] = TokenBucketRateLimiter(rate, burst)
            return self._limiters[endpoint]

    def acquire(self, endpoint: str, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """Acquire tokens for an endpoint."""
        limiter = self._get_limiter(endpoint)
        return limiter.acquire(tokens, timeout)

    def try_acquire(self, endpoint: str, tokens: int = 1) -> bool:
        """Try to acquire tokens without blocking."""
        limiter = self._get_limiter(endpoint)
        return limiter.try_acquire(tokens)