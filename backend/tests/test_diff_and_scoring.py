"""
backend/tests/test_diff_and_scoring.py — Tests covering comparison structures,
scoring transparency, provenance, reordering, omissions, and factuality representation.

Covers:
- Unchanged and reworded bullets tracking via source_bullet_id
- Reordered bullets identification using source_bullet_id vs current position
- Omitted/consolidated original bullets identification when original has more items
- Missing/empty sections safety (empty skills, missing summaries, no education/projects)
- Supported, partially supported, and unmentioned requirements distinctions
- Zero requirements calculation and explanatory methodology text
- Factuality warnings representation and provenance verification
"""
from __future__ import annotations

import pytest
from app.schemas.analysis import (
    ImportanceLevel,
    MatchAnalysis,
    MissingRequirement,
    RequirementMatch,
    SupportStatus,
)
from app.schemas.common import ContactInfo, ExperienceBullet
from app.schemas.resume import ExperienceEntry, ParsedResume
from app.schemas.tailored import (
    AuditWarning,
    ChangeType,
    TailingChange,
    TailoredBullet,
    TailoredExperienceEntry,
    TailoredResume,
    TailoredSkills,
)
from app.services.scoring_service import (
    build_scoring_methodology_text,
    calculate_match_score,
)


def test_scoring_methodology_text_with_zero_requirements():
    """Confirms zero requirements produce an informative message rather than a crash."""
    score = calculate_match_score([])
    text = build_scoring_methodology_text([], score)
    assert score == 0
    assert "No requirements could be extracted" in text
    assert "Score defaults to 0" in text


def test_scoring_methodology_text_with_mixed_requirements():
    """Confirms transparent methodology text documents points achieved and total possible."""
    reqs = [
        RequirementMatch(
            requirement="Python programming",
            importance=ImportanceLevel.REQUIRED,
            status=SupportStatus.EXPLICITLY_SUPPORTED,
            evidence_quote="5 years building backend microservices in Python",
            notes="Direct match found in experience section",
        ),
        RequirementMatch(
            requirement="Kubernetes orchestration",
            importance=ImportanceLevel.PREFERRED,
            status=SupportStatus.PARTIALLY_SUPPORTED,
            evidence_quote=None,
            notes="Docker mentioned, but Kubernetes not explicitly named",
        ),
        RequirementMatch(
            requirement="Go programming",
            importance=ImportanceLevel.PREFERRED,
            status=SupportStatus.NOT_MENTIONED,
            evidence_quote=None,
            notes="No mention of Go in source resume",
        ),
    ]

    score = calculate_match_score(reqs)
    # Required: 1.0 * 1.5 = 1.5 achieved / 1.5 possible
    # Preferred 1: 0.5 * 1.0 = 0.5 achieved / 1.0 possible
    # Preferred 2: 0.0 * 1.0 = 0.0 achieved / 1.0 possible
    # Total achieved = 2.0 / Total possible = 3.5 -> 57.14% -> 57%
    assert score == 57

    methodology = build_scoring_methodology_text(reqs, score)
    assert "3 extracted requirements" in methodology
    assert "1 required @ 1.5×" in methodology
    assert "2 preferred @ 1.0×" in methodology
    assert "Points achieved: 2.0 / 3.5 = 57%" in methodology


def test_bullet_provenance_and_diff_tracking():
    """
    Verifies that source_bullet_id accurately links tailored bullets
    to original source bullets, distinguishing genuine changes from unchanged items.
    """
    b1 = TailoredBullet(
        source_bullet_id=0,
        original_text="Engineered REST API endpoints.",
        tailored_text="Architected resilient RESTful API endpoints handling 20,000 req/sec.",
        rationale="Target JD prioritizes high-throughput REST APIs.",
    )
    b2 = TailoredBullet(
        source_bullet_id=1,
        original_text="Managed weekly sprint planning.",
        tailored_text="Managed weekly sprint planning.",  # Unchanged
        rationale="Preserved verbatim.",
    )

    assert b1.source_bullet_id == 0
    assert b1.original_text != b1.tailored_text
    assert b2.source_bullet_id == 1
    assert b2.original_text == b2.tailored_text


def test_bullet_reordering_detection_via_source_provenance():
    """
    Verifies that reordering is accurately identified when source_bullet_id
    differs from current array index, and that reordered bullets are NOT
    falsely categorized as removed or deleted.
    """
    # Original bullet order: 0: Leader, 1: Cloud architect, 2: Sprint planning
    # Tailored bullet order: Position 0 is source 1 (reordered), Position 1 is source 0 (reordered)
    tailored_bullets = [
        TailoredBullet(
            source_bullet_id=1,  # Originally at index 1, now at index 0
            original_text="Designed cloud architecture.",
            tailored_text="Architected AWS multi-region cloud infrastructure.",
            rationale="Prioritized cloud architecture for JD relevance.",
        ),
        TailoredBullet(
            source_bullet_id=0,  # Originally at index 0, now at index 1
            original_text="Led team of 4 engineers.",
            tailored_text="Led high-performing team of 4 backend engineers.",
            rationale="Highlighted team leadership.",
        ),
    ]

    is_reordered_0 = tailored_bullets[0].source_bullet_id != 0
    is_reordered_1 = tailored_bullets[1].source_bullet_id != 1

    assert is_reordered_0 is True
    assert is_reordered_1 is True
    # The source content was reordered, not removed
    assert tailored_bullets[0].source_bullet_id == 1
    assert tailored_bullets[1].source_bullet_id == 0


