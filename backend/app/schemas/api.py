"""app/schemas/api.py — Top-level API request and response models."""
from __future__ import annotations

from pydantic import BaseModel

from app.schemas.analysis import MatchAnalysis
from app.schemas.resume import ParsedResume
from app.schemas.tailored import TailoredResume


class CustomizeResponse(BaseModel):
    """Full response payload for POST /api/v1/customize."""
    match_analysis: MatchAnalysis
    original_resume: ParsedResume
    tailored_resume: TailoredResume


class ExportPdfRequest(BaseModel):
    """Request body for POST /api/v1/export/pdf."""
    tailored_resume: TailoredResume
