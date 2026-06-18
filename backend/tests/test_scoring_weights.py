"""Unit tests for per-question weighting and Watermark doctrine weights."""
from app.services.scoring_engine import QuestionScore, calculate_pillar_scores
from app.services.doctrinal_framework import doctrinal_question_weight


def test_equal_weights_is_plain_average():
    qs = [
        QuestionScore(1, "spiritual_discipline", 100.0, "likert"),
        QuestionScore(2, "spiritual_discipline", 0.0, "likert"),
    ]
    r = calculate_pillar_scores(qs)
    assert r["spiritual_discipline"].normalized_score == 50.0


def test_weighted_average_shifts_toward_heavier_question():
    qs = [
        QuestionScore(1, "doctrinal_integrity", 100.0, "likert", weight=3.0),
        QuestionScore(2, "doctrinal_integrity", 0.0, "likert", weight=1.0),
    ]
    r = calculate_pillar_scores(qs)
    assert r["doctrinal_integrity"].normalized_score == 75.0  # (100*3 + 0*1) / 4


def test_doctrine_weights_match_framework():
    assert doctrinal_question_weight(1) == 2.0    # salvation
    assert doctrinal_question_weight(2) == 1.75   # scripture
    assert doctrinal_question_weight(6) == 1.5    # trinity
    assert doctrinal_question_weight(9) == 0.75   # eschatology


def test_unmapped_question_defaults_to_one():
    assert doctrinal_question_weight(10) == 1.0   # forced prioritization
    assert doctrinal_question_weight(999) == 1.0
