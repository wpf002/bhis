"""
Consistent error shape across the API: every error response is
``{"detail": ..., "code": ..., "field"?: ...}`` (Phase 1 DoD).

- HTTPException → {detail, code} where code is a machine-readable slug.
- RequestValidationError (422) → {detail, code: "validation_error", field, errors}.
"""
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

_STATUS_CODE_SLUG = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "validation_error",
    429: "rate_limited",
    500: "internal_error",
    501: "not_implemented",
}


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": _STATUS_CODE_SLUG.get(exc.status_code, "error")},
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    field = None
    if errors:
        loc = [p for p in errors[0].get("loc", []) if p != "body"]
        field = loc[-1] if loc else None
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "code": "validation_error",
            "field": field,
            "errors": jsonable_encoder(errors),
        },
    )


def register_error_handlers(app) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
