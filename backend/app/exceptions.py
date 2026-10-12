"""app/exceptions.py — Standardized application and document parsing exceptions.

All domain exceptions inherit from DocumentValidationError and provide canonical
error codes and HTTP status codes conforming to the standard ErrorResponse schema.
"""
from __future__ import annotations

from typing import Any, Optional
from app.schemas.error import ErrorCode


class DocumentValidationError(Exception):
    """Base class for all document validation and parsing errors."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


class InvalidFileTypeError(DocumentValidationError):
    """Raised when file extension or magic bytes do not match supported document types (.pdf, .docx)."""

    def __init__(
        self,
        message: str = "Invalid file type. Only PDF (.pdf) and Word (.docx) documents are supported.",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            code=ErrorCode.INVALID_FILE_TYPE,
            message=message,
            status_code=400,
            details=details,
        )


class FileTooLargeError(DocumentValidationError):
    """Raised when file size exceeds the configured maximum upload limit."""

    def __init__(
        self,
        message: str = "Uploaded file exceeds the maximum allowed size limit.",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            code=ErrorCode.FILE_TOO_LARGE,
            message=message,
            status_code=413,
            details=details,
        )


class EmptyFileError(DocumentValidationError):
    """Raised when the uploaded file contains 0 bytes."""

    def __init__(
        self,
        message: str = "The uploaded file is empty (0 bytes).",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            code=ErrorCode.ENCRYPTED_OR_CORRUPT_FILE,
            message=message,
            status_code=400,
            details=details,
        )


class EncryptedOrCorruptFileError(DocumentValidationError):
    """Raised when document is corrupted, password-protected, encrypted, or cannot be parsed."""

    def __init__(
        self,
        message: str = "The document is password-protected, encrypted, or corrupted.",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            code=ErrorCode.ENCRYPTED_OR_CORRUPT_FILE,
            message=message,
            status_code=422,
            details=details,
        )


class InsufficientTextContentError(DocumentValidationError):
    """Raised when document yields insufficient or sparse readable text (e.g., scanned image PDF)."""

    def __init__(
        self,
        message: str = (
            "The document contains insufficient readable text. "
            "Please upload a text-based resume (not a scanned image or photo)."
        ),
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            code=ErrorCode.INSUFFICIENT_TEXT_CONTENT,
            message=message,
            status_code=422,
            details=details,
        )
