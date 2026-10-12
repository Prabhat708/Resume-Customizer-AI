"""
tests/test_scoring.py — Deterministic match score formula tests.

Verifies:
  1. Standard calculation: 5.0 / 6.5 → 77% (not 69% or 68%).
  2. Half-up rounding: 68.5% → 69%, 68.4% → 68%.
  3. Zero-requirement edge case → 0% (no divide-by-zero).
  4. All explicitly supported → 100%.
  5. All not mentioned → 0%.
  6. Mixed required/preferred weighting is applied correctly.

No API keys or external services are required.
"""
from __future__ import annotations

import pytest

from app.schemas.analysis import ImportanceLevel, RequirementMatch, SupportStatus
from app.services.scoring_service import calculate_match_score


def _req(
    importance: ImportanceLevel,
    status: SupportStatus,
    requirement: str = "test requirement",
) -> RequirementMatch:
    """Helper: build a minimal RequirementMatch for scoring tests."""
    return RequirementMatch(
        requirement=requirement,
        importance=importance,
        status=status,
        evidence_quote=None,
        notes="unit test fixture",
    )


# ── Test 1: Standard calculation matching the plan example ───────────────────
def test_standard_calculation_five_point_zero_over_six_point_five():
    """
    Replicates the plan's illustrative example:
      3 required, all explicitly_supported → 3 × (1.0 × 1.5) = 4.5
      1 preferred, partially_supported    → 1 × (0.5 × 1.0) = 0.5
      1 preferred, not_mentioned          → 1 × (0.0 × 1.0) = 0.0
      ──────────────────────────────────────────────────────────────
      achieved / possible = 5.0 / 6.5 = 76.923…% → rounds to 77
    """
    requirements = [
        _req(ImportanceLevel.REQUIRED, SupportStatus.EXPLICITLY_SUPPORTED, "Python REST API"),
        _req(ImportanceLevel.REQUIRED, SupportStatus.EXPLICITLY_SUPPORTED, "DB optimization"),
        _req(ImportanceLevel.REQUIRED, SupportStatus.EXPLICITLY_SUPPORTED, "Docker"),
        _req(ImportanceLevel.PREFERRED, SupportStatus.PARTIALLY_SUPPORTED, "FastAPI"),
        _req(ImportanceLevel.PREFERRED, SupportStatus.NOT_MENTIONED, "Kubernetes"),
    ]
    score = calculate_match_score(requirements)
    assert score == 77, f"Expected 77, got {score}"


# ── Test 2: Half-up rounding — exactly at 0.5 boundary rounds up ─────────────
def test_rounding_68_5_rounds_up_to_69():
    """
    Construct a requirement set whose exact ratio is 68.5%.
    Using Decimal ROUND_HALF_UP, 68.5 → 69.

    To get 68.5%:
      preferred only (multiplier 1.0):
        6 × explicit (weight 1.0) + 1 × partial (weight 0.5) + 6 × not_mentioned (0.0)
        achieved = 6.5, possible = 13, ratio = 6.5/13 = 50% — not right.

    Simplest direct approach: 1 required explicit + 1 required partial.
      achieved = 1×1.5 + 0.5×1.5 = 1.5 + 0.75 = 2.25
      possible = 1.5 + 1.5 = 3.0
      2.25 / 3.0 = 75% — not right.

    Use preferred only: 137 explicit + 3 partial + 60 not_mentioned:
      achieved = 137×1.0 + 3×0.5 = 138.5
      possible = 200
      = 69.25% → 69. Not 68.5%.

    Direct: 1 preferred partial = 0.5/1.0 = 50%. Too low.

    Best direct construction for exactly 68.5%:
      Use 200 preferred items:
        137 explicit: 137×1.0 = 137
        1 partial:      1×0.5 = 0.5
        62 not_mentioned: 0
        achieved = 137.5, possible = 200 → 68.75% → 69.

      136 explicit + 1 partial + 63 not_mentioned:
        achieved = 136.5, possible = 200 → 68.25% → 68.

    For exactly 68.5: need achieved/possible = 0.685.
      137/200 = 68.5% ✓  (137 explicit preferred, 63 not_mentioned)
    Wait: 137 × 1.0 + 63 × 0.0 = 137, possible = 200. 137/200 = 0.685 = 68.5% → ROUND_HALF_UP → 69 ✓
    """
    requirements = (
        [_req(ImportanceLevel.PREFERRED, SupportStatus.EXPLICITLY_SUPPORTED)] * 137
        + [_req(ImportanceLevel.PREFERRED, SupportStatus.NOT_MENTIONED)] * 63
    )
    score = calculate_match_score(requirements)
    assert score == 69, f"Expected 69 (half-up from 68.5%), got {score}"


