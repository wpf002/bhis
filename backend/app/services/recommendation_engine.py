"""
BHIS Recommendation Engine
--------------------------
Generates prioritized, actionable recommendations for churches and individuals
based on pillar scores, archetypes, and drift signals.
"""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class RecommendationOutput:
    priority: int
    pillar: str
    title: str
    urgency: str  # HIGH | MEDIUM | LOW
    diagnosis: str
    biblical_anchor: str
    intervention: str
    timeline: str


# Church-level recommendation rules (ordered by priority)
CHURCH_RULES = [
    {
        "pillar": "church_health_trust",
        "trigger": lambda scores, archetype: scores.get("church_health_trust", 100) <= 45,
        "urgency": "HIGH",
        "title": "Address Trust Crisis Before Everything Else",
        "diagnosis": "Trust in leadership is critically low. No other initiative will gain traction until this is addressed.",
        "biblical_anchor": "Hebrews 13:17; Ezekiel 34:4 — shepherds who neglect the flock will scatter it.",
        "intervention": "Pastoral team should initiate transparent listening sessions with the congregation. Acknowledge what hasn't worked. Create visible accountability. Trust is rebuilt through consistency over time, not announcements.",
        "timeline": "Immediate — within 30 days",
    },
    {
        "pillar": "drift_vulnerability",
        "trigger": lambda scores, archetype: scores.get("drift_vulnerability", 100) <= 38,
        "urgency": "HIGH",
        "title": "Counter Accelerating Worldview Drift",
        "diagnosis": "Significant drift signals across worldview, moral relativism, and cultural accommodation questions. The doctrinal floor is weakening.",
        "biblical_anchor": "Hebrews 2:1 — we must pay closer attention, lest we drift. 2 Timothy 4:3–4 — people will accumulate teachers that suit their passions.",
        "intervention": "Preach a direct series on the authority of Scripture and the cost of cultural compromise. Equip members with language to hold biblical positions under social pressure. Small group curriculum on worldview.",
        "timeline": "Launch within 60 days",
    },
    {
        "pillar": "discipleship_depth",
        "trigger": lambda scores, archetype: scores.get("discipleship_depth", 100) <= 45,
        "urgency": "HIGH",
        "title": "Pastoral Call to Multiplication",
        "diagnosis": "Discipleship multiplication is critically low. The church is producing receivers, not reproducers. The Great Commission is being treated as a pastoral specialty rather than a congregational calling.",
        "biblical_anchor": "Matthew 28:19–20; 2 Timothy 2:2 — entrust to faithful people who will teach others.",
        "intervention": "Preach a Great Commission series explicitly naming every member as a disciple-maker. Create a simple, visible on-ramp (cohort of 3–4, 12 weeks, structured). Celebrate discipleship stories from the front.",
        "timeline": "Launch within 60 days",
    },
    {
        "pillar": "spiritual_discipline",
        "trigger": lambda scores, archetype: scores.get("spiritual_discipline", 100) <= 50,
        "urgency": "MEDIUM",
        "title": "Church-Wide Scripture and Prayer Initiative",
        "diagnosis": "Members value Scripture and prayer in principle but practice is inconsistent. The gap between stated value and actual practice is among the highest in the assessment.",
        "biblical_anchor": "Joshua 1:8; Luke 18:1 — men should always pray and not lose heart.",
        "intervention": "Launch a 21-day prayer emphasis paired with a church-wide reading plan. Build accountability into existing small groups. Share simple daily rhythms from the pulpit — not long programs, but sustainable habits.",
        "timeline": "Begin next quarter",
    },
    {
        "pillar": "transformation_fruit",
        "trigger": lambda scores, archetype: scores.get("transformation_fruit", 100) <= 50,
        "urgency": "MEDIUM",
        "title": "Deepen Application Culture in Preaching and Groups",
        "diagnosis": "Life transformation scores are below the doctrinal scores — indicating a gap between receiving truth and living it. Obedience structures are weak.",
        "biblical_anchor": "James 1:22 — be doers of the word, not hearers only. Romans 12:1–2.",
        "intervention": "Restructure small groups to include a specific application question each week. Add 'what are you going to do differently this week?' as a standard close to sermons. Create accountability partnerships within groups.",
        "timeline": "This quarter",
    },
    {
        "pillar": "engagement_alignment",
        "trigger": lambda scores, archetype: scores.get("engagement_alignment", 100) <= 48,
        "urgency": "MEDIUM",
        "title": "Create Visible Pathways for Involvement",
        "diagnosis": "Members want to be more involved but don't know how. The church has systems but not visible on-ramps. Passivity is partly a communication failure.",
        "biblical_anchor": "1 Corinthians 12:7 — to each is given the manifestation of the Spirit for the common good.",
        "intervention": "Design and promote a 3-step involvement pathway: Attend → Connect → Contribute. Make it visible physically and digitally. Preach body-life theology. Celebrate servant stories.",
        "timeline": "This month",
    },
    {
        "pillar": "doctrinal_integrity",
        "trigger": lambda scores, archetype: scores.get("doctrinal_integrity", 100) <= 52,
        "urgency": "MEDIUM",
        "title": "Strengthen Doctrinal Foundation",
        "diagnosis": "Doctrinal clarity is below average. Members may struggle to articulate core beliefs, distinguish truth from error, or hold firm under cultural pressure.",
        "biblical_anchor": "Titus 1:9 — the elder must hold firm to the trustworthy word as taught. 1 Timothy 4:16.",
        "intervention": "Preach through a doctrinal foundation series (gospel, Scripture, sin, salvation, church, mission). Create a new members class that covers core doctrine explicitly. Equip small group leaders to handle doctrinal questions.",
        "timeline": "Plan for next sermon series",
    },
]


