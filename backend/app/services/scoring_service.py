"""
app/services/scoring_service.py — Deterministic, formula-driven match score calculator.

The score is an ESTIMATE based on evidence found in the candidate's resume.
It is NOT an official ATS score and must never be presented as one.

Formula:
    score = round(Σ(status_weight(r) × importance_multiplier(r)) /
                  Σ(importance_multiplier(r)) × 100)

Where:
    status_weight:       explicitly_supported=1.0, partially_supported=0.5, not_mentioned=0.0
    importance_multiplier: required=1.5, preferred=1.0

Edge case: If there are zero requirements, the score is 0.

Rounding uses standard half-up rounding (Decimal.ROUND_HALF_UP) to produce
deterministic, reproducible results independent of Python's built-in banker's
rounding behavior.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import List

from app.schemas.analysis import ImportanceLevel, RequirementMatch, SupportStatus

# ── Weight tables ────────────────────────────────────────────────────────────

_STATUS_WEIGHT: dict[SupportStatus, Decimal] = {
    SupportStatus.EXPLICITLY_SUPPORTED: Decimal("1.0"),
    SupportStatus.PARTIALLY_SUPPORTED: Decimal("0.5"),
    SupportStatus.NOT_MENTIONED: Decimal("0.0"),
}

_IMPORTANCE_MULTIPLIER: dict[ImportanceLevel, Decimal] = {
    ImportanceLevel.REQUIRED: Decimal("1.5"),
    ImportanceLevel.PREFERRED: Decimal("1.0"),
}


def calculate_match_score(requirements: List[RequirementMatch]) -> int:
    """
    Return an integer match score in [0, 100].

    Returns 0 safely when the requirements list is empty (no divide-by-zero).
    Uses Decimal arithmetic and ROUND_HALF_UP for deterministic results.
    """
    if not requirements:
        return 0

    total_possible = Decimal("0")
    total_achieved = Decimal("0")

    for req in requirements:
        multiplier = _IMPORTANCE_MULTIPLIER[req.importance]
        weight = _STATUS_WEIGHT[req.status]
        total_possible += multiplier
        total_achieved += weight * multiplier

    if total_possible == 0:
        return 0

    raw_percentage = (total_achieved / total_possible) * Decimal("100")
    rounded = int(raw_percentage.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return rounded


def _format_points(val: float) -> str:
    """Format points cleanly without banker's rounding truncation (e.g. 2.0 -> '2.0', 5.25 -> '5.25')."""
    if round(val * 10) == round(val * 100) / 10:
        return f"{val:.1f}"
    return f"{val:.2f}"


def get_alignment_label(score: int) -> str:
    """Return deterministic evidence alignment label consistent across backend and frontend."""
    if score >= 75:
        return "Strong Evidence Alignment"
    elif score >= 50:
        return "Moderate Alignment"
    return "Partial Evidence Match"


def build_scoring_methodology_text(
    requirements: List[RequirementMatch], score: int
) -> str:
    """
    Produce a human-readable explanation of how the score was calculated,
    so the result is transparent and reproducible by the candidate.
    """
    if not requirements:
        return "No requirements could be extracted from the job description. Score defaults to 0."

    total_possible = sum(
        float(_IMPORTANCE_MULTIPLIER[r.importance]) for r in requirements
    )
    total_achieved = sum(
        float(_STATUS_WEIGHT[r.status]) * float(_IMPORTANCE_MULTIPLIER[r.importance])
        for r in requirements
    )
    n = len(requirements)
    req_counts = {
        ImportanceLevel.REQUIRED: sum(
            1 for r in requirements if r.importance == ImportanceLevel.REQUIRED
        ),
        ImportanceLevel.PREFERRED: sum(
            1 for r in requirements if r.importance == ImportanceLevel.PREFERRED
        ),
    }

    achieved_str = _format_points(total_achieved)
    possible_str = _format_points(total_possible)
    alignment_str = get_alignment_label(score)

    return (
        f"Weighted evidence calculation across {n} extracted requirements "
        f"({req_counts[ImportanceLevel.REQUIRED]} required @ 1.5×, "
        f"{req_counts[ImportanceLevel.PREFERRED]} preferred @ 1.0×). "
        f"Points achieved: {achieved_str} / {possible_str} "
        f"= {score}% ({alignment_str})."
    )
