"""
app/schemas/analysis.py — Match analysis schemas.

Scoring is deterministic and formula-driven (not LLM-generated).
The estimated score is clearly labeled as an estimate, not an official ATS score.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SupportStatus(str, Enum):
    EXPLICITLY_SUPPORTED = "explicitly_supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    NOT_MENTIONED = "not_mentioned"


class ImportanceLevel(str, Enum):
    REQUIRED = "required"
    PREFERRED = "preferred"


class RequirementMatch(BaseModel):
    requirement: str = Field(..., description="Requirement extracted from job description")
    importance: ImportanceLevel
    status: SupportStatus
    evidence_quote: Optional[str] = Field(
        None, description="Verbatim quote from original resume supporting this requirement"
    )
    notes: str = Field(..., description="Human-readable explanation of the status determination")


class MissingRequirement(BaseModel):
    requirement: str
    importance: ImportanceLevel
    guidance: str = Field(
        ...,
        description=(
            "Actionable note for candidate. Never instructs them to add unverified claims."
        ),
    )


class MatchAnalysis(BaseModel):
    estimated_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Deterministic weighted evidence score (0–100). Not an official ATS score.",
    )
    scoring_methodology: str = Field(
        ..., description="Human-readable explanation of the score calculation"
    )
    disclaimer: str = Field(
        default=(
            "Estimated match based on requirement evidence analysis. "
            "Not an official ATS score."
        )
    )
    breakdown: List[RequirementMatch]
    missing_requirements: List[MissingRequirement]
