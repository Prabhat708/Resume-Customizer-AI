"""app/schemas/resume.py — Original (parsed) resume schema."""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.common import ContactInfo, EducationEntry, ExperienceBullet, ProjectEntry


class ExperienceEntry(BaseModel):
    company: str
    role: str
    dates: Optional[str] = None
    bullets: List[ExperienceBullet] = Field(default_factory=list)


class ParsedResume(BaseModel):
    """Structured representation of the candidate's original resume.

    All fields are treated as immutable ground truth for factuality auditing.
    Nothing in this model is ever fabricated or supplemented.
    """
    contact_info: ContactInfo
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[ExperienceEntry] = Field(default_factory=list)
    education: List[EducationEntry] = Field(default_factory=list)
    projects: List[ProjectEntry] = Field(default_factory=list)
    raw_text: str = Field(..., description="Full verbatim extracted text for factuality auditing")


class ResumeParseResponse(BaseModel):
    """Diagnostic response model for POST /api/v1/resume/parse."""
    filename: str
    file_type: str
    page_count: int
    char_count: int
    word_count: int
    raw_text: str

