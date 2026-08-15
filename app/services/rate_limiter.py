"""
services/rate_limiter.py
─────────────────────────
Sliding-window rate limiter for the DM send endpoint.
Limit: 10 requests per rolling 60 seconds (per the mock API spec).

Usage:
    limiter = RateLimiter()
    await limiter.acquire()   # blocks until a slot is available
"""
import asyncio
import time
from collections import deque

from app.config import RATE_LIMIT_MAX, RATE_LIMIT_WINDOW


class RateLimiter:
    """
    Token-bucket / sliding-window hybrid.
    Tracks the timestamps of the last N sends and blocks until
    the oldest one is outside the rolling window.
    """

    def __init__(
        self,
        max_calls: int = RATE_LIMIT_MAX,
        window: float = RATE_LIMIT_WINDOW,
    ):
        self._max_calls = max_calls
        self._window = window
        self._calls: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Wait until there is capacity to make one more request."""
        async with self._lock:
            while True:
                now = time.monotonic()
                # Evict timestamps outside the window
                while self._calls and now - self._calls[0] >= self._window:
                    self._calls.popleft()

                if len(self._calls) < self._max_calls:
                    self._calls.append(now)
                    return

                # Must wait until the oldest call leaves the window
                wait_for = self._window - (now - self._calls[0]) + 0.05  # 50ms buffer
                await asyncio.sleep(wait_for)

    def record_429(self, retry_after: float):
        """
        Called when the API returns 429.  We immediately block the limiter
        for `retry_after` seconds by filling up the window with phantom entries.
        """
        now = time.monotonic()
        # Fill the deque so no slot is free until retry_after expires
        while len(self._calls) < self._max_calls:
            self._calls.appendleft(now - self._window + retry_after)


# Module-level singleton shared by the worker
rate_limiter = RateLimiter()
