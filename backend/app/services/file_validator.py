"""app/services/file_validator.py — File validation and magic-byte verification service.

Validates:
- File extension matches supported types (.pdf, .docx).
- Actual file byte signature (magic bytes) matches declared type (prevents spoofing).
- Upload size does not exceed the configured maximum.
- Empty files (0 bytes) are rejected.
- Corrupted archives / containers are rejected.

NEVER logs file contents, candidate identities, or sensitive personal data.
"""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Optional
import zipfile

from app.exceptions import (
    EmptyFileError,
    EncryptedOrCorruptFileError,
    FileTooLargeError,
    InvalidFileTypeError,
)

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
PDF_MAGIC_BYTES = b"%PDF-"
ZIP_MAGIC_BYTES = b"PK\x03\x04"


def validate_file(
    content: bytes,
    filename: Optional[str],
    max_size_bytes: int,
    max_size_mb: int,
) -> str:
    """Validate uploaded document bytes and filename.

    Args:
        content: Raw bytes of the uploaded file.
        filename: Original filename provided in the upload request.
        max_size_bytes: Maximum allowed file size in bytes.
        max_size_mb: Maximum allowed file size in MB (used for user-friendly error messages).

    Returns:
        The validated canonical document format string: "pdf" or "docx".

    Raises:
        EmptyFileError: When content is 0 bytes.
        FileTooLargeError: When content exceeds max_size_bytes.
        InvalidFileTypeError: When extension or magic bytes are unsupported/mismatched.
        EncryptedOrCorruptFileError: When container format is structurally corrupt.
    """
    # 1. Filename presence and extension check
    if not filename or not filename.strip():
        raise InvalidFileTypeError("A valid filename with extension (.pdf or .docx) must be provided.")

    clean_name = filename.strip()
    ext = Path(clean_name).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise InvalidFileTypeError(
            f"Unsupported file format '{ext or 'unknown'}'. Only .pdf and .docx documents are supported."
        )

    # 2. File size enforcement
    size_bytes = len(content)
    if size_bytes == 0:
        raise EmptyFileError("The uploaded file is empty (0 bytes). Please upload a valid document.")

    if size_bytes > max_size_bytes:
        size_mb_actual = size_bytes / (1024 * 1024)
        raise FileTooLargeError(
            f"File size ({size_mb_actual:.2f} MB) exceeds the maximum allowed limit of {max_size_mb} MB."
        )

    # 3. Magic-byte and deep content-type validation
    if ext == ".pdf":
        _validate_pdf_signature(content)
        canonical_type = "pdf"
    elif ext == ".docx":
        _validate_docx_signature(content)
        canonical_type = "docx"
    else:
        raise InvalidFileTypeError(f"Unsupported file extension: {ext}")

    logger.info(
        "File validation passed: extension=%s, size_bytes=%d",
        ext,
        size_bytes,
    )
    return canonical_type


def _validate_pdf_signature(content: bytes) -> None:
    """Verify that the byte stream conforms to PDF format specifications."""
    # Standard PDF header %PDF- must appear near the beginning (within first 1024 bytes)
    header_sample = content[:1024]
    if PDF_MAGIC_BYTES not in header_sample:
        raise InvalidFileTypeError(
            "File content does not match the expected PDF format. Magic header missing or invalid."
        )


def _validate_docx_signature(content: bytes) -> None:
    """Verify that the byte stream is a valid OpenXML Word document (ZIP container)."""
    if not content.startswith(ZIP_MAGIC_BYTES):
        raise InvalidFileTypeError(
            "File content does not match the expected DOCX format. ZIP header missing or invalid."
        )

    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            namelist = zf.namelist()
            # Valid DOCX contains word/document.xml or [Content_Types].xml
            is_valid_docx = any(
                name.startswith("word/") or name == "[Content_Types].xml"
                for name in namelist
            )
            if not is_valid_docx:
                raise InvalidFileTypeError(
                    "The uploaded archive is not a valid Microsoft Word (.docx) document."
                )

            # Test ZIP container structural integrity
            corrupted_file = zf.testzip()
            if corrupted_file is not None:
                raise EncryptedOrCorruptFileError(
                    "The DOCX document is corrupted or contains damaged internal components."
                )
    except zipfile.BadZipFile:
        raise EncryptedOrCorruptFileError(
            "The DOCX document is corrupted or not a valid archive."
        )
    except (zipfile.LargeZipFile, RuntimeError) as exc:
        raise EncryptedOrCorruptFileError(
            f"Unable to process DOCX archive: {str(exc)}"
        )
