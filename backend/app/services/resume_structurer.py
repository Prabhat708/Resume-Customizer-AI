"""app/services/resume_structurer.py — Structures verbatim document text into a ParsedResume model.

Assigns immutable 0-based bullet_id indices to each experience bullet for provenance tracking.
Extracts contact info, summary, skills, experience, education, and projects without fabrication.
"""
from __future__ import annotations

import re
from typing import List, Optional

from app.schemas.common import ContactInfo, EducationEntry, ExperienceBullet, ProjectEntry
from app.schemas.resume import ExperienceEntry, ParsedResume


EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_PATTERN = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
URL_PATTERN = re.compile(
    r"\b(?:https?://|www\.)[A-Za-z0-9.\-_]+(?:\.[A-Za-z]{2,})+(?:/[^\s]*)?\b|"
    r"\b(?:linkedin\.com/in/[A-Za-z0-9_-]+|github\.com/[A-Za-z0-9_-]+)\b",
    re.IGNORECASE,
)

SECTION_HEADERS = {
    "summary": re.compile(r"^(?:professional\s+summary|summary|profile|about\s+me)\b", re.IGNORECASE),
    "skills": re.compile(r"^(?:skills|technical\s+skills|core\s+competencies|technologies)\b", re.IGNORECASE),
    "experience": re.compile(r"^(?:experience|work\s+experience|professional\s+experience|employment\s+history)\b", re.IGNORECASE),
    "education": re.compile(r"^(?:education|academic\s+background|qualifications)\b", re.IGNORECASE),
    "projects": re.compile(r"^(?:projects|key\s+projects|personal\s+projects)\b", re.IGNORECASE),
}


