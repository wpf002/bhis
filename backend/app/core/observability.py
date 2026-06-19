"""
Observability: optional Sentry init + a structured request-logging/timing
middleware. Both are no-ops when unconfigured, so dev/test stay quiet.
"""
import logging
import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = logging.getLogger("bhis.request")

# Process start, for /health uptime. time.time() is fine in app code.
START_TIME = time.time()


def init_sentry() -> None:
    """Initialise Sentry if a DSN is configured and the SDK is installed."""
    if not settings.SENTRY_DSN:
        return
    try:
        import sentry_sdk  # optional dependency
        sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.ENVIRONMENT, traces_sample_rate=0.0)
        logger.info("Sentry initialised")
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Sentry init skipped: %s", exc)


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Log every request with timing, and flag slow ones. Enriches with
    user_id/church_id if a dependency set them on request.state."""

    async def dispatch(self, request, call_next):
        request_id = uuid4().hex[:12]
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        fields = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration_ms, 1),
            "user_id": getattr(request.state, "user_id", None),
            "church_id": getattr(request.state, "church_id", None),
        }
        if duration_ms > settings.SLOW_REQUEST_MS:
            logger.warning("slow request %s", fields)
        else:
            logger.info("request %s", fields)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-ms"] = f"{duration_ms:.1f}"
        return response
