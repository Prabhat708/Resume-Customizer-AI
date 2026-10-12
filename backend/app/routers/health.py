"""app/routers/health.py — Independent liveness probe.

This endpoint:
- Does NOT call the Gemini API.
- Does NOT require GEMINI_API_KEY to be set.
- Does NOT expose secrets, model names, environment names, or key prefixes.
- Returns only: operational status, app version, and a boolean indicating
  whether GEMINI_MODEL is configured (not its value).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import Settings, get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    model_configured: bool


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness and readiness probe",
    description=(
        "Returns operational status and safe configuration state. "
        "Does not depend on external API credentials."
    ),
)
def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        model_configured=settings.gemini_configured,
    )
