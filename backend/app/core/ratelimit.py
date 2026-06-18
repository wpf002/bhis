"""
Minimal fixed-window rate limiter.

In-process and per-worker — fine for the pilot's single backend process. For
multi-worker production, swap the in-memory store for Redis (already a dependency)
behind the same RateLimiter.check() interface.

Usage:
    login_limiter = RateLimiter("login", limit=10, window=60)

    @router.post("/login", dependencies=[Depends(rate_limit(login_limiter))])
    ...
"""
import time
from typing import Callable, Dict, List, Optional, Tuple

from fastapi import HTTPException, Request, status


class RateLimiter:
    # All instances register here so tests can reset state between cases.
    _registry: List["RateLimiter"] = []

    def __init__(self, name: str, limit: int, window: int):
        self.name = name
        self.limit = limit
        self.window = window
        self._hits: Dict[str, Tuple[float, int]] = {}  # key -> (window_start, count)
        RateLimiter._registry.append(self)

    def check(self, key: str, now: Optional[float] = None) -> None:
        now = time.time() if now is None else now
        window_start, count = self._hits.get(key, (now, 0))
        if now - window_start >= self.window:
            window_start, count = now, 0
        count += 1
        self._hits[key] = (window_start, count)
        if count > self.limit:
            retry_after = int(self.window - (now - window_start))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(max(retry_after, 1))},
            )

    def reset(self) -> None:
        self._hits.clear()


def reset_all() -> None:
    for limiter in RateLimiter._registry:
        limiter.reset()


def rate_limit(limiter: RateLimiter) -> Callable:
    """Build a FastAPI dependency that enforces ``limiter`` keyed by client IP."""
    async def dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "anon"
        limiter.check(f"{limiter.name}:{client_ip}")

    return dependency
