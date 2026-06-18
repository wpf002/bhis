"""
Tests for archetype classification and recommendation engine.
"""
import pytest
from app.services.archetype_engine import classify_archetype
from app.services.recommendation_engine import (
    generate_church_recommendations,
    generate_individual_recommendations,
)

# ── Archetype classification ───────────────────────────────────────────────────

def _scores(**kwargs):
    base = {
        "doctrinal_integrity": 60,
        "spiritual_discipline": 60,
        "transformation_fruit": 60,
        "discipleship_depth": 60,
        "church_health_trust": 60,
        "engagement_alignment": 60,
        "drift_vulnerability": 60,
    }
    base.update(kwargs)
    return base


def test_archetype_disciple_making():
    scores = _scores(**{k: 80 for k in ["doctrinal_integrity", "spiritual_discipline", "transformation_fruit", "discipleship_depth", "church_health_trust", "engagement_alignment", "drift_vulnerability"]})
    result = classify_archetype(scores)
    assert result == "Disciple-Making Church"


def test_archetype_orthodoxy_without_obedience():
    scores = _scores(doctrinal_integrity=75, transformation_fruit=45)
    result = classify_archetype(scores)
    assert result == "Orthodoxy Without Obedience"


def test_archetype_consumer_church():
    scores = _scores(engagement_alignment=72, discipleship_depth=38)
    result = classify_archetype(scores)
    assert result == "Consumer Church"


def test_archetype_trust_fracture():
    scores = _scores(church_health_trust=35)
    result = classify_archetype(scores)
    assert result == "Trust Fracture"


def test_archetype_high_energy_low_doctrine():
    scores = _scores(engagement_alignment=75, doctrinal_integrity=45)
    result = classify_archetype(scores)
    assert result == "High Energy, Low Doctrine"


def test_archetype_drift_risk():
    scores = _scores(drift_vulnerability=30)
    result = classify_archetype(scores)
    assert result == "Drift Risk Church"


def test_archetype_fallback():
    # A profile that doesn't match any specific archetype
    scores = _scores(**{k: 60 for k in ["doctrinal_integrity", "spiritual_discipline",
                                          "transformation_fruit", "discipleship_depth",
                                          "church_health_trust", "engagement_alignment"]})
    result = classify_archetype(scores)
    # Should return some valid archetype or fallback
    assert isinstance(result, str)
    assert len(result) > 0


# ── Church recommendations ────────────────────────────────────────────────────

def test_church_recommendations_trust_crisis():
    scores = _scores(church_health_trust=35)
    recs = generate_church_recommendations(scores, "Trust Fracture")
    assert len(recs) >= 1
    trust_rec = next((r for r in recs if r.pillar == "church_health_trust"), None)
    assert trust_rec is not None
    assert trust_rec.urgency == "HIGH"


def test_church_recommendations_discipleship_gap():
    scores = _scores(discipleship_depth=35)
    recs = generate_church_recommendations(scores, "Consumer Church")
    disc_rec = next((r for r in recs if r.pillar == "discipleship_depth"), None)
    assert disc_rec is not None
    assert disc_rec.urgency == "HIGH"


def test_church_recommendations_max_count():
    # A church with all low scores should not return more than max
    scores = _scores(**{k: 25 for k in _scores().keys()})
    recs = generate_church_recommendations(scores, "Plateau Church", max_recommendations=3)
    assert len(recs) <= 3


def test_church_recommendations_priority_ordering():
    scores = _scores(church_health_trust=30, discipleship_depth=30, drift_vulnerability=25)
    recs = generate_church_recommendations(scores, "Fragmentation Risk")
    priorities = [r.priority for r in recs]
    assert priorities == sorted(priorities)


def test_church_recommendations_healthy_church():
    # Healthy church should have fewer or no recommendations
    scores = _scores(**{k: 80 for k in _scores().keys()})
    recs = generate_church_recommendations(scores, "Disciple-Making Church")
    assert len(recs) == 0


# ── Individual recommendations ────────────────────────────────────────────────

def test_individual_recommendations_discipleship_gap():
    scores = {"discipleship_depth": 35, "spiritual_discipline": 70, "transformation_fruit": 70}
    recs = generate_individual_recommendations(scores, "Growing", False)
    assert any(r.pillar == "discipleship_depth" for r in recs)


def test_individual_recommendations_max_3():
    scores = {k: 25 for k in ["discipleship_depth", "spiritual_discipline", "transformation_fruit", "doctrinal_integrity"]}
    recs = generate_individual_recommendations(scores, "Nominal", False)
    assert len(recs) <= 3


def test_individual_recommendations_healthy():
    scores = {k: 85 for k in ["discipleship_depth", "spiritual_discipline", "transformation_fruit", "doctrinal_integrity"]}
    recs = generate_individual_recommendations(scores, "Multiplying Disciple", False)
    assert len(recs) == 0


def test_individual_recommendations_have_biblical_anchor():
    scores = {"discipleship_depth": 35}
    recs = generate_individual_recommendations(scores, "Nominal", False)
    for r in recs:
        assert r.biblical_anchor
        assert len(r.biblical_anchor) > 10
