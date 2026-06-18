"""
BHIS Scoring Engine
-------------------
Implements the full scoring algorithm from the blueprint:
  - Per-pillar normalized scores (0-100)
  - Weighted composite score
  - Contradiction detection (7 pairs)
  - Drift signal detection
  - Maturity tier classification
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ── Constants ─────────────────────────────────────────────────────────────────

PILLARS = [
    "doctrinal_integrity",
    "spiritual_discipline",
    "transformation_fruit",
    "discipleship_depth",
    "church_health_trust",
    "engagement_alignment",
    "drift_vulnerability",
]

PILLAR_WEIGHTS = {
    "doctrinal_integrity":  0.20,
    "spiritual_discipline": 0.15,
    "transformation_fruit": 0.20,
    "discipleship_depth":   0.15,
    "church_health_trust":  0.12,
    "engagement_alignment": 0.10,
    # drift_vulnerability is a modifier, not a weighted pillar
}

MATURITY_TIERS = [
    (81, 100, "Multiplying Disciple"),
    (61, 80,  "Grounded"),
    (41, 60,  "Growing"),
    (21, 40,  "Nominal"),
    (0,  20,  "Spiritually Disengaged"),
]

PILLAR_STATUS_THRESHOLDS = {
    "strength":       70,
    "moderate":       50,
    "gap":            35,
    # below 35 = significant_gap
}

# Contradiction pairs: (pair_id, q_a_number, q_b_number, flag_if_a_gte, flag_if_b_lte)
CONTRADICTION_PAIRS: List[Tuple[str, int, int, float, float]] = [
    ("CP-01", 2,  11, 80.0, 25.0),   # Scripture authority vs reading frequency
    ("CP-02", 13, 16, 80.0, 25.0),   # Prayer dependence vs actual prayer days
    ("CP-03", 5,  33, 80.0, 40.0),   # Gospel confidence vs gospel scenario
    ("CP-04", 23, 22, 80.0, 40.0),   # Life consistency vs scenario response
    ("CP-05", 38, 40, 80.0, 40.0),   # Leadership trust vs safety scenario
    ("CP-06", 49, 47, 80.0, 25.0),   # Beyond attending vs actual involvement
    ("CP-07", 55, 54, 80.0, 40.0),   # Shaped by Scripture vs cultural pressure
]

# Drift signal questions and their threshold (score <= threshold triggers signal)
DRIFT_SIGNAL_QUESTIONS: List[Tuple[int, float]] = [
    (53, 40),  # Moral relativism / soft pluralism
    (54, 40),  # Cultural accommodation under pressure
    (55, 40),  # Shaped more by culture than Scripture
    (57, 40),  # Attends out of habit only
    (59, 40),  # Low life change admission
]


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class QuestionScore:
    question_number: int
    pillar: str
    normalized_score: float  # 0-100
    question_type: str
    qualitative_only: bool = False


@dataclass
class PillarResult:
    pillar: str
    raw_score: float
    normalized_score: float
    question_count: int
    status: str


@dataclass
class ContradictionResult:
    pair_id: str
    question_a: int
    question_b: int
    score_a: float
    score_b: float
    delta: float
    flagged: bool


@dataclass
class ScoringResult:
    composite_score: float
    maturity_tier: str
    pillar_results: Dict[str, PillarResult]
    contradiction_results: List[ContradictionResult]
    contradiction_count: int
    credibility_warning: bool
    drift_signal_count: int
    drift_risk_level: str
    drift_adjustment: float


# ── Normalization ─────────────────────────────────────────────────────────────

def normalize_likert(value: int) -> float:
    """Likert 1-5 → 0-100"""
    return (value - 1) / 4 * 100


def normalize_option_score(score_value: int) -> float:
    """Option score already 0-100"""
    return float(score_value)


# ── Pillar scoring ────────────────────────────────────────────────────────────

def calculate_pillar_scores(question_scores: List[QuestionScore]) -> Dict[str, PillarResult]:
    pillar_buckets: Dict[str, List[float]] = {p: [] for p in PILLARS}

    for qs in question_scores:
        if qs.qualitative_only:
            continue
        if qs.pillar in pillar_buckets:
            pillar_buckets[qs.pillar].append(qs.normalized_score)

    results = {}
    for pillar, scores in pillar_buckets.items():
        if not scores:
            results[pillar] = PillarResult(
                pillar=pillar,
                raw_score=0.0,
                normalized_score=0.0,
                question_count=0,
                status="gap",
            )
            continue

        raw = sum(scores) / len(scores)
        status = _pillar_status(raw)
        results[pillar] = PillarResult(
            pillar=pillar,
            raw_score=raw,
            normalized_score=round(raw, 2),
            question_count=len(scores),
            status=status,
        )

    return results


def _pillar_status(score: float) -> str:
    if score >= PILLAR_STATUS_THRESHOLDS["strength"]:
        return "strength"
    if score >= PILLAR_STATUS_THRESHOLDS["moderate"]:
        return "moderate"
    if score >= PILLAR_STATUS_THRESHOLDS["gap"]:
        return "gap"
    return "significant_gap"


# ── Drift detection ───────────────────────────────────────────────────────────

def calculate_drift(scores_by_qnum: Dict[int, float]) -> Tuple[int, str]:
    """Returns (signal_count, risk_level)"""
    count = 0
    for q_num, threshold in DRIFT_SIGNAL_QUESTIONS:
        score = scores_by_qnum.get(q_num)
        if score is not None and score <= threshold:
            count += 1

    if count == 0:
        level = "low"
    elif count <= 2:
        level = "low"
    elif count <= 3:
        level = "moderate"
    elif count <= 4:
        level = "high"
    else:
        level = "critical"

    return count, level


def calculate_drift_adjustment(signal_count: int) -> float:
    adjustments = {0: 0, 1: -2, 2: -4, 3: -6}
    return adjustments.get(signal_count, -8)


# ── Contradiction detection ───────────────────────────────────────────────────

def detect_contradictions(scores_by_qnum: Dict[int, float]) -> List[ContradictionResult]:
    results = []
    for pair_id, q_a, q_b, a_gte, b_lte in CONTRADICTION_PAIRS:
        score_a = scores_by_qnum.get(q_a)
        score_b = scores_by_qnum.get(q_b)

        if score_a is None or score_b is None:
            continue

        flagged = score_a >= a_gte and score_b <= b_lte
        results.append(ContradictionResult(
            pair_id=pair_id,
            question_a=q_a,
            question_b=q_b,
            score_a=round(score_a, 2),
            score_b=round(score_b, 2),
            delta=round(score_a - score_b, 2),
            flagged=flagged,
        ))

    return results


# ── Maturity tier ─────────────────────────────────────────────────────────────

def classify_maturity(composite: float) -> str:
    for low, high, label in MATURITY_TIERS:
        if low <= composite <= high:
            return label
    return "Spiritually Disengaged"


# ── Composite score ───────────────────────────────────────────────────────────

def calculate_composite(
    pillar_results: Dict[str, PillarResult],
    contradiction_count: int,
    drift_adjustment: float,
) -> float:
    weighted = sum(
        pillar_results[p].normalized_score * w
        for p, w in PILLAR_WEIGHTS.items()
        if p in pillar_results
    )
    contradiction_penalty = contradiction_count * 3
    composite = weighted - contradiction_penalty + drift_adjustment
    return round(max(0.0, min(100.0, composite)), 2)


# ── Main entry point ──────────────────────────────────────────────────────────

def score_individual(question_scores: List[QuestionScore]) -> ScoringResult:
    """
    Full individual scoring pipeline.

    Args:
        question_scores: list of QuestionScore objects (one per answered question)

    Returns:
        ScoringResult with all fields populated
    """
    scores_by_qnum = {qs.question_number: qs.normalized_score for qs in question_scores}

    # 1. Pillar scores
    pillar_results = calculate_pillar_scores(question_scores)

    # 2. Drift
    drift_count, drift_level = calculate_drift(scores_by_qnum)
    drift_adj = calculate_drift_adjustment(drift_count)

    # 3. Contradictions
    contradiction_results = detect_contradictions(scores_by_qnum)
    flagged = [c for c in contradiction_results if c.flagged]
    contradiction_count = len(flagged)
    credibility_warning = contradiction_count >= 3

    # 4. Composite
    composite = calculate_composite(pillar_results, contradiction_count, drift_adj)

    # 5. Maturity tier
    tier = classify_maturity(composite)

    return ScoringResult(
        composite_score=composite,
        maturity_tier=tier,
        pillar_results=pillar_results,
        contradiction_results=contradiction_results,
        contradiction_count=contradiction_count,
        credibility_warning=credibility_warning,
        drift_signal_count=drift_count,
        drift_risk_level=drift_level,
        drift_adjustment=drift_adj,
    )
