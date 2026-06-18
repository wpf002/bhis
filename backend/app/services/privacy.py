"""
Privacy enforcement for church-facing aggregate views.

The Critical risk in the roadmap is a church re-identifying an individual member
from an aggregate. Severing identity at the data layer (capability-token report
retrieval, dropping respondent_sessions.user_id) is the other half of the
defense and lands in a separate phase. This module handles the second vector:
**small-N de-anonymization** — when so few people responded that an aggregate
effectively points at named individuals.

Rule: no church-facing aggregate breakdown renders below a minimum respondent
count (``N_MIN``). See docs/anonymity-design.md.

These are pure functions with no DB/HTTP dependencies so they can be unit-tested
directly, matching the existing scoring-engine test style.
"""
from typing import Any, Dict, Mapping, Optional

# Default floor for 150–600-member churches (see anonymity design doc, decided 2026-06-18).
MIN_N_DEFAULT = 15

# Absolute floor: a church/instance setting may RAISE the threshold but never lower it past this.
HARD_FLOOR = 10

# Fields that constitute a re-identifying breakdown and must be withheld below the floor.
SUPPRESSED_FIELDS = (
    "health_score",
    "archetype",
    "pillar_scores",
    "maturity_distribution",
    "drift_risk_score",
    "drift_risk_level",
)

SUPPRESSION_REASON = "below_anonymity_threshold"


def resolve_min_n(configured: Optional[int] = None) -> int:
    """Resolve the effective floor for a church/instance.

    ``configured`` is the optional per-church/instance override (a future
    settings column). ``None`` → the default. Any override is clamped UP to the
    hard floor so anonymity can be strengthened but never weakened below it.
    """
    if configured is None:
        return MIN_N_DEFAULT
    return max(int(configured), HARD_FLOOR)


def is_below_floor(respondent_count: Optional[int], min_n: int = MIN_N_DEFAULT) -> bool:
    """True when there are too few respondents to safely show a breakdown."""
    return (respondent_count or 0) < min_n


def suppressed_payload(respondent_count: Optional[int], min_n: int = MIN_N_DEFAULT) -> Dict[str, Any]:
    """The placeholder returned in lieu of a real aggregate when below the floor."""
    count = respondent_count or 0
    return {
        "suppressed": True,
        "reason": SUPPRESSION_REASON,
        "respondent_count": count,
        "min_n": min_n,
        "message": (
            f"Not enough responses yet to protect anonymity — "
            f"need at least {min_n} (have {count})."
        ),
    }


def apply_min_n_floor(
    aggregate: Mapping[str, Any],
    respondent_count: Optional[int],
    min_n: int = MIN_N_DEFAULT,
) -> Dict[str, Any]:
    """Gate a church-facing aggregate behind the minimum-N floor.

    Below the floor, return only the suppression placeholder (no breakdown
    fields, no recommendations leak through). At or above the floor, return the
    aggregate annotated with ``suppressed: False`` and the floor metadata so the
    client can render an honest "anonymity protected" indicator.
    """
    if is_below_floor(respondent_count, min_n):
        return suppressed_payload(respondent_count, min_n)
    result: Dict[str, Any] = dict(aggregate)
    result["suppressed"] = False
    result["respondent_count"] = respondent_count
    result["min_n"] = min_n
    return result