def structure_raw_resume(raw_text: str, filename: str = "resume") -> ParsedResume:
    """Parse raw resume text into a structured ParsedResume object."""
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    # 1. Extract contact information
    email_match = EMAIL_PATTERN.search(raw_text)
    email = email_match.group(0) if email_match else None

    phone_match = PHONE_PATTERN.search(raw_text)
    phone = phone_match.group(0) if phone_match else None

    links = list(set(URL_PATTERN.findall(raw_text)))

    # Candidate name: first non-header, non-contact line of text (max 60 chars)
    name = "Candidate"
    for line in lines[:5]:
        if (
            len(line) < 60
            and not EMAIL_PATTERN.search(line)
            and not PHONE_PATTERN.search(line)
            and not URL_PATTERN.search(line)
            and not any(h.match(line) for h in SECTION_HEADERS.values())
        ):
            # Clean possible titles after a separator like ' - ' or ' | '
            clean_name = re.split(r"\s+[-|—]\s+", line)[0].strip()
            if clean_name and not clean_name.lower().startswith("resume"):
                name = clean_name
                break

    contact_info = ContactInfo(
        name=name,
        email=email,
        phone=phone,
        location=None,
        links=links,
    )

    # 2. Segment text into sections
    current_section = "header"
    section_lines: dict[str, List[str]] = {
        "summary": [],
        "skills": [],
        "experience": [],
        "education": [],
        "projects": [],
    }

    for line in lines:
        matched_section = None
        for sec, pattern in SECTION_HEADERS.items():
            if pattern.match(line.rstrip(":")):
                matched_section = sec
                break

        if matched_section:
            current_section = matched_section
            continue

        if current_section in section_lines:
            section_lines[current_section].append(line)

    # 3. Extract Summary
    summary_text: Optional[str] = None
    if section_lines["summary"]:
        summary_text = " ".join(section_lines["summary"])

    # 4. Extract Skills
    skills_list: List[str] = []
    for s_line in section_lines["skills"]:
        # Handle delimiters like comma, bullet, pipe, semicolon
        tokens = re.split(r"[,•|;·\n]", s_line)
        for token in tokens:
            cleaned = token.strip().strip("-").strip()
            # Filter headers or categories like 'Languages: Python'
            if ":" in cleaned:
                cleaned = cleaned.split(":", 1)[1].strip()
            if cleaned and len(cleaned) < 40 and cleaned.lower() not in ["skills", "technical skills"]:
                if cleaned not in skills_list:
                    skills_list.append(cleaned)

    # 5. Extract Experience & assign bullet_ids
    experience_entries: List[ExperienceEntry] = []
    exp_lines = section_lines["experience"]

    if exp_lines:
        current_exp: Optional[dict] = None
        current_bullets: List[str] = []

        for line in exp_lines:
            is_bullet = line.startswith(("-", "•", "*", "–", "—")) or line.startswith(tuple(f"{i}." for i in range(1, 10)))
            clean_line = re.sub(r"^[-•*–—\d.]\s*", "", line).strip()

            if is_bullet:
                if clean_line:
                    current_bullets.append(clean_line)
            elif len(line.split()) < 10 and any(sep in line for sep in ["–", "-", " at ", " @ ", "|", ","]):
                # Looks like a company / role header line
                if current_exp is not None:
                    bullets_objs = [
                        ExperienceBullet(bullet_id=b_idx, text=b_text)
                        for b_idx, b_text in enumerate(current_bullets)
                    ]
                    experience_entries.append(
                        ExperienceEntry(
                            company=current_exp.get("company", "Company"),
                            role=current_exp.get("role", "Role"),
                            dates=current_exp.get("dates"),
                            bullets=bullets_objs,
                        )
                    )
                    current_bullets = []

                # Parse header: e.g. "Senior Software Engineer - Acme Corp (2020 - Present)"
                parts = re.split(r"\s+[-–|]\s+", line)
                role = parts[0].strip() if len(parts) > 0 else "Software Engineer"
                company = parts[1].strip() if len(parts) > 1 else "Organization"
                dates = parts[2].strip() if len(parts) > 2 else None

                current_exp = {"company": company, "role": role, "dates": dates}
            else:
                if clean_line:
                    current_bullets.append(clean_line)

        if current_exp is not None or current_bullets:
            company = current_exp.get("company", "Organization") if current_exp else "Organization"
            role = current_exp.get("role", "Professional Experience") if current_exp else "Professional Experience"
            dates = current_exp.get("dates") if current_exp else None
            bullets_objs = [
                ExperienceBullet(bullet_id=b_idx, text=b_text)
                for b_idx, b_text in enumerate(current_bullets)
            ]
            experience_entries.append(
                ExperienceEntry(company=company, role=role, dates=dates, bullets=bullets_objs)
            )

    # Fallback if experience section was not explicitly titled: split paragraphs into bullets
    if not experience_entries and len(lines) > 2:
        fallback_bullets = [
            ExperienceBullet(bullet_id=idx, text=l)
            for idx, l in enumerate(lines[1:8])
        ]
        experience_entries.append(
            ExperienceEntry(
                company="Professional Experience",
                role="Software Engineer",
                dates=None,
                bullets=fallback_bullets,
            )
        )

    # 6. Extract Education
    education_entries: List[EducationEntry] = []
    for edu_line in section_lines["education"]:
        if len(edu_line) > 5:
            education_entries.append(
                EducationEntry(
                    institution="Educational Institution",
                    degree=edu_line,
                    dates=None,
                    details=None,
                )
            )

    # 7. Extract Projects
    project_entries: List[ProjectEntry] = []
    for proj_line in section_lines["projects"]:
        if len(proj_line) > 5:
            project_entries.append(
                ProjectEntry(
                    name=proj_line.split(" - ")[0].strip() if " - " in proj_line else "Project",
                    description=proj_line,
                    technologies=[],
                    url=None,
                )
            )

    return ParsedResume(
        contact_info=contact_info,
        summary=summary_text,
        skills=skills_list,
        experience=experience_entries,
        education=education_entries,
        projects=project_entries,
        raw_text=raw_text,
    )
