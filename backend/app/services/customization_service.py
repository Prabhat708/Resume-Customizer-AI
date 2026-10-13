"""app/services/customization_service.py — Orchestrates the complete resume customization flow.

Coordinates:
1. Job description validation.
2. File validation & document text extraction (via Phase 2 services).
3. Verbatim resume structuring into ParsedResume.
4. Gemini structured customization call.
5. Deterministic scoring calculation via scoring_service.py.
6. Factuality & provenance auditing via factuality_auditor.py.
7. Assembly of validated CustomizeResponse matching frontend TypeScript types.
"""
from __future__ import annotations

import logging
import re
from typing import Any, List, Optional

from app.config import Settings
from app.exceptions import DocumentValidationError, InvalidJobDescriptionError
from app.schemas.error import ErrorCode
from app.schemas.analysis import (
    EvidenceLevel,
    ImportanceLevel,
    MatchAnalysis,
    MissingRequirement,
    RequirementMatch,
    SupportStatus,
)
from app.schemas.api import CustomizeResponse
from app.services.document_parser import extract_document_text
from app.services.factuality_auditor import audit_and_build_tailored_resume
from app.services.file_validator import validate_file
from app.services.gemini_service import call_gemini_customization
from app.services.resume_structurer import structure_raw_resume
from app.services.scoring_service import (
    build_scoring_methodology_text,
    calculate_match_score,
)

logger = logging.getLogger(__name__)


def validate_job_description(jd: str, settings: Settings) -> str:
    """Validate that the job description meets length and content requirements."""
    if not jd or not jd.strip():
        raise InvalidJobDescriptionError("Job description cannot be empty.")

    clean_jd = jd.strip()
    char_count = len(clean_jd)
    word_count = len(clean_jd.split())

    if char_count < settings.min_job_description_chars or word_count < settings.min_job_description_words:
        raise InvalidJobDescriptionError(
            f"Job description is too short ({char_count} chars, {word_count} words). "
            f"Please provide at least {settings.min_job_description_chars} characters and {settings.min_job_description_words} words."
        )

    if char_count > settings.max_job_description_chars:
        raise InvalidJobDescriptionError(
            f"Job description exceeds maximum allowed length of {settings.max_job_description_chars} characters."
        )

    return clean_jd


def determine_evidence_level(
    requirement: str,
    evidence_quote: Optional[str],
    status: SupportStatus,
    parsed_resume: Any,
    model_evidence_level: Optional[str] = None,
) -> EvidenceLevel:
    """
    Deterministically classify the source of candidate evidence:
    - WORK_EXPERIENCE: Direct evidence in formal employer work history
    - PROJECTS: Evidence in project portfolio or open-source repositories
    - SKILLS: Evidence in technical skills, certifications, or summary
    - NONE: Unmentioned or unsupported
    """
    if status == SupportStatus.NOT_MENTIONED:
        return EvidenceLevel.NONE

    quote_clean = (evidence_quote or "").strip().lower()

    # 1. Check formal work experience bullets, company, role
    exp_texts: List[str] = []
    for exp in parsed_resume.experience:
        exp_texts.append(exp.company.lower())
        exp_texts.append(exp.role.lower())
        for b in exp.bullets:
            exp_texts.append(b.text.lower())
    exp_blob = " ".join(exp_texts)

    if quote_clean and len(quote_clean) > 5 and quote_clean in exp_blob:
        return EvidenceLevel.WORK_EXPERIENCE

    # 2. Check projects & open-source
    proj_texts: List[str] = []
    for p in parsed_resume.projects:
        proj_texts.append(p.name.lower())
        proj_texts.append(p.description.lower())
        proj_texts.extend([t.lower() for t in p.technologies])
    proj_blob = " ".join(proj_texts)

    if quote_clean and len(quote_clean) > 5 and quote_clean in proj_blob:
        return EvidenceLevel.PROJECTS

    # 3. Check skills list, certifications, and summary
    skills_texts = [s.lower() for s in parsed_resume.skills]
    if getattr(parsed_resume, "certifications", None):
        skills_texts.extend([c.lower() for c in parsed_resume.certifications])
    if getattr(parsed_resume, "summary", None):
        skills_texts.append(parsed_resume.summary.lower())
    skills_blob = " ".join(skills_texts)

    if quote_clean and len(quote_clean) > 5 and quote_clean in skills_blob:
        return EvidenceLevel.SKILLS

    # 4. Respect model_evidence_level if provided
    if model_evidence_level:
        mel = model_evidence_level.lower().strip()
        if mel in ("work_experience", "employment", "experience", "work"):
            return EvidenceLevel.WORK_EXPERIENCE
        elif mel in ("projects", "project", "open_source"):
            return EvidenceLevel.PROJECTS
        elif mel in ("skills", "skill", "certification", "certifications"):
            return EvidenceLevel.SKILLS

    # 5. Check keywords from requirement in sections
    req_tokens = [
        t for t in re.findall(r"\w+", requirement.lower())
        if len(t) > 2 and t not in ("with", "and", "for", "year", "years", "experience", "developer", "software")
    ]
    if req_tokens:
        in_exp = any(t in exp_blob for t in req_tokens)
        in_proj = any(t in proj_blob for t in req_tokens)
        in_skills = any(t in skills_blob for t in req_tokens)
        if in_exp and not in_proj:
            return EvidenceLevel.WORK_EXPERIENCE
        elif in_proj:
            return EvidenceLevel.PROJECTS
        elif in_skills:
            return EvidenceLevel.SKILLS

    return EvidenceLevel.SKILLS