def generate_church_recommendations(
    pillar_scores: Dict[str, float],
    archetype: str,
    max_recommendations: int = 5,
) -> List[RecommendationOutput]:
    results = []
    priority = 1

    for rule in CHURCH_RULES:
        if priority > max_recommendations:
            break
        try:
            if rule["trigger"](pillar_scores, archetype):
                results.append(RecommendationOutput(
                    priority=priority,
                    pillar=rule["pillar"],
                    title=rule["title"],
                    urgency=rule["urgency"],
                    diagnosis=rule["diagnosis"],
                    biblical_anchor=rule["biblical_anchor"],
                    intervention=rule["intervention"],
                    timeline=rule["timeline"],
                ))
                priority += 1
        except Exception:
            continue

    return results


def generate_individual_recommendations(
    pillar_scores: Dict[str, float],
    maturity_tier: str,
    credibility_warning: bool,
) -> List[RecommendationOutput]:
    """Generates up to 3 individual-level growth recommendations."""
    results = []
    priority = 1

    INDIVIDUAL_RULES = [
        {
            "pillar": "discipleship_depth",
            "trigger": lambda p: p.get("discipleship_depth", 100) <= 45,
            "urgency": "HIGH",
            "title": "Move from Receiver to Reproducer",
            "diagnosis": "Your doctrinal foundation is present, but it hasn't moved into multiplication. There's no evidence of intentional discipleship in the last year.",
            "biblical_anchor": "2 Timothy 2:2; Matthew 28:19–20 — the call to make disciples is for every believer.",
            "intervention": "Find one person to meet with weekly around Scripture and life for 12 weeks. Start small. Stay consistent. This is the next step.",
            "timeline": "Start within the next 2 weeks",
        },
        {
            "pillar": "spiritual_discipline",
            "trigger": lambda p: p.get("spiritual_discipline", 100) <= 50,
            "urgency": "MEDIUM",
            "title": "Build a Consistent Daily Rhythm with God",
            "diagnosis": "Your responses show a gap between how much you value prayer and Scripture and how consistently you practice them.",
            "biblical_anchor": "John 15:4 — abide in me, and I in you. The fruit comes from the connection.",
            "intervention": "Block 20 minutes each morning before anything else. One paragraph of Scripture. Pray it back. Do this 30 days and note what changes.",
            "timeline": "Begin tomorrow",
        },
        {
            "pillar": "transformation_fruit",
            "trigger": lambda p: p.get("transformation_fruit", 100) <= 50,
            "urgency": "MEDIUM",
            "title": "Name and Pursue Specific Life Change",
            "diagnosis": "Your responses suggest belief is present but the evidence of ongoing transformation is limited. Faith without visible fruit raises important questions worth sitting with.",
            "biblical_anchor": "Galatians 5:22–23; 2 Corinthians 3:18 — we are being transformed from one degree of glory to another.",
            "intervention": "Identify one specific area of sin or immaturity. Name it. Confess it. Find accountability. Pursue change with a plan, not just a wish.",
            "timeline": "This week",
        },
        {
            "pillar": "doctrinal_integrity",
            "trigger": lambda p: p.get("doctrinal_integrity", 100) <= 52,
            "urgency": "MEDIUM",
            "title": "Strengthen Your Doctrinal Foundation",
            "diagnosis": "Some responses suggest uncertainty on core biblical doctrines. A shaky foundation will affect everything built on it.",
            "biblical_anchor": "2 Timothy 2:15 — do your best to present yourself to God as one approved, correctly handling the word of truth.",
            "intervention": "Work through a foundational resource: 'Doctrine' by Mark Driscoll and Gerry Breshears, or Wayne Grudem's 'Christian Beliefs'. Ask your pastor for a reading recommendation suited to where you are.",
            "timeline": "Begin this month",
        },
    ]

    for rule in INDIVIDUAL_RULES:
        if priority > 3:
            break
        if rule["trigger"](pillar_scores):
            results.append(RecommendationOutput(
                priority=priority,
                pillar=rule["pillar"],
                title=rule["title"],
                urgency=rule["urgency"],
                diagnosis=rule["diagnosis"],
                biblical_anchor=rule["biblical_anchor"],
                intervention=rule["intervention"],
                timeline=rule["timeline"],
            ))
            priority += 1

    return results
