"""
Tests for the minimum-N suppression mechanism.

NOTE: the floor is OFF by default (MIN_N_DEFAULT = 1) per the 2026-06-19 product
decision — results render from the first response. The suppression *mechanism*
is still exercised here with an explicit min_n so a floor can be re-enabled later.
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

# ── default: floor is off ─────────────────────────────────────────────────────

def test_floor_is_disabled_by_default():
    assert MIN_N_DEFAULT == 1
    # With the floor off, any real aggregate (>=1 respondent) renders.
    assert is_below_floor(1) is False
    assert is_below_floor(2) is False
    assert is_below_floor(40) is False
    # Only an empty (0 / None) aggregate is withheld.
    assert is_below_floor(0) is True
    assert is_below_floor(None) is True

# ── resolve_min_n (a per-church override can re-enable a floor) ────────────────

def test_resolve_min_n_default():
    assert resolve_min_n() == MIN_N_DEFAULT
    assert resolve_min_n(None) == MIN_N_DEFAULT

def test_resolve_min_n_override_raises_threshold():
    assert resolve_min_n(25) == 25

def test_resolve_min_n_clamped_to_hard_floor():
    assert resolve_min_n(0) == HARD_FLOOR
    assert resolve_min_n(HARD_FLOOR) == HARD_FLOOR

def test_hard_floor_not_above_default():
    assert HARD_FLOOR <= MIN_N_DEFAULT

# ── is_below_floor with an explicit floor (mechanism still works) ─────────────

def test_is_below_floor_respects_custom_min_n():
    assert is_below_floor(18, min_n=20) is True
    assert is_below_floor(20, min_n=20) is False

# ── suppressed_payload ────────────────────────────────────────────────────────

def test_suppressed_payload_shape():
    p = suppressed_payload(7, min_n=20)
    assert p["suppressed"] is True
    assert p["reason"] == SUPPRESSION_REASON
    assert p["respondent_count"] == 7
    assert p["min_n"] == 20
    assert "20" in p["message"]

def test_suppressed_payload_leaks_no_breakdown_fields():
    p = suppressed_payload(7, min_n=20)
    for leaked in ("health_score", "archetype", "pillar_scores", "maturity_distribution"):
        assert leaked not in p

def test_suppressed_payload_none_count():
    assert suppressed_payload(None)["respondent_count"] == 0

# ── apply_min_n_floor (with an explicit floor) ────────────────────────────────

def test_apply_floor_suppresses_below_explicit_threshold():
    out = apply_min_n_floor(SAMPLE_AGG, respondent_count=9, min_n=20)
    assert out["suppressed"] is True
    assert "pillar_scores" not in out
    assert "health_score" not in out

def test_apply_floor_passes_through_by_default():
    # Default floor is off, so a 2-respondent aggregate renders.
    out = apply_min_n_floor(SAMPLE_AGG, respondent_count=2)
    assert out["suppressed"] is False
    assert out["health_score"] == 72.5
    assert out["pillar_scores"]["doctrinal_integrity"] == 80.0

def test_apply_floor_does_not_mutate_input():
    before = dict(SAMPLE_AGG)
    apply_min_n_floor(SAMPLE_AGG, respondent_count=50)
    assert SAMPLE_AGG == before
    assert "suppressed" not in SAMPLE_AGG