def test_bullet_omission_detection_when_original_has_deprioritized_content():
    """
    Verifies that when an original experience entry contains bullets not referenced
    by any tailored bullet's source_bullet_id, they can be identified as omitted.
    """
    orig_bullets = [
        ExperienceBullet(bullet_id=0, text="Engineered microservices in Python."),
        ExperienceBullet(bullet_id=1, text="Participated in daily standups and sprint retros."),
        ExperienceBullet(bullet_id=2, text="Optimized Postgres queries."),
    ]

    tailored_bullets = [
        TailoredBullet(
            source_bullet_id=0,
            original_text=orig_bullets[0].text,
            tailored_text="Engineered fault-tolerant microservices in Python.",
            rationale="Highlighted resilience.",
        ),
        TailoredBullet(
            source_bullet_id=2,
            original_text=orig_bullets[2].text,
            tailored_text="Optimized PostgreSQL queries reducing latency by 40%.",
            rationale="Highlighted query performance.",
        ),
    ]

    tailored_source_ids = {b.source_bullet_id for b in tailored_bullets}
    omitted = [ob for ob in orig_bullets if ob.bullet_id not in tailored_source_ids]

    assert len(omitted) == 1
    assert omitted[0].bullet_id == 1
    assert "daily standups" in omitted[0].text


def test_factuality_audit_warnings_representation():
    """
    Verifies that audit warnings highlight ambiguous claims without
    falsely claiming generated content is verified or factual.
    """
    warning = AuditWarning(
        bullet_ref="Acme Inc / bullet 0",
        original_text="Improved database performance.",
        tailored_text="Optimized database indexing improving query throughput by 50%.",
        concern="Specific percentage (50%) not evidenced in source resume text.",
    )

    resume = TailoredResume(
        contact_info=ContactInfo(name="Alex Test"),
        skills=TailoredSkills(retained_relevant=["SQL"], retained_other=[]),
        experience=[
            TailoredExperienceEntry(
                company="Acme Inc",
                role="Engineer",
                bullets=[
                    TailoredBullet(
                        source_bullet_id=0,
                        original_text=warning.original_text,
                        tailored_text=warning.tailored_text,
                        rationale="Rephrased with metric",
                    )
                ],
            )
        ],
        audit_warnings=[warning],
    )

    assert len(resume.audit_warnings) == 1
    assert "not evidenced" in resume.audit_warnings[0].concern
    assert resume.audit_warnings[0].bullet_ref == "Acme Inc / bullet 0"


def test_missing_optional_sections_safety():
    """Verifies TailoredResume schema handles empty arrays and null optional sections safely."""
    minimal_resume = TailoredResume(
        contact_info=ContactInfo(name="Solo Candidate"),
        summary=None,
        skills=TailoredSkills(retained_relevant=[], retained_other=[]),
        experience=[],
        education=[],
        projects=[],
        tailoring_changes=[],
        audit_warnings=[],
    )

    assert minimal_resume.summary is None
    assert len(minimal_resume.experience) == 0
    assert len(minimal_resume.education) == 0
    assert len(minimal_resume.projects) == 0
    assert len(minimal_resume.skills.retained_relevant) == 0


def test_tailoring_change_coercion_from_unstructured_model_strings():
    """Verifies that non-standard change_type strings from LLM output (like 'filtered', 'reordered') coerce safely without 500 error."""
    from app.services.factuality_auditor import audit_and_build_tailored_resume

    parsed_resume = ParsedResume(
        contact_info=ContactInfo(name="Candidate"),
        skills=["Python"],
        experience=[],
        raw_text="Candidate raw text with Python",
    )

    tailored = audit_and_build_tailored_resume(
        parsed_resume=parsed_resume,
        raw_tailored_summary="Summary",
        raw_relevant_skills=["Python"],
        raw_tailored_experience=[],
        raw_tailoring_changes=[
            {"section": "Experience", "change_type": "filtered", "reasoning": "Filtered irrelevant items"},
            {"section": "Summary", "change_type": "reordered", "reasoning": "Reordered statements"},
            {"section": "Skills", "change_type": "highlighted", "reasoning": "Highlighted key skills"},
        ],
    )

    assert len(tailored.tailoring_changes) == 3
    assert tailored.tailoring_changes[0].change_type == ChangeType.REFRAMED
    assert tailored.tailoring_changes[1].change_type == ChangeType.REFRAMED
    assert tailored.tailoring_changes[2].change_type == ChangeType.ENHANCED

