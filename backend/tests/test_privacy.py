"""
Tests for the anonymity minimum-N suppression floor.
Run: pytest tests/ -v
"""
from app.services.privacy import (
    MIN_N_DEFAULT,
    HARD_FLOOR,
    resolve_min_n,
    is_below_floor,
    suppressed_payload,
    apply_min_n_floor,
    SUPPRESSION_REASON,
)

SAMPLE_AGG = {
    "health_score": 72.5,
    "archetype": "Quietly Healthy",
    "pillar_scores": {"doctrinal_integrity": 80.0, "discipleship_depth": 61.0},
    "maturity_distribution": {"Grounded": 12, "Growing": 8},
    "drift_risk_level": "low",
    "drift_risk_score": -2.0,
}

# ── resolve_min_n ─────────────────────────────────────────────────────────────

def test_resolve_min_n_default():
    assert resolve_min_n() == MIN_N_DEFAULT
    assert resolve_min_n(None) == MIN_N_DEFAULT

def test_resolve_min_n_override_raises_threshold():
    assert resolve_min_n(25) == 25

def test_resolve_min_n_override_clamped_to_hard_floor():
    # A configured value below the hard floor cannot weaken anonymity.
    assert resolve_min_n(3) == HARD_FLOOR
    assert resolve_min_n(HARD_FLOOR - 1) == HARD_FLOOR

def test_hard_floor_not_above_default():
    assert HARD_FLOOR <= MIN_N_DEFAULT

# ── is_below_floor ────────────────────────────────────────────────────────────

def test_is_below_floor_true_when_under():
    assert is_below_floor(14) is True

def test_is_below_floor_false_at_threshold():
    assert is_below_floor(MIN_N_DEFAULT) is False

def test_is_below_floor_false_when_over():
    assert is_below_floor(40) is False

def test_is_below_floor_handles_none_as_zero():
    assert is_below_floor(None) is True

def test_is_below_floor_zero():
    assert is_below_floor(0) is True

def test_is_below_floor_respects_custom_min_n():
    assert is_below_floor(18, min_n=20) is True
    assert is_below_floor(20, min_n=20) is False

# ── suppressed_payload ────────────────────────────────────────────────────────

def test_suppressed_payload_shape():
    p = suppressed_payload(7)
    assert p["suppressed"] is True
    assert p["reason"] == SUPPRESSION_REASON
    assert p["respondent_count"] == 7
    assert p["min_n"] == MIN_N_DEFAULT
    assert "15" in p["message"]

def test_suppressed_payload_leaks_no_breakdown_fields():
    p = suppressed_payload(7)
    for leaked in ("health_score", "archetype", "pillar_scores", "maturity_distribution"):
        assert leaked not in p

def test_suppressed_payload_none_count():
    assert suppressed_payload(None)["respondent_count"] == 0

# ── apply_min_n_floor ─────────────────────────────────────────────────────────

def test_apply_floor_suppresses_below_threshold():
    out = apply_min_n_floor(SAMPLE_AGG, respondent_count=9)
    assert out["suppressed"] is True
    assert "pillar_scores" not in out
    assert "health_score" not in out

def test_apply_floor_passes_through_at_threshold():
    out = apply_min_n_floor(SAMPLE_AGG, respondent_count=MIN_N_DEFAULT)
    assert out["suppressed"] is False
    assert out["health_score"] == 72.5
    assert out["pillar_scores"]["doctrinal_integrity"] == 80.0
    assert out["respondent_count"] == MIN_N_DEFAULT
    assert out["min_n"] == MIN_N_DEFAULT

def test_apply_floor_passes_through_above_threshold():
    out = apply_min_n_floor(SAMPLE_AGG, respondent_count=120)
    assert out["suppressed"] is False
    assert out["archetype"] == "Quietly Healthy"

def test_apply_floor_does_not_mutate_input():
    before = dict(SAMPLE_AGG)
    apply_min_n_floor(SAMPLE_AGG, respondent_count=50)
    assert SAMPLE_AGG == before
    assert "suppressed" not in SAMPLE_AGG

def test_apply_floor_custom_min_n():
    out = apply_min_n_floor(SAMPLE_AGG, respondent_count=18, min_n=20)
    assert out["suppressed"] is True
