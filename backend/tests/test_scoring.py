"""
Tests for the BHIS scoring engine.
Run: pytest tests/ -v
"""
import pytest
from app.services.scoring_engine import (
    QuestionScore, score_individual,
    normalize_likert, normalize_option_score,
    calculate_pillar_scores, detect_contradictions,
    calculate_drift, classify_maturity,
    PILLARS,
)

# ── Normalization ─────────────────────────────────────────────────────────────

def test_normalize_likert_min():
    assert normalize_likert(1) == 0.0

def test_normalize_likert_max():
    assert normalize_likert(5) == 100.0

def test_normalize_likert_mid():
    assert normalize_likert(3) == 50.0

def test_normalize_option_passthrough():
    assert normalize_option_score(80) == 80.0

# ── Maturity tiers ────────────────────────────────────────────────────────────

def test_tier_multiplying():
    assert classify_maturity(90) == "Multiplying Disciple"

def test_tier_grounded():
    assert classify_maturity(70) == "Grounded"

def test_tier_growing():
    assert classify_maturity(55) == "Growing"

def test_tier_nominal():
    assert classify_maturity(30) == "Nominal"

def test_tier_disengaged():
    assert classify_maturity(10) == "Spiritually Disengaged"

def test_tier_boundary_grounded_multiplying():
    assert classify_maturity(81) == "Multiplying Disciple"
    assert classify_maturity(80) == "Grounded"

# ── Pillar scoring ────────────────────────────────────────────────────────────

def _make_scores(pillar: str, values: list, q_start: int = 1) -> list:
    return [
        QuestionScore(
            question_number=q_start + i,
            pillar=pillar,
            normalized_score=v,
            question_type="likert",
        )
        for i, v in enumerate(values)
    ]

def test_pillar_scores_single_pillar():
    scores = _make_scores("doctrinal_integrity", [100, 80, 60])
    results = calculate_pillar_scores(scores)
    assert "doctrinal_integrity" in results
    assert abs(results["doctrinal_integrity"].normalized_score - 80.0) < 0.01

def test_pillar_status_strength():
    scores = _make_scores("doctrinal_integrity", [100, 90, 80])
    results = calculate_pillar_scores(scores)
    assert results["doctrinal_integrity"].status == "strength"

def test_pillar_status_gap():
    scores = _make_scores("doctrinal_integrity", [40, 30, 35])
    results = calculate_pillar_scores(scores)
    assert results["doctrinal_integrity"].status in ("gap", "significant_gap")

def test_qualitative_only_questions_excluded():
    scores = [
        QuestionScore(question_number=1, pillar="doctrinal_integrity", normalized_score=100, question_type="open_ended", qualitative_only=True),
        QuestionScore(question_number=2, pillar="doctrinal_integrity", normalized_score=50, question_type="likert"),
    ]
    results = calculate_pillar_scores(scores)
    assert results["doctrinal_integrity"].normalized_score == 50.0
    assert results["doctrinal_integrity"].question_count == 1

# ── Contradiction detection ───────────────────────────────────────────────────

def test_contradiction_cp01_flagged():
    # Q2 high (Scripture authority), Q11 low (Bible reading)
    scores = {2: 90.0, 11: 10.0}
    results = detect_contradictions(scores)
    cp01 = next(r for r in results if r.pair_id == "CP-01")
    assert cp01.flagged is True

def test_contradiction_cp01_not_flagged():
    # Both high — consistent
    scores = {2: 90.0, 11: 80.0}
    results = detect_contradictions(scores)
    cp01 = next(r for r in results if r.pair_id == "CP-01")
    assert cp01.flagged is False

def test_contradiction_cp07_flagged():
    # Says shaped by Scripture (Q55 high) but folds under pressure (Q54 low)
    scores = {55: 90.0, 54: 20.0}
    results = detect_contradictions(scores)
    cp07 = next(r for r in results if r.pair_id == "CP-07")
    assert cp07.flagged is True

def test_contradiction_missing_question_skipped():
    # Only one question in the pair present — engine skips the pair entirely
    scores = {2: 90.0}  # Q11 missing
    results = detect_contradictions(scores)
    cp01_results = [r for r in results if r.pair_id == "CP-01"]
    assert len(cp01_results) == 0

# ── Drift detection ───────────────────────────────────────────────────────────

def test_drift_none():
    scores = {53: 100, 54: 100, 55: 100, 57: 100, 59: 100}
    count, level = calculate_drift(scores)
    assert count == 0
    assert level == "low"

