"""app/routers/resume.py — Document upload and parsing endpoints.

Provides:
- POST /api/v1/resume/parse: Validates and extracts text from uploaded PDF or DOCX files.

Streaming upload size protection prevents memory exhaustion.
NEVER logs uploaded resume contents or sensitive personal data.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile

from app.config import Settings, get_settings
from app.exceptions import FileTooLargeError, InvalidFileTypeError
from app.schemas.resume import ResumeParseResponse
from app.services.document_parser import extract_document_text
from app.services.file_validator import validate_file

logger = logging.getLogger(__name__)

router = APIRouter()

STREAM_CHUNK_SIZE = 64 * 1024  # 64 KB chunks


@router.post(
    "/parse",
    response_model=ResumeParseResponse,
    summary="Validate and extract text from resume document",
    description=(
        "Uploads a PDF (.pdf) or Word (.docx) resume, enforces file-size limits, "
        "validates magic bytes, extracts readable text, and validates text density."
    ),
)
async def parse_resume_document(
    file: UploadFile = File(..., description="Resume document in PDF or DOCX format"),
    settings: Settings = Depends(get_settings),
) -> ResumeParseResponse:
    filename = file.filename or "unknown"
    logger.info("Received resume upload request: filename=%s", filename)

    # 1. Read bytes with streaming chunk limit enforcement to prevent memory attacks
    buffer = bytearray()
    max_bytes = settings.max_file_size_bytes

    while True:
        chunk = await file.read(STREAM_CHUNK_SIZE)
        if not chunk:
            break
        buffer.extend(chunk)
        if len(buffer) > max_bytes:
            raise FileTooLargeError(
                f"File size exceeds the maximum allowed limit of {settings.max_file_size_mb} MB."
            )

    content = bytes(buffer)

    # 2. Validate file extension, size, and magic bytes
    canonical_type = validate_file(
        content=content,
        filename=filename,
        max_size_bytes=max_bytes,
        max_size_mb=settings.max_file_size_mb,
    )

    # 3. Extract text, enforce page limits, and validate text density
    parse_result = extract_document_text(
        content=content,
        filename=filename,
        file_type=canonical_type,
        settings=settings,
    )

    return ResumeParseResponse(
        filename=parse_result.filename,
        file_type=parse_result.file_type,
        page_count=parse_result.page_count,
        char_count=parse_result.char_count,
        word_count=parse_result.word_count,
        raw_text=parse_result.raw_text,
    )
