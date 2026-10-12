"""app/main.py — FastAPI application entrypoint.

Registers:
- CORS middleware (origins from config, never hardcoded).
- Standardized error response handlers.
- All API routers under the /api/v1 prefix.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.exceptions import DocumentValidationError
from app.routers import health, resume
from app.schemas.error import ErrorCode, ErrorDetail, ErrorResponse

settings = get_settings()

app = FastAPI(
    title="Resume Customizer API",
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept"],
)


# ── Global exception handlers ─────────────────────────────────────────────────
@app.exception_handler(DocumentValidationError)
async def document_validation_exception_handler(
    request: Request, exc: DocumentValidationError
) -> JSONResponse:
    """Standardized handler for domain validation and document parsing errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                details=exc.details,
            )
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Standardized handler for request validation failures (e.g. missing file)."""
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.INVALID_FILE_TYPE,
                message="Invalid request payload or missing required file parameter.",
                details=exc.errors(),
            )
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler that never leaks internal details to the client."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.INTERNAL_ERROR,
                message="An unexpected server error occurred. Please try again later.",
            )
        ).model_dump(),
    )


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(resume.router, prefix="/api/v1/resume", tags=["resume"])
