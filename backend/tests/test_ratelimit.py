"""Unit tests for the fixed-window rate limiter (no DB, no HTTP)."""
import pytest
from fastapi import HTTPException

from app.core.ratelimit import RateLimiter, reset_all


def test_allows_up_to_limit():
    rl = RateLimiter("t1", limit=3, window=60)
    for _ in range(3):
        rl.check("ip", now=100.0)  # same window


def test_blocks_over_limit():
    rl = RateLimiter("t2", limit=2, window=60)
    rl.check("ip", now=100.0)
    rl.check("ip", now=100.5)
    with pytest.raises(HTTPException) as exc:
        rl.check("ip", now=101.0)
    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers


def test_window_resets():
    rl = RateLimiter("t3", limit=1, window=60)
    rl.check("ip", now=100.0)
    with pytest.raises(HTTPException):
        rl.check("ip", now=110.0)  # same window
    rl.check("ip", now=200.0)  # new window, allowed again


def test_keys_are_independent():
    rl = RateLimiter("t4", limit=1, window=60)
    rl.check("a", now=100.0)
    rl.check("b", now=100.0)  # different key, not blocked


def test_reset_all_clears_state():
    rl = RateLimiter("t5", limit=1, window=60)
    rl.check("ip", now=100.0)
    reset_all()
    rl.check("ip", now=100.0)  # allowed again after reset