def test_drift_moderate():
    scores = {53: 20, 54: 20, 55: 20, 57: 100, 59: 100}
    count, level = calculate_drift(scores)
    assert count == 3
    assert level == "moderate"

def test_drift_high():
    scores = {53: 20, 54: 20, 55: 20, 57: 20, 59: 100}
    count, level = calculate_drift(scores)
    assert count == 4
    assert level == "high"

def test_drift_critical():
    scores = {53: 20, 54: 20, 55: 20, 57: 20, 59: 20}
    count, level = calculate_drift(scores)
    assert count == 5
    assert level == "critical"

# ── Full scoring pipeline ─────────────────────────────────────────────────────

def _make_healthy_respondent() -> list:
    """A respondent who scores high on everything."""
    qs = []
    q = 1
    for pillar in PILLARS:
        for _ in range(8):
            qs.append(QuestionScore(
                question_number=q,
                pillar=pillar,
                normalized_score=85.0,
                question_type="likert",
            ))
            q += 1
    return qs

def _make_struggling_respondent() -> list:
    """A respondent who scores low with contradictions."""
    qs = []
    q = 1
    for pillar in PILLARS:
        for _ in range(8):
            qs.append(QuestionScore(
                question_number=q,
                pillar=pillar,
                normalized_score=30.0,
                question_type="likert",
            ))
            q += 1
    # Add specific contradiction triggers
    qs.append(QuestionScore(question_number=2, pillar="doctrinal_integrity", normalized_score=95.0, question_type="likert"))
    qs.append(QuestionScore(question_number=11, pillar="spiritual_discipline", normalized_score=5.0, question_type="behavioral_frequency"))
    return qs

def test_full_pipeline_healthy_respondent():
    qs = _make_healthy_respondent()
    result = score_individual(qs)
    assert result.composite_score > 70
    assert result.maturity_tier in ("Grounded", "Multiplying Disciple")
    assert result.contradiction_count == 0
    assert result.credibility_warning is False
    assert result.drift_risk_level in ("low", "moderate")

def test_full_pipeline_struggling_respondent():
    qs = _make_struggling_respondent()
    result = score_individual(qs)
    assert result.composite_score < 50
    assert result.maturity_tier in ("Spiritually Disengaged", "Nominal", "Growing")

def test_composite_capped_at_100():
    # Even with all perfect scores, composite should not exceed 100
    qs = [
        QuestionScore(question_number=i, pillar="doctrinal_integrity", normalized_score=100.0, question_type="likert")
        for i in range(1, 11)
    ]
    result = score_individual(qs)
    assert result.composite_score <= 100.0

def test_composite_floored_at_0():
    # Even with penalties, composite should not go below 0
    qs = [
        QuestionScore(question_number=i, pillar="doctrinal_integrity", normalized_score=0.0, question_type="likert")
        for i in range(1, 11)
    ]
    result = score_individual(qs)
    assert result.composite_score >= 0.0

def test_credibility_warning_triggered():
    # Build a respondent with 3+ contradiction flags
    qs = [
        # CP-01: Q2 high, Q11 low
        QuestionScore(question_number=2, pillar="doctrinal_integrity", normalized_score=95.0, question_type="likert"),
        QuestionScore(question_number=11, pillar="spiritual_discipline", normalized_score=5.0, question_type="behavioral_frequency"),
        # CP-02: Q13 high, Q12 low, Q16 low
        QuestionScore(question_number=13, pillar="spiritual_discipline", normalized_score=95.0, question_type="likert"),
        QuestionScore(question_number=12, pillar="spiritual_discipline", normalized_score=5.0, question_type="behavioral_frequency"),
        QuestionScore(question_number=16, pillar="spiritual_discipline", normalized_score=5.0, question_type="behavioral_frequency"),
        # CP-07: Q55 high, Q54 low
        QuestionScore(question_number=55, pillar="drift_vulnerability", normalized_score=95.0, question_type="likert"),
        QuestionScore(question_number=54, pillar="drift_vulnerability", normalized_score=5.0, question_type="scenario"),
        # Fill remaining pillars
        *[QuestionScore(question_number=100 + i, pillar=p, normalized_score=50.0, question_type="likert")
          for i, p in enumerate(PILLARS)],
    ]
    result = score_individual(qs)
    assert result.contradiction_count >= 3
    assert result.credibility_warning is True
