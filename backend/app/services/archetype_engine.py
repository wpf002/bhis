"""
BHIS Archetype Engine
---------------------
Classifies churches based on their pillar score profile, not just composite score.
Pattern matching runs in priority order — first match wins.
"""

from typing import Dict, Optional


ARCHETYPES = [
    {
        "id": "disciple_making_church",
        "label": "Disciple-Making Church",
        "description": "Consistently healthy across all dimensions. Rare. Worth studying and celebrating.",
        "condition": lambda p: all(v >= 70 for v in p.values()),
    },
    {
        "id": "drift_risk",
        "label": "Drift Risk Church",
        "description": "Cultural accommodation is accelerating. Worldview is softening. High urgency.",
        "condition": lambda p: p.get("drift_vulnerability", 100) <= 35,
    },
    {
        "id": "fragmentation_risk",
        "label": "Fragmentation Risk",
        "description": "People are pulling back. Trust is low. Without intervention, this church will fracture.",
        "condition": lambda p: p.get("church_health_trust", 100) <= 40 and p.get("engagement_alignment", 100) <= 45,
    },
    {
        "id": "trust_fracture",
        "label": "Trust Fracture",
        "description": "Leadership trust is the primary issue. Likely driving disengagement and attrition.",
        "condition": lambda p: p.get("church_health_trust", 100) <= 40,
    },
    {
        "id": "orthodoxy_without_obedience",
        "label": "Orthodoxy Without Obedience",
        "description": "Knows the truth but doesn't live it. Preaches well but lacks application structures.",
        "condition": lambda p: (
            p.get("doctrinal_integrity", 0) >= 68
            and p.get("transformation_fruit", 100) <= 52
        ),
    },
    {
        "id": "high_energy_low_doctrine",
        "label": "High Energy, Low Doctrine",
        "description": "Active, enthusiastic — but doctrinally shallow. Risk of drift over time.",
        "condition": lambda p: (
            p.get("engagement_alignment", 0) >= 68
            and p.get("doctrinal_integrity", 100) <= 52
        ),
    },
    {
        "id": "consumer_church",
        "label": "Consumer Church",
        "description": "People show up and even serve, but no one is making disciples. Receiver culture.",
        "condition": lambda p: (
            p.get("engagement_alignment", 0) >= 60
            and p.get("discipleship_depth", 100) <= 42
        ),
    },
    {
        "id": "gathering_without_discipling",
        "label": "Gathering Without Discipling",
        "description": "Good services, decent community — but multiplication is missing.",
        "condition": lambda p: p.get("discipleship_depth", 100) <= 42,
    },
    {
        "id": "warmth_without_depth",
        "label": "Warmth Without Depth",
        "description": "People love the church and each other, but doctrinal clarity is weak.",
        "condition": lambda p: (
            p.get("church_health_trust", 0) >= 68
            and p.get("doctrinal_integrity", 100) <= 55
        ),
    },
    {
        "id": "equipped_but_not_sending",
        "label": "Equipped But Not Sending",
        "description": "Solid internal culture. Strong teaching. But the Great Commission is not happening.",
        "condition": lambda p: (
            p.get("doctrinal_integrity", 0) >= 68
            and p.get("spiritual_discipline", 0) >= 62
            and p.get("discipleship_depth", 100) <= 47
        ),
    },
    {
        "id": "plateau_church",
        "label": "Plateau Church",
        "description": "Stuck. Not failing, not thriving. Needs catalytic pastoral vision.",
        "condition": lambda p: all(45 <= v <= 65 for v in p.values()),
    },
    {
        "id": "quietly_healthy",
        "label": "Quietly Healthy",
        "description": "Solid but not stellar. A mature, stable congregation. Watch for plateau.",
        "condition": lambda p: all(55 <= v <= 72 for v in p.values()),
    },
]


def classify_archetype(pillar_scores: Dict[str, float]) -> str:
    """
    Returns the archetype label for a church based on its pillar score profile.
    First match wins. Falls back to 'Developing Church' if no pattern matches.
    """
    for archetype in ARCHETYPES:
        try:
            if archetype["condition"](pillar_scores):
                return archetype["label"]
        except Exception:
            continue

    return "Developing Church"


def get_archetype_description(label: str) -> Optional[str]:
    for a in ARCHETYPES:
        if a["label"] == label:
            return a["description"]
    return None
