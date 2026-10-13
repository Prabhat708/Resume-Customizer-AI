"""app/schemas/gemini.py — Pydantic validation schema for raw Gemini structured outputs.

Enforces structural validity on model output before domain processing.
Every field is explicitly typed to prevent KeyError/TypeError in downstream services.
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class GeminiTailoredBullet(BaseModel):
    source_bullet_id: int = Field(
        ..., description="0-based index linking directly to the source experience bullet"
    )
    tailored_text: str = Field(
        ..., description="Rewritten experience bullet tailored to target role requirements"
    )
    rationale: str = Field(
        default="", description="Explanation of why this rewrite highlights JD relevance"
    )


class GeminiTailoredExperience(BaseModel):
    company: str = Field(..., description="Company name preserved verbatim from candidate resume")
    role: str = Field(..., description="Role title preserved verbatim from candidate resume")
    bullets: List[GeminiTailoredBullet] = Field(
        default_factory=list, description="List of tailored experience bullets"
    )


class GeminiRequirementMatch(BaseModel):
    requirement: str = Field(..., description="Target role qualification or requirement")
    importance: str = Field(
        default="required", description="'required' or 'preferred'"
    )
    status: str = Field(
        default="not_mentioned",
        description="'explicitly_supported', 'partially_supported', or 'not_mentioned'",
    )
    evidence_level: Optional[str] = Field(
        default=None,
        description="'work_experience', 'projects', 'skills', or 'none'",
    )
    evidence_quote: Optional[str] = Field(
        default=None, description="Verbatim quote from candidate resume proving this requirement"
    )
    notes: Optional[str] = Field(
        default="Evaluated against verified candidate background.",
        description="Brief notes explaining the match evaluation",
    )


class GeminiMissingRequirement(BaseModel):
    requirement: str = Field(..., description="Job requirement missing or unmentioned")
    importance: str = Field(default="required", description="'required' or 'preferred'")
    guidance: str = Field(
        default="", description="Constructive actionable guidance for candidate verification"
    )


class GeminiTailoringChange(BaseModel):
    section: str = Field(default="Summary", description="Resume section affected")
    change_type: str = Field(default="reframed", description="'reframed', 'enhanced', or 'unchanged'")
    reasoning: str = Field(default="", description="Reasoning behind the customization")


class GeminiCustomizationResponse(BaseModel):
    """Raw structured output schema guaranteed from Google Gemini."""
    tailored_summary: str = Field(
        ..., description="Reframed professional summary highlighting verified candidate qualifications"
    )
    highlighted_skills: List[str] = Field(
        default_factory=list, description="Skills present in candidate resume relevant to the JD"
    )
    tailored_experience: List[GeminiTailoredExperience] = Field(
        default_factory=list, description="Experience section with rewritten bullets"
    )
    requirements_analysis: List[GeminiRequirementMatch] = Field(
        default_factory=list, description="Requirement-by-requirement match breakdown"
    )
    missing_requirements: List[GeminiMissingRequirement] = Field(
        default_factory=list, description="List of unmet or partially supported JD requirements"
    )
    tailoring_changes: List[GeminiTailoringChange] = Field(
        default_factory=list, description="Summary of changes made to the resume"
    )
