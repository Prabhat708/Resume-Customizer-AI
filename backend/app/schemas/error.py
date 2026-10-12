"""app/schemas/error.py — Standardized error response envelope."""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ── Canonical error codes ───────────────────────────────────────────────────
class ErrorCode:
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    ENCRYPTED_OR_CORRUPT_FILE = "ENCRYPTED_OR_CORRUPT_FILE"
    INSUFFICIENT_TEXT_CONTENT = "INSUFFICIENT_TEXT_CONTENT"
    INVALID_JOB_DESCRIPTION = "INVALID_JOB_DESCRIPTION"
    AI_PROVIDER_ERROR = "AI_PROVIDER_ERROR"
    AI_FACTUALITY_REJECTED = "AI_FACTUALITY_REJECTED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
