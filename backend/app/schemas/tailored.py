"""
app/schemas/tailored.py — Tailored (AI-customized) resume schema.

Provenance is tracked at the bullet level via source_bullet_id.
The factuality auditor uses this linkage to verify no new claims were introduced.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.common import ContactInfo, EducationEntry, ProjectEntry


class ChangeType(str, Enum):
    REFRAMED = "reframed"
    ENHANCED = "enhanced"
    UNCHANGED = "unchanged"
    REORDERED = "reordered"


class TailoredBullet(BaseModel):
    source_bullet_id: int = Field(
        ..., description="0-based index of the original bullet this rewrite is derived from"
    )
    original_text: str = Field(..., description="Verbatim original bullet — immutable reference")
    tailored_text: str = Field(..., description="Rewritten bullet — must not introduce new facts")
    rationale: str = Field(
        ..., description="Why this rewrite improves JD relevance without fabricating claims"
    )


class TailoredExperienceEntry(BaseModel):
    """Immutable identity fields preserved verbatim from original resume."""
    company: str
    role: str
    dates: Optional[str] = None
    bullets: List[TailoredBullet] = Field(default_factory=list)


class TailoredSkills(BaseModel):
    retained_relevant: List[str] = Field(
        default_factory=list,
        description="Candidate's original skills that are relevant to the JD",
    )
    retained_other: List[str] = Field(
        default_factory=list,
        description="Candidate's remaining original skills preserved for completeness",
    )


class TailingChange(BaseModel):
    section: str
    change_type: ChangeType
    reasoning: str


class AuditWarning(BaseModel):
    """Ambiguous phrasing flagged for candidate review (Tier 2 audit finding)."""
    bullet_ref: str = Field(..., description="e.g. 'Apex Software Solutions / bullet 1'")
    original_text: str
    tailored_text: str
    concern: str


class TailoredResume(BaseModel):
    """
    AI-customized resume. Identity, employer, dates, and education fields
    are copied verbatim from ParsedResume and must not be altered.
    Skills are strictly partitioned; no JD-only skills are injected.
    """
    contact_info: ContactInfo
    summary: Optional[str] = None
    skills: TailoredSkills
    experience: List[TailoredExperienceEntry] = Field(default_factory=list)
    education: List[EducationEntry] = Field(default_factory=list)
    projects: List[ProjectEntry] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    tailoring_changes: List[TailingChange] = Field(default_factory=list)
    audit_warnings: List[AuditWarning] = Field(
        default_factory=list,
        description="Tier-2 ambiguous findings flagged for candidate verification",
    )
