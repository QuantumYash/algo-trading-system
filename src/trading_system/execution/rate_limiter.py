
import asyncio
import time


class AsyncRateLimiter:
    """Simple async rate limiter."""

    def __init__(
        self,
        max_calls: int,
        period_seconds: float,
    ) -> None:
        if max_calls <= 0:
            raise ValueError("max_calls must be positive.")

        if period_seconds <= 0:
            raise ValueError("period_seconds must be positive.")

        self._max_calls = max_calls
        self._period = period_seconds
        self._timestamps: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                now = time.monotonic()

                self._timestamps = [
                    timestamp
                    for timestamp in self._timestamps
                    if now - timestamp < self._period
                ]

                if len(self._timestamps) < self._max_calls:
                    self._timestamps.append(now)
                    return

                wait_time = self._period - (
                    now - self._timestamps[0]
                )

            await asyncio.sleep(wait_time)