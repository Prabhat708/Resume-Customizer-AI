"""app/services/factuality_auditor.py — Enforces factuality invariants and provenance tracking.

Invariants enforced:
1. Candidate identity, employers, titles, dates, and education are immutable and preserved verbatim.
2. Skills are strictly partitioned: no JD-only skills are injected into the candidate's tailored resume.
3. Rewritten experience bullets must link to a valid source_bullet_id.
4. Quantitative metrics (percentages, numbers, currencies) introduced by the model that were not present
   in the candidate's original resume are flagged as AuditWarning items for candidate review.
"""
from __future__ import annotations

import logging
import re
from typing import List, Tuple

from app.schemas.resume import ParsedResume
from app.schemas.tailored import (
    AuditWarning,
    TailoredBullet,
    TailoredExperienceEntry,
    TailoredResume,
    TailoredSkills,
    TailingChange,
)

logger = logging.getLogger(__name__)

# Patterns for extracting quantitative metrics
METRIC_PATTERNS = [
    re.compile(r"\b\d+(?:\.\d+)?%"),  # Percentages (e.g., 45%, 99.9%)
    re.compile(r"\$\d+[\d,]*(?:\.\d+)?(?:\s*[kKmMbB]|\s*million|\s*billion)?\b"),  # Currency
    re.compile(r"\b\d+(?:\.\d+)?x\b", re.IGNORECASE),  # Multipliers (e.g., 3x, 10x)
    re.compile(r"\b\d+[\d,]*(?:\+)?\s*(?:users|clients|customers|microservices|ms|seconds|minutes|hours|engineers|team\s+members|projects|endpoints)\b", re.IGNORECASE),
]


def extract_metrics(text: str) -> List[str]:
    """Find all quantitative metric strings in a block of text."""
    metrics: List[str] = []
    for pattern in METRIC_PATTERNS:
        matches = pattern.findall(text)
        for m in matches:
            cleaned = m.strip().lower()
            if cleaned not in metrics:
                metrics.append(cleaned)
    return metrics


def audit_and_build_tailored_resume(
    parsed_resume: ParsedResume,
    raw_tailored_summary: str | None,
    raw_relevant_skills: List[str],
    raw_tailored_experience: List[dict],
    raw_tailoring_changes: List[dict],
) -> TailoredResume:
    """Enforce factuality constraints and produce the final TailoredResume."""

    # 1. Skill Containment: only retain skills that exist in original resume
    original_skills_normalized = {s.strip().lower(): s.strip() for s in parsed_resume.skills if s.strip()}
    raw_text_lower = parsed_resume.raw_text.lower()

    retained_relevant: List[str] = []
    for skill in raw_relevant_skills:
        s_clean = skill.strip()
        s_lower = s_clean.lower()
        # Verify if skill existed in candidate's original skill list or anywhere in their raw resume text
        if s_lower in original_skills_normalized or (len(s_lower) > 2 and s_lower in raw_text_lower):
            display_name = original_skills_normalized.get(s_lower, s_clean)
            if display_name not in retained_relevant:
                retained_relevant.append(display_name)
        else:
            logger.info("Stripped ungrounded skill proposed by model: %s", s_clean)

    # All remaining original skills go to retained_other
    retained_other = [
        s for s in parsed_resume.skills
        if s not in retained_relevant
    ]

    tailored_skills = TailoredSkills(
        retained_relevant=retained_relevant,
        retained_other=retained_other,
    )

    # 2. Experience Provenance & Metric Auditing
    audit_warnings: List[AuditWarning] = []
    tailored_experience: List[TailoredExperienceEntry] = []

    for orig_exp in parsed_resume.experience:
        orig_bullet_map = {b.bullet_id: b.text for b in orig_exp.bullets}
        tailored_bullets_list: List[TailoredBullet] = []

        # Find corresponding raw tailored bullets from model output
        matched_raw_entry = next(
            (
                item for item in raw_tailored_experience
                if item.get("company", "").strip().lower() == orig_exp.company.strip().lower()
                or item.get("role", "").strip().lower() == orig_exp.role.strip().lower()
            ),
            None,
        )

        model_bullets = matched_raw_entry.get("bullets", []) if matched_raw_entry else []
        model_bullet_by_id = {
            b.get("source_bullet_id"): b for b in model_bullets if "source_bullet_id" in b
        }

        for orig_b in orig_exp.bullets:
            b_id = orig_b.bullet_id
            orig_text = orig_b.text

            if b_id in model_bullet_by_id:
                m_bullet = model_bullet_by_id[b_id]
                tailored_text = m_bullet.get("tailored_text", orig_text).strip()
                rationale = m_bullet.get("rationale", "Reframed to emphasize target qualifications.")
            else:
                # Default to original bullet if model did not return a rewrite for this id
                tailored_text = orig_text
                rationale = "Retained original achievement."

            # Metric check: detect newly invented numbers/percentages
            tailored_metrics = extract_metrics(tailored_text)
            orig_metrics = extract_metrics(orig_text)
            raw_text_metrics = extract_metrics(parsed_resume.raw_text)

            for tm in tailored_metrics:
                if tm not in orig_metrics and tm not in raw_text_metrics:
                    audit_warnings.append(
                        AuditWarning(
                            bullet_ref=f"{orig_exp.company} (Bullet #{b_id + 1})",
                            original_text=orig_text,
                            tailored_text=tailored_text,
                            concern=f"Metric '{tm}' appears in customized bullet but was not found in original resume.",
                        )
                    )

            tailored_bullets_list.append(
                TailoredBullet(
                    source_bullet_id=b_id,
                    original_text=orig_text,
                    tailored_text=tailored_text,
                    rationale=rationale,
                )
            )

        tailored_experience.append(
            TailoredExperienceEntry(
                company=orig_exp.company,
                role=orig_exp.role,
                dates=orig_exp.dates,
                bullets=tailored_bullets_list,
            )
        )

    # 3. Tailoring Changes
    tailoring_changes = [
        TailingChange(
            section=c.get("section", "Experience"),
            change_type=c.get("change_type", "reframed"),
            reasoning=c.get("reasoning", "Aligned with job requirements while preserving candidate qualifications."),
        )
        for c in raw_tailoring_changes
    ]
    if not tailoring_changes:
        tailoring_changes.append(
            TailingChange(
                section="Experience",
                change_type="reframed",
                reasoning="Reordered and highlighted bullet accomplishments relevant to target qualifications.",
            )
        )

    return TailoredResume(
        contact_info=parsed_resume.contact_info,
        summary=raw_tailored_summary or parsed_resume.summary,
        skills=tailored_skills,
        experience=tailored_experience,
        education=parsed_resume.education,
        projects=parsed_resume.projects,
        tailoring_changes=tailoring_changes,
        audit_warnings=audit_warnings,
    )
