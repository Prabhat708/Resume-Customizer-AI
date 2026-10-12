"""app/schemas/common.py — Shared sub-models used across resume schemas."""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    links: List[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    institution: str
    degree: str
    dates: Optional[str] = None
    details: Optional[str] = None


class ProjectEntry(BaseModel):
    name: str
    description: str
    technologies: List[str] = Field(default_factory=list)
    url: Optional[str] = None


class ExperienceBullet(BaseModel):
    """A single original bullet point — immutable ground truth."""
    bullet_id: int = Field(..., description="0-based index within the experience entry")
    text: str
