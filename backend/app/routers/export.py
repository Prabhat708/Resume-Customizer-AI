"""
app/routers/export.py — PDF export endpoints.

Provides:
- POST /api/v1/export/pdf: Generates and streams an ATS-formatted resume PDF
  directly from a validated TailoredResume schema payload.
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse, Response

from app.schemas.api import ExportPdfRequest
from app.schemas.error import ErrorCode, ErrorDetail, ErrorResponse
from app.services.pdf_exporter import generate_resume_pdf, get_safe_pdf_filename

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/pdf",
    summary="Export tailored resume as an ATS-readable PDF",
    description=(
        "Converts validated TailoredResume JSON into a high-fidelity, ATS-readable PDF. "
        "Returns raw PDF binary stream with Content-Disposition attachment headers."
    ),
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Resume PDF file binary stream.",
        },
        400: {"model": ErrorResponse, "description": "Validation error in resume structure."},
        500: {"model": ErrorResponse, "description": "PDF generation failed."},
    },
)
async def export_resume_pdf(request: ExportPdfRequest) -> Response:
    """Export validated TailoredResume into an ATS-readable PDF."""
    try:
        pdf_bytes = generate_resume_pdf(request.tailored_resume)
        filename = get_safe_pdf_filename(request.tailored_resume.contact_info.name)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/pdf",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )
    except Exception as e:
        logger.exception("Failed to generate resume PDF: %s", str(e))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=ErrorCode.INTERNAL_ERROR,
                    message="Failed to generate resume PDF. Please check resume content and retry.",
                )
            ).model_dump(),
        )