def test_rounding_68_25_rounds_down_to_68():
    """
    136 explicit preferred + 1 partial preferred + 63 not_mentioned preferred:
      achieved = 136×1.0 + 1×0.5 + 63×0.0 = 136.5
      possible = 200
      136.5 / 200 = 68.25% → ROUND_HALF_UP → 68
    """
    requirements = (
        [_req(ImportanceLevel.PREFERRED, SupportStatus.EXPLICITLY_SUPPORTED)] * 136
        + [_req(ImportanceLevel.PREFERRED, SupportStatus.PARTIALLY_SUPPORTED)] * 1
        + [_req(ImportanceLevel.PREFERRED, SupportStatus.NOT_MENTIONED)] * 63
    )
    score = calculate_match_score(requirements)
    assert score == 68, f"Expected 68 (68.25% rounds down), got {score}"


# ── Test 3: Zero-requirement edge case ───────────────────────────────────────
def test_zero_requirements_returns_zero_not_error():
    """Empty requirement list must return 0, not raise ZeroDivisionError."""
    score = calculate_match_score([])
    assert score == 0, f"Expected 0 for empty requirements, got {score}"


# ── Test 4: All explicitly supported → 100% ──────────────────────────────────
def test_all_explicitly_supported_returns_100():
    requirements = [
        _req(ImportanceLevel.REQUIRED, SupportStatus.EXPLICITLY_SUPPORTED),
        _req(ImportanceLevel.PREFERRED, SupportStatus.EXPLICITLY_SUPPORTED),
        _req(ImportanceLevel.REQUIRED, SupportStatus.EXPLICITLY_SUPPORTED),
    ]
    score = calculate_match_score(requirements)
    assert score == 100, f"Expected 100, got {score}"


# ── Test 5: All not mentioned → 0% ───────────────────────────────────────────
def test_all_not_mentioned_returns_0():
    requirements = [
        _req(ImportanceLevel.REQUIRED, SupportStatus.NOT_MENTIONED),
        _req(ImportanceLevel.PREFERRED, SupportStatus.NOT_MENTIONED),
    ]
    score = calculate_match_score(requirements)
    assert score == 0, f"Expected 0, got {score}"


# ── Test 6: Mixed weighting applied correctly ─────────────────────────────────
def test_required_weight_higher_than_preferred():
    """
    Verify required (1.5×) outweighs preferred (1.0×).
    1 required explicit + 1 preferred not_mentioned:
      achieved = 1.0×1.5 + 0.0×1.0 = 1.5
      possible = 1.5 + 1.0 = 2.5
      1.5 / 2.5 = 60% → 60
    """
    requirements = [
        _req(ImportanceLevel.REQUIRED, SupportStatus.EXPLICITLY_SUPPORTED),
        _req(ImportanceLevel.PREFERRED, SupportStatus.NOT_MENTIONED),
    ]
    score = calculate_match_score(requirements)
    assert score == 60, f"Expected 60, got {score}"


def test_preferred_only_partial_returns_50():
    """
    1 preferred partially_supported:
      achieved = 0.5×1.0 = 0.5, possible = 1.0, ratio = 50%
    """
    requirements = [
        _req(ImportanceLevel.PREFERRED, SupportStatus.PARTIALLY_SUPPORTED),
    ]
    score = calculate_match_score(requirements)
    assert score == 50, f"Expected 50, got {score}"