def customize_resume(
    file_bytes: bytes,
    filename: str,
    job_description: str,
    settings: Settings,
    gemini_client: Any | None = None,
) -> CustomizeResponse:
    """Execute the end-to-end customization workflow."""
    logger.info("Starting resume customization: filename=%s, bytes=%d", filename, len(file_bytes))

    # 1. Validate Job Description
    clean_jd = validate_job_description(job_description, settings)

    # 2. Validate File Container & Magic Bytes
    canonical_type = validate_file(
        content=file_bytes,
        filename=filename,
        max_size_bytes=settings.max_file_size_bytes,
        max_size_mb=settings.max_file_size_mb,
    )

    # 3. Extract and Clean Document Text
    parsed_doc = extract_document_text(
        content=file_bytes,
        filename=filename,
        file_type=canonical_type,
        settings=settings,
    )

    # 4. Structure Raw Text into Candidate Ground Truth (ParsedResume)
    if len(parsed_doc.raw_text) > settings.max_resume_chars:
        raise DocumentValidationError(
            code=ErrorCode.INSUFFICIENT_TEXT_CONTENT,
            message=f"Resume content exceeds maximum allowed length of {settings.max_resume_chars} characters.",
            status_code=400,
        )

    parsed_resume = structure_raw_resume(
        raw_text=parsed_doc.raw_text,
        filename=filename,
    )

    # 5. Call Gemini Provider for Structured Tailoring
    ai_output = call_gemini_customization(
        parsed_resume=parsed_resume,
        job_description=clean_jd,
        settings=settings,
        client=gemini_client,
    )

    # 6. Build Breakdown and Missing Requirements
    raw_breakdown = ai_output.get("requirements_analysis", [])
    breakdown: List[RequirementMatch] = []
    for item in raw_breakdown:
        # Validate status enum safely
        raw_status = str(item.get("status", "not_mentioned")).lower()
        if raw_status == "explicitly_supported":
            status = SupportStatus.EXPLICITLY_SUPPORTED
        elif raw_status == "partially_supported":
            status = SupportStatus.PARTIALLY_SUPPORTED
        else:
            status = SupportStatus.NOT_MENTIONED

        # Validate importance enum safely
        raw_imp = str(item.get("importance", "required")).lower()
        importance = ImportanceLevel.PREFERRED if raw_imp == "preferred" else ImportanceLevel.REQUIRED

        req_text = str(item.get("requirement", "Requirement"))
        evidence_quote = item.get("evidence_quote")

        evidence_lvl = determine_evidence_level(
            requirement=req_text,
            evidence_quote=evidence_quote,
            status=status,
            parsed_resume=parsed_resume,
            model_evidence_level=item.get("evidence_level"),
        )

        # Evidence Level Calibration: If technical developer capability is evidenced only in projects
        # rather than verified employer work experience, calibrate status to partially_supported
        # to ensure the score accurately reflects moderate alignment (67%) without fabricating primary employment.
        if (
            status == SupportStatus.EXPLICITLY_SUPPORTED
            and evidence_lvl == EvidenceLevel.PROJECTS
            and not any(exp_term in req_text.lower() for exp_term in ("years", "tenure", "education", "degree"))
        ):
            status = SupportStatus.PARTIALLY_SUPPORTED

        breakdown.append(
            RequirementMatch(
                requirement=req_text,
                importance=importance,
                status=status,
                evidence_level=evidence_lvl,
                evidence_quote=evidence_quote,
                notes=str(item.get("notes", "Evidence evaluated against resume content.")),
            )
        )

    raw_missing = ai_output.get("missing_requirements", [])
    missing_requirements: List[MissingRequirement] = []
    for item in raw_missing:
        raw_imp = str(item.get("importance", "required")).lower()
        importance = ImportanceLevel.PREFERRED if raw_imp == "preferred" else ImportanceLevel.REQUIRED
        missing_requirements.append(
            MissingRequirement(
                requirement=str(item.get("requirement", "Requirement")),
                importance=importance,
                guidance=str(item.get("guidance", "Consider highlighting this qualification if you possess it.")),
            )
        )

    # 7. Calculate Deterministic Match Score on Backend (Not Generated by LLM)
    estimated_score = calculate_match_score(breakdown)
    methodology_text = build_scoring_methodology_text(breakdown, estimated_score)

    match_analysis = MatchAnalysis(
        estimated_score=estimated_score,
        scoring_methodology=methodology_text,
        disclaimer="Estimated match based on requirement evidence analysis. Not an official ATS score.",
        breakdown=breakdown,
        missing_requirements=missing_requirements,
    )

    # 8. Factuality & Provenance Audit for Tailored Resume
    tailored_resume = audit_and_build_tailored_resume(
        parsed_resume=parsed_resume,
        raw_tailored_summary=ai_output.get("tailored_summary"),
        raw_relevant_skills=ai_output.get("highlighted_skills", []),
        raw_tailored_experience=ai_output.get("tailored_experience", []),
        raw_tailoring_changes=ai_output.get("tailoring_changes", []),
    )

    logger.info("Customization succeeded: estimated_score=%d", estimated_score)

    return CustomizeResponse(
        match_analysis=match_analysis,
        original_resume=parsed_resume,
        tailored_resume=tailored_resume,
    )
