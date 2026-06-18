"""
BHIS Doctrinal Framework
------------------------
Grounded in Watermark Community Church's Full Doctrinal Statement
(watermark.org/about/full-doctrinal-statement)

This module defines the theological standard against which the
Doctrinal Integrity pillar is scored. Every doctrine, its biblical
anchor, its BHIS measurement dimension, and its scoring logic are
documented here.

If a church adopts a different theological profile, this module
is the single file to swap. The scoring engine itself is framework-agnostic;
this file is the theological layer that drives Pillar 1.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DoctrinalPosition:
    section: int
    title: str
    summary: str
    scripture_anchors: List[str]
    bhis_dimension: str          # which BHIS pillar or sub-dimension
    measurement_approach: str    # how BHIS tests this
    common_errors: List[str]     # what wrong answers look like
    drift_indicators: List[str]  # signs this doctrine is weakening
    urgency: str                 # 'core' | 'important' | 'secondary'
    scoring_note: str


WATERMARK_DOCTRINAL_FRAMEWORK = [

    DoctrinalPosition(
        section=1,
        title="The Bible — Verbal Inspiration and Inerrancy",
        summary=(
            "The Bible is the verbally inspired Word of God, without error in the original "
            "writings, and the supreme and final authority in doctrine and practice."
        ),
        scripture_anchors=["2 Timothy 3:16-17", "2 Peter 1:21", "John 17:17"],
        bhis_dimension="doctrinal_integrity + spiritual_discipline",
        measurement_approach=(
            "Test stated belief in inerrancy (Likert). Cross-check against actual Scripture "
            "engagement frequency (Q11). The gap between these two is one of the most "
            "diagnostically valuable contradiction flags in the system (CP-01)."
        ),
        common_errors=[
            "Scripture is inspired but may contain errors in historical or scientific matters",
            "The Bible is a human document that contains God's Word but is not identical with it",
            "Scripture is one authority among many — tradition, reason, and experience are co-equal",
            "Biblical authority is functional (it works for faith) but not propositional (factually true)",
        ],
        drift_indicators=[
            "Member rejects clear biblical teaching on social/ethical issues citing 'historical context'",
            "Member treats Scripture as one input among many rather than the final word",
            "Member reads Scripture rarely despite claiming it is authoritative",
            "Member distinguishes between 'inspired ideas' and 'inspired words'",
        ],
        urgency="core",
        scoring_note=(
            "If a respondent scores Q2 (Scripture authority) high but Q11 (reading frequency) low, "
            "CP-01 contradiction flag fires. Scores are reduced by the contradiction penalty. "
            "This gap is the most common false-health signal in evangelical churches."
        ),
    ),

    DoctrinalPosition(
        section=2,
        title="The Trinity",
        summary=(
            "There is one God. The Father, Son, and Spirit are each fully God, and each is a "
            "distinct person — not three gods, and not three modes of one person."
        ),
        scripture_anchors=["Deuteronomy 6:4", "Matthew 28:19-20", "2 Corinthians 13:14",
                            "1 Corinthians 8:6", "Colossians 2:9", "Acts 5:3-4"],
        bhis_dimension="doctrinal_integrity",
        measurement_approach=(
            "Multiple choice question distinguishing Trinitarian orthodoxy from Modalism "
            "(God appears in three modes), Tritheism (three gods), and Arianism "
            "(Jesus is a created being, not fully God)."
        ),
        common_errors=[
            "God shows himself in three different ways (Modalism / Oneness theology)",
            "The Father, Son, and Spirit are three separate gods (Tritheism)",
            "Jesus was the greatest created being but not fully God (Arianism)",
            "The Trinity is a Greek philosophical concept imposed on the Bible",
        ],
        drift_indicators=[
            "Member sees Jesus as primarily a moral teacher rather than second person of the Trinity",
            "Member uses language suggesting the Spirit is a force or energy rather than a person",
            "Member is fuzzy on the distinction between monotheism and Trinitarian theology",
        ],
        urgency="core",
        scoring_note=(
            "Trinitarian doctrine is a boundary marker of Christian orthodoxy. A wrong answer "
            "here indicates either significant theological confusion or a non-orthodox background. "
            "Does not trigger drift signal alone but depresses Pillar 1 score meaningfully."
        ),
    ),

    DoctrinalPosition(
        section=3,
        title="Jesus Christ — Person and Work",
        summary=(
            "Jesus is the eternal Son of God who became fully human without ceasing to be fully God. "
            "He accomplished redemption through substitutionary atonement, burial, and bodily "
            "resurrection. He is the only means of salvation."
        ),
        scripture_anchors=["John 1:1,14,18", "Luke 1:35", "Romans 3:24-26", "4:25",
                            "John 14:6", "Acts 4:12", "Philippians 2:5-8",
                            "1 Timothy 2:5", "Colossians 1:15-19", "Hebrews 1:3"],
        bhis_dimension="doctrinal_integrity",
        measurement_approach=(
            "Multiple dimensions tested: (1) the exclusivity of Christ as the only way to God, "
            "(2) the substitutionary nature of the atonement, (3) the bodily resurrection as "
            "historical fact, (4) the full deity and humanity of Christ simultaneously."
        ),
        common_errors=[
            "Jesus was a great moral teacher but not uniquely God",
            "Jesus showed us the way to God but is not the exclusive way",
            "The resurrection was spiritual/symbolic, not a literal bodily event",
            "Jesus was more human than divine, or more divine than human (not both fully)",
            "Salvation is available through sincere faith regardless of knowledge of Christ",
        ],
        drift_indicators=[
            "Member hesitant to affirm Jesus as the only way when social pressure is applied (Q54 proxy)",
            "Member separates Jesus's teachings from his claims to divinity",
            "Member describes the atonement only in moral influence terms, not substitution",
            "Member is universalist in tendency — God accepts all sincere seekers",
        ],
        urgency="core",
        scoring_note=(
            "Christology and soteriology are the doctrinal core. Q1 (salvation mechanism) and "
            "Q6 (Christ exclusivity) are the primary measurement questions for this section. "
            "Wrong answers on either are scored as significant errors, not minor gaps."
        ),
    ),

    DoctrinalPosition(
        section=4,
        title="The Holy Spirit",
        summary=(
            "The Holy Spirit is a divine person who convicts, indwells all believers from the "
            "moment of faith, baptizes into the body of Christ, seals for salvation, regenerates, "
            "and bestows spiritual gifts. Sign gifts (tongues, miraculous healing) were "
            "authenticating signs for the early church, not normative for all believers."
        ),
        scripture_anchors=["John 16:7-11", "John 3:8", "1 Corinthians 12:4-11,13",
                            "John 14:16-17", "Ephesians 4:30", "5:18",
                            "Acts 8:14", "10:44-48", "Acts 2:6-13"],
        bhis_dimension="doctrinal_integrity + spiritual_discipline",
        measurement_approach=(
            "Test the Spirit's role in regeneration and sanctification. The cessationism position "
            "is noted but NOT used as a primary scoring question in the MVP, as this is "
            "denominationally specific and would unfairly penalize charismatic/pentecostal members. "
            "Flag for theological profile customization in Phase 2."
        ),
        common_errors=[
            "The Holy Spirit is a force or energy, not a divine person",
            "The Spirit only comes to some believers, not all, at conversion",
            "Speaking in tongues is required evidence of Spirit baptism for all believers",
            "The Spirit's primary role is emotional experience rather than conviction, regeneration, and sanctification",
        ],
        drift_indicators=[
            "Member treats the Spirit as optional or passive in daily life",
            "Member has no concept of the Spirit's role in their sanctification",
            "Member's spiritual life is entirely self-directed with no sense of divine enablement",
        ],
        urgency="important",
        scoring_note=(
            "The MVP does not test cessationism vs. continuationism, as this would introduce "
            "theological tribalism. The theological_profile field on the Church model allows "
            "future customization. Core Spirit doctrine (person, indwelling, regeneration) is tested."
        ),
    ),

    DoctrinalPosition(
        section=5,
        title="Angels — Fallen and Unfallen",
        summary=(
            "Angels are created spiritual beings in different orders. Satan is a fallen angel, "
            "the originator of sin, currently ruling as 'the god of this world,' judged at the "
            "cross, and destined for the Lake of Fire."
        ),
        scripture_anchors=["Hebrews 1:13-14", "2 Peter 2:4", "Revelation 7:12",
                            "Isaiah 14:12-14", "Genesis 3:1-19", "Revelation 20:10"],
        bhis_dimension="doctrinal_integrity",
        measurement_approach=(
            "Not directly tested in the MVP 60-question bank as a standalone question. "
            "Satan's reality surfaces indirectly in Q28 (spiritual resistance), Q26 (active "
            "battle against sin), and drift signal questions. Phase 2 may add explicit testing."
        ),
        common_errors=[
            "Satan is a symbol for human evil, not a real personal being",
            "Angels and demons are mythology, not literal spiritual realities",
        ],
        drift_indicators=[
            "Member treats spiritual warfare as metaphor only",
            "Member has no category for personal evil or demonic influence",
        ],
        urgency="secondary",
        scoring_note="Indirect measurement only in MVP. Low scoring priority.",
    ),

    DoctrinalPosition(
        section=6,
        title="Man — Creation, Fall, Gender, Marriage, and Need for Salvation",
        summary=(
            "Man was created innocent in God's image but sinned, bringing death to all. Man can "
            "do nothing to merit God's favor and needs salvation. God created mankind male and "
            "female, sexually and biologically distinct but equally valued. Marriage is a lifelong "
            "union between one man and one woman."
        ),
        scripture_anchors=["Genesis 1:27", "2:17", "3:19", "Romans 6:23", "Romans 1:20-24",
                            "Ephesians 2:1-3", "Psalm 139:13-16", "Genesis 1:26-28",
                            "Genesis 2:18", "Matthew 19:4-9", "Ephesians 5:31-33",
                            "Romans 5:8"],
        bhis_dimension="doctrinal_integrity + drift_vulnerability",
        measurement_approach=(
            "Two separate dimensions: (1) anthropology — total depravity, man's inability to "
            "earn salvation, the universality of sin. (2) Ethics — biblical view of gender and "
            "marriage. The anthropology questions are scored as core doctrine. The ethics "
            "questions feed into the drift engine, specifically Q54 (cultural accommodation "
            "under pressure), which directly targets this doctrinal area without naming specifics."
        ),
        common_errors=[
            "People are basically good and capable of earning God's favor through moral effort",
            "Sin is primarily social or environmental, not a personal condition before God",
            "Gender and sexuality are socially constructed rather than creational givens",
            "Marriage can be redefined by culture without violating God's design",
        ],
        drift_indicators=[
            "Q54: member folds under social pressure on ethics",
            "Q53: member holds to relativistic view of moral truth",
            "Q55: member says culture shapes their views more than Scripture",
            "Open-ended Q60: ethics/sexuality gap themes emerge",
        ],
        urgency="core",
        scoring_note=(
            "Anthropology (sin, need for salvation) is tested explicitly in Q4. Ethics (gender, "
            "marriage) is tested implicitly via Q54 scenario. Direct ethics questions are not "
            "included as named MC questions to avoid virtue signaling — the scenario approach "
            "is more reliable. High drift signals in this area should be flagged pastorally."
        ),
    ),

    DoctrinalPosition(
        section=7,
        title="Salvation — Grace Alone, Faith Alone, Christ Alone",
        summary=(
            "Salvation is a sovereign gift of God received through personal faith in Jesus Christ "
            "and his sacrifice for sin. Man is justified by grace through faith apart from works. "
            "Christ is the only means of salvation. All true believers are kept secure in Christ forever."
        ),
        scripture_anchors=["Acts 13:38-39", "Romans 6:23", "Ephesians 1:4-5", "2:8-10",
                            "John 14:6", "Acts 4:12", "Romans 10:9-10",
                            "Romans 8:1,29-30,38-39", "John 10:27-30"],
        bhis_dimension="doctrinal_integrity",
        measurement_approach=(
            "This is the most heavily weighted doctrinal area. Q1 (how is man made right with God) "
            "and Q6 (is Christ the only way) are the primary tests. Q3 (scenario: friend trusts in "
            "personal goodness) is the behavioral test of whether this doctrine is actually held "
            "convictionally, not just academically."
        ),
        common_errors=[
            "Salvation is by living a moral life and doing good (moralism)",
            "Sincere belief in God — regardless of Christ specifically — is sufficient",
            "Good works cooperate with grace to earn or maintain salvation",
            "All people will ultimately be saved because God is love (universalism)",
            "Salvation can be lost through sin or failure to persevere",
        ],
        drift_indicators=[
            "Member affirms salvation by grace but adds implicit moral conditions",
            "Member is universalist in practice — uncomfortable saying non-Christians are lost",
            "Member sees salvation as requiring ongoing performance to maintain",
        ],
        urgency="core",
        scoring_note=(
            "This is the gospel. Wrong answers here are the most significant score penalties in "
            "Pillar 1. A church with consistently low scores on salvation doctrine has a "
            "foundational crisis, not a discipleship gap. Pastoral response is different from "
            "the standard recommendation engine outputs."
        ),
    ),

    DoctrinalPosition(
        section=8,
        title="Sanctification — Positional, Progressive, Ultimate",
        summary=(
            "Sanctification is positional (complete in Christ, the believer is already set apart), "
            "progressive (the Christian grows in grace by the Spirit's power, retaining the sinful "
            "nature), and ultimate (full freedom from sin at glorification)."
        ),
        scripture_anchors=["John 17:17", "2 Corinthians 3:18", "Ephesians 5:25-27",
                            "1 Thessalonians 5:23", "Hebrews 10:10,14"],
        bhis_dimension="transformation_fruit + doctrinal_integrity",
        measurement_approach=(
            "Tested primarily through Pillar 3 behavioral questions. The doctrinal understanding "
            "of sanctification surfaces in Q24 (Romans 12:1-2 application) and Q26 (active battle "
            "against sin). The distinction between positional and progressive sanctification is "
            "not directly tested in MVP but informs the Transformation pillar design."
        ),
        common_errors=[
            "Sanctification is optional — Christians can stay spiritually immature indefinitely",
            "Sanctification is primarily about church attendance and religious activity",
            "True believers should achieve sinless perfection in this life",
            "The sinful nature is fully eradicated at conversion",
        ],
        drift_indicators=[
            "Low Transformation scores despite high Doctrinal Integrity — suggests positional "
            "understanding without progressive pursuit",
            "Member has no sense of ongoing battle with sin",
            "Member has given up on significant areas of sin without pastoral engagement",
        ],
        urgency="important",
        scoring_note=(
            "The gap between Doctrinal Integrity and Transformation & Fruit scores is the "
            "primary diagnostic for sanctification health. The 'Orthodoxy Without Obedience' "
            "archetype is largely driven by high doctrine + low transformation — the classic "
            "sanctification disconnect."
        ),
    ),

    DoctrinalPosition(
        section=9,
        title="The Church — Body, Bride, Local Assembly",
        summary=(
            "The Church is all born-again persons of this age. The local church is an assembly "
            "of believers joined together for worship, Word, ordinances, fellowship, equipping, "
            "and the Great Commission."
        ),
        scripture_anchors=["Ephesians 1:22-23", "1 Corinthians 12:13", "Acts 2:42-47",
                            "1 Corinthians 1:1-2", "Ephesians 4:11-13",
                            "Matthew 16:18", "28:19-20"],
        bhis_dimension="church_health_trust + engagement_alignment + discipleship_depth",
        measurement_approach=(
            "Ecclesiology is tested primarily through Pillars 5 and 6. Q52 (what would happen "
            "if the church closed) tests the member's sense of the church's missional identity. "
            "Q37 (role at church) tests consumer vs. body-member posture. "
            "Q47/Q48 (small group + serving) test whether the Acts 2:42-47 pattern is lived out."
        ),
        common_errors=[
            "The church is a building or institution, not a community of people",
            "Church attendance is optional for mature Christians",
            "The local church exists primarily for the member's personal benefit",
            "The Great Commission is for pastors and missionaries, not ordinary members",
        ],
        drift_indicators=[
            "Member attends primarily out of habit or preference, not conviction (Q57)",
            "Member sees no personal responsibility for the church's mission (Q36, Q51)",
            "Member is disconnected from any community structure within the church (Q47)",
        ],
        urgency="important",
        scoring_note=(
            "Low Church Health + low Engagement + low Discipleship = 'Gathering Without Discipling' "
            "archetype. The ecclesiological drift toward consumerism is one of the most common "
            "patterns in American evangelical churches and a primary BHIS detection target."
        ),
    ),

    DoctrinalPosition(
        section=10,
        title="The Ordinances — Baptism and Lord's Supper",
        summary=(
            "Christ instituted water baptism (believer's baptism, publicly identifying with "
            "Christ's death and resurrection) and the Lord's Supper (memorial of Christ's death, "
            "expression of faith in his return). Both are observed until he comes."
        ),
        scripture_anchors=["Matthew 28:19-20", "1 Corinthians 11:23-26"],
        bhis_dimension="engagement_alignment + doctrinal_integrity",
        measurement_approach=(
            "Not directly tested in the MVP 60-question bank as a standalone MC question. "
            "Baptism participation and Lord's Supper engagement are captured in the optional "
            "behavioral data layer. Phase 2 may add explicit ordinance questions."
        ),
        common_errors=[
            "Baptism saves or contributes to salvation",
            "Infant baptism is equivalent to believer's baptism",
            "The Lord's Supper is the literal body and blood of Christ (transubstantiation)",
            "The ordinances are optional for believers who find them unhelpful",
        ],
        drift_indicators=[
            "Member has never been baptized as a believer",
            "Member does not participate in the Lord's Supper",
        ],
        urgency="secondary",
        scoring_note="Indirect measurement only in MVP.",
    ),

    DoctrinalPosition(
        section=11,
        title="End Times and Eternal State",
        summary=(
            "Jesus Christ will return personally, visibly, and gloriously. The dead will be raised. "
            "Christ will judge all people. The unrighteous face everlasting punishment in Hell. "
            "The righteous will enjoy unbroken fellowship with God. After death, believers are "
            "immediately with Christ; unbelievers are in conscious misery in Hades until final judgment."
        ),
        scripture_anchors=["1 Thessalonians 4:16-17", "2 Peter 3:9-10", "2 Thessalonians 1:5-10",
                            "Matthew 25:31-34,41,46", "John 5:28-29", "Revelation 20:11-15",
                            "1 Corinthians 15:50-57", "Revelation 21:1-5",
                            "Luke 23:43", "Philippians 1:21-23"],
        bhis_dimension="doctrinal_integrity",
        measurement_approach=(
            "The reality of final judgment and eternal consequences is tested as a drift indicator. "
            "Universalism (all are saved) and annihilationism (the wicked simply cease to exist) "
            "are the most common errors among evangelicals. This surfaces in Q7 (God accepts "
            "everyone because he is love) as an incorrect option."
        ),
        common_errors=[
            "All people will ultimately be reconciled to God (universalism)",
            "Hell is not eternal conscious punishment but cessation of existence (annihilationism)",
            "The second coming is metaphorical or already accomplished",
            "After death, everyone gets another chance to accept Christ",
            "Heaven and Hell are states of mind, not real places",
        ],
        drift_indicators=[
            "Member has difficulty affirming that unbelievers face eternal judgment",
            "Member is functionally universalist — uncomfortable with the exclusivity of the gospel",
            "Q7 option d (God accepts everyone) selected — the most common eschatological error",
        ],
        urgency="important",
        scoring_note=(
            "Q7 option d tests universalist drift implicitly. A high percentage of church members "
            "selecting this option is a significant doctrinal warning at the church level. "
            "Universalism is often the endpoint of gospel drift, not the beginning — so it "
            "functions as an advanced drift indicator."
        ),
    ),
]


# ── Doctrinal scoring weights within Pillar 1 ─────────────────────────────────
# These weights determine how much each doctrine impacts the Pillar 1 score.
# 'core' doctrines carry more weight than 'important' or 'secondary'.

DOCTRINAL_QUESTION_WEIGHTS = {
    "salvation":       2.0,   # Sections 3 + 7 — most critical
    "scripture":       1.75,  # Section 1 — foundation of everything else
    "christ":          1.75,  # Section 3 — the person of Christ
    "trinity":         1.5,   # Section 2 — boundary of orthodoxy
    "sin_anthropology":1.25,  # Section 6 — need for salvation
    "holy_spirit":     1.0,   # Section 4 — person and work
    "sanctification":  1.0,   # Section 8 — Christian growth
    "church":          0.75,  # Section 9 — ecclesiology
    "eschatology":     0.75,  # Section 11 — end times
    "ordinances":      0.5,   # Section 10 — secondary
    "angels":          0.25,  # Section 5 — tertiary
}


# Map each Pillar 1 question (Q1–Q10) to the doctrine it primarily tests, taken
# from the seed bank (seeds/pillar_1_questions.py). Q10 is a forced-prioritization
# question spanning several core areas, so it keeps the default (equal) weight.
DOCTRINAL_QUESTION_DOCTRINE = {
    1: "salvation",          # how a person is made right with God (S7)
    2: "scripture",          # Scripture authority (S1)
    3: "christ",             # exclusivity of Christ (S3)
    4: "sin_anthropology",   # nature of sin (S6)
    5: "salvation",          # gospel confidence (S7)
    6: "trinity",            # the Trinity (S2)
    7: "sanctification",     # sanctification (S8)
    8: "holy_spirit",        # the Holy Spirit's role (S4)
    9: "eschatology",        # end times / eternal state (S11)
    # 10: forced prioritization across core doctrines → default weight 1.0
}


def doctrinal_question_weight(question_number: int) -> float:
    """Weight for a Pillar 1 question within the doctrinal_integrity pillar,
    derived from the Watermark doctrine it tests. Defaults to 1.0."""
    doctrine = DOCTRINAL_QUESTION_DOCTRINE.get(question_number)
    if doctrine is None:
        return 1.0
    return DOCTRINAL_QUESTION_WEIGHTS.get(doctrine, 1.0)


def get_doctrine_by_section(section: int) -> DoctrinalPosition | None:
    return next((d for d in WATERMARK_DOCTRINAL_FRAMEWORK if d.section == section), None)


def get_core_doctrines() -> list[DoctrinalPosition]:
    return [d for d in WATERMARK_DOCTRINAL_FRAMEWORK if d.urgency == "core"]


def get_drift_indicators_by_pillar(pillar: str) -> list[str]:
    indicators = []
    for d in WATERMARK_DOCTRINAL_FRAMEWORK:
        if pillar in d.bhis_dimension:
            indicators.extend(d.drift_indicators)
    return indicators
