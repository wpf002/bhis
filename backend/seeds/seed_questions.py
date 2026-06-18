"""
BHIS Question Bank Seed Script
Seeds the database with the full 60-question assessment.
Run: python seeds/seed_questions.py
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.config import settings
from app.models.models import SurveyTemplate, Question, QuestionOption

engine = create_async_engine(settings.DATABASE_URL)
Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ── Pillar constants ───────────────────────────────────────────────────────────
DOC  = "doctrinal_integrity"
DIS  = "spiritual_discipline"
TRF  = "transformation_fruit"
DEP  = "discipleship_depth"
CHT  = "church_health_trust"
ENG  = "engagement_alignment"
DRI  = "drift_vulnerability"

L  = "likert"
MC = "mc"
BF = "behavioral_frequency"
SC = "scenario"
FP = "forced_prioritization"
OE = "open_ended"

# Format: (q_num, pillar, q_type, text, is_cc, cc_pair_num, church_sig, indiv_sig, qualitative_only, options)
# options: list of (letter, text, score, is_correct, is_drift_signal)

from seeds.pillar_1_questions import PILLAR_1_QUESTIONS

# Full 60-question bank
# Q1-Q10: Rebuilt from Watermark Community Church Doctrinal Statement
# Q11-Q60: Pillars 2-7 (unchanged)
QUESTIONS = PILLAR_1_QUESTIONS + [

        # ── PILLAR 2: Spiritual Discipline ────────────────────────────────────────
    (11, DIS, BF, "How often do you read or study the Bible on your own, outside of church services?", True, 2, True, True, False, [
        ("a", "Daily or almost daily", 100, False, False),
        ("b", "A few times a week", 75, False, False),
        ("c", "Once a week", 50, False, False),
        ("d", "A few times a month", 25, False, False),
        ("e", "Rarely or never", 0, False, False),
    ]),
    (12, DIS, BF, "How often do you spend intentional time in personal prayer — not quick requests, but extended, focused prayer?", True, 13, True, True, False, [
        ("a", "Daily or almost daily", 100, False, False),
        ("b", "Several times a week", 75, False, False),
        ("c", "Once a week", 50, False, False),
        ("d", "Occasionally", 25, False, False),
        ("e", "Rarely", 0, False, False),
    ]),
    (13, DIS, L, "My personal prayer life genuinely reflects dependence on God, not just religious habit.", True, 12, False, True, False, []),
    (14, DIS, SC, "When you read Scripture, which best describes your typical approach?", False, None, False, True, False, [
        ("a", "I read to fulfill a reading plan or obligation", 40, False, False),
        ("b", "I read to understand what God is saying and how to apply it to my life", 100, True, False),
        ("c", "I scan for verses that comfort or encourage me in the moment", 60, False, False),
        ("d", "I read for general spiritual knowledge and understanding", 60, False, False),
    ]),
    (15, DIS, L, "I regularly examine my heart and confess specific sins to God — not just general guilt.", False, None, False, True, False, []),
    (16, DIS, BF, "In the last 30 days, approximately how many days did you spend 10 or more minutes in intentional personal prayer?", True, 13, False, True, False, [
        ("a", "20 or more days", 100, False, False),
        ("b", "10–19 days", 75, False, False),
        ("c", "5–9 days", 50, False, False),
        ("d", "1–4 days", 25, False, False),
        ("e", "Zero days", 0, False, False),
    ]),
    (17, DIS, L, "I am currently growing in my understanding of the Bible.", False, None, False, True, False, []),
    (18, DIS, OE, "Describe one specific way your relationship with God has deepened or changed in the past 6 months.", False, None, False, True, True, []),

    # ── PILLAR 3: Transformation & Fruit ──────────────────────────────────────
    (19, TRF, L, "Compared to 2 years ago, I can point to genuine change in how I think, speak, and treat others.", False, None, False, True, False, []),
    (20, TRF, SC, "When you realize you have sinned or fallen short, how do you typically respond?", False, None, False, True, False, [
        ("a", "I feel guilty but usually don't do much with it", 40, False, False),
        ("b", "I confess to God and try to move on, but I often repeat the same patterns", 60, False, False),
        ("c", "I genuinely confess, seek to make it right, and work toward change with God's help", 100, True, False),
        ("d", "I tend to rationalize or minimize it over time", 20, False, False),
    ]),
    (21, TRF, L, "In daily life, I increasingly show patience, kindness, and self-control — including when it's inconvenient.", False, None, False, True, False, []),
    (22, TRF, SC, "A coworker takes credit for your work in front of your supervisor. How do you most honestly respond?", False, None, False, True, False, [
        ("a", "I confront it aggressively — that kind of dishonesty needs to be addressed", 40, False, False),
        ("b", "I feel hurt and say nothing, but carry resentment privately", 20, False, False),
        ("c", "I address it calmly and try to genuinely forgive the person", 100, True, False),
        ("d", "I struggle honestly with this and recognize I need to respond better", 80, False, False),
    ]),
    (23, TRF, L, "My life outside of church looks consistent with the values I express inside church.", True, 22, True, True, False, []),
    (24, TRF, SC, "Romans 12:1–2 calls believers to offer their lives as living sacrifices and not conform to the pattern of the world. How well does this describe your actual life right now?", False, None, False, True, False, [
        ("a", "I would say this describes my life well", 80, False, False),
        ("b", "I'm working toward this but struggle with cultural conformity", 80, False, False),
        ("c", "I believe it's true but haven't thought deeply about applying it", 40, False, False),
        ("d", "I find this standard difficult to hold realistically", 20, False, False),
    ]),
    (25, TRF, SC, "How would the people who know you best describe the way you treat them?", False, None, False, True, False, [
        ("a", "Mostly kind, but I can be difficult when I'm stressed or tired", 60, False, False),
        ("b", "Consistently patient, forgiving, and present — even when it's hard", 100, True, False),
        ("c", "I'm genuinely working on this — I have real growth areas in relationships", 80, False, False),
        ("d", "Honestly, I don't think I'd get a very strong review", 40, False, False),
    ]),
    (26, TRF, L, "I am actively fighting specific sins or patterns in my life — not just acknowledging they exist.", False, None, False, True, False, []),
    (27, TRF, SC, "When someone hurts you seriously, what most honestly describes your approach to forgiveness?", False, None, False, True, False, [
        ("a", "Forgiveness is a genuine area of strength for me — I release offenses with time", 100, True, False),
        ("b", "I try, but it's slow and I struggle — forgiveness doesn't come easily", 60, False, False),
        ("c", "I find forgiveness genuinely hard and tend to hold things for a long time", 40, False, False),
        ("d", "I don't think about forgiveness as something I need to actively pursue", 20, False, False),
    ]),
    (28, TRF, OE, "Is there currently an area of your life where you sense God is asking for change, but you have been slow to respond? (Yes / No / I'm not sure)", False, None, False, True, True, []),

    # ── PILLAR 4: Discipleship Depth ──────────────────────────────────────────
    (29, DEP, L, "I am currently being intentionally discipled or spiritually mentored by someone.", True, 30, True, False, False, []),
    (30, DEP, BF, "In the last year, have you intentionally helped another person grow in their faith through teaching, mentoring, or consistent spiritual encouragement?", True, 29, True, True, False, [
        ("a", "Yes — I am actively discipling or mentoring someone now", 100, False, False),
        ("b", "I have had meaningful spiritual conversations but nothing intentional or ongoing", 60, False, False),
        ("c", "I want to but haven't started yet", 40, False, False),
        ("d", "I don't feel equipped to disciple others", 40, False, False),
    ]),
    (31, DEP, L, "I understand the gospel well enough to clearly walk someone through it.", True, 33, False, True, False, []),
    (32, DEP, BF, "How often do you have intentional spiritual conversations with people who are not Christians or not yet committed to Christ?", False, None, True, True, False, [
        ("a", "Regularly — at least a few times a month", 100, False, False),
        ("b", "Occasionally — a few times a year", 60, False, False),
        ("c", "Rarely — I don't often bring my faith into conversations", 40, False, False),
        ("d", "Never — I can't think of a time this has happened", 20, False, False),
    ]),
    (33, DEP, SC, "Someone in your life asks: 'What does it actually mean to be a Christian?' What most accurately describes how you respond?", True, 5, False, True, False, [
        ("a", "I give a clear, confident explanation of the gospel", 100, True, False),
        ("b", "I share what faith means to me personally but probably miss key elements", 60, False, False),
        ("c", "I refer them to a pastor or someone more equipped", 40, False, False),
        ("d", "I would feel genuinely unsure how to answer well", 20, False, False),
    ]),
    (34, DEP, L, "I understand the difference between making converts and making disciples — and I see discipleship as my personal responsibility.", False, None, False, True, False, []),
    (35, DEP, MC, "2 Timothy 2:2 says: 'And the things you have heard me say... entrust to reliable people who will also be qualified to teach others.' What does this passage most clearly call believers to do?", False, None, False, True, False, [
        ("a", "Attend strong biblical teaching consistently", 40, False, False),
        ("b", "Pass what they've received to others who will continue the chain", 100, True, False),
        ("c", "Find a reliable pastor and follow their teaching closely", 40, False, False),
        ("d", "Document important teachings to preserve them for the future", 20, False, False),
    ]),
    (36, DEP, L, "I see myself as responsible for the spiritual growth of people in my life, not only my own.", False, None, False, True, False, []),
    (37, DEP, SC, "When you think honestly about your role at your church, which best describes you?", False, None, True, True, False, [
        ("a", "I primarily receive — I attend, listen, and take in what's offered", 40, False, False),
        ("b", "I contribute in some ways, mostly through serving functions", 60, False, False),
        ("c", "I am actively involved in others' growth and the church's mission", 80, False, False),
        ("d", "I lead or train others in discipleship — it's a core part of my involvement", 100, True, False),
    ]),

    # ── PILLAR 5: Church Health & Trust ───────────────────────────────────────
    (38, CHT, L, "I trust the pastoral leadership of my church.", True, 40, True, True, False, []),
    (39, CHT, L, "The preaching at my church is biblically grounded and helps me understand and apply Scripture.", False, None, True, True, False, []),
    (40, CHT, SC, "If you were going through a serious spiritual struggle or dealing with a significant sin issue, would you feel safe bringing it to a pastor or leader at your church?", True, 38, False, True, False, [
        ("a", "Yes — I fully trust the leadership and would feel safe being honest", 100, True, False),
        ("b", "I might, but I'd be selective about what I actually shared", 60, False, False),
        ("c", "No — I wouldn't feel safe being fully honest with leadership", 20, False, False),
        ("d", "I haven't really thought about whether I would or not", 40, False, False),
    ]),
    (41, CHT, L, "My church creates space for healthy accountability — people are both encouraged and challenged.", False, None, True, True, False, []),
    (42, CHT, SC, "A decision was recently made in your church that you personally disagreed with. How did you most likely respond?", False, None, True, True, False, [
        ("a", "I expressed my concerns through appropriate channels and respected the final decision", 100, True, False),
        ("b", "I discussed my frustration with others at the church informally", 40, False, False),
        ("c", "I became less engaged or pulled back somewhat as a result", 20, False, False),
        ("d", "I prayed about it and chose to extend trust to the leadership", 100, True, False),
        ("e", "This hasn't happened to me recently", 60, False, False),
    ]),
    (43, CHT, L, "I feel genuinely cared for by my church community — not just on Sundays.", False, None, True, True, False, []),
    (44, CHT, L, "My church is heading in the right spiritual direction.", False, None, True, True, False, []),
    (45, CHT, OE, "What is one thing your church does genuinely well? What is one area where you wish it would grow?", False, None, True, False, True, []),

    # ── PILLAR 6: Engagement & Alignment ─────────────────────────────────────
    (46, ENG, BF, "How consistently do you attend your church's primary Sunday gathering?", True, 49, True, True, False, [
        ("a", "Almost every week — 45 or more times per year", 100, False, False),
        ("b", "Most weeks — 30 to 44 times per year", 75, False, False),
        ("c", "Somewhat regularly — 15 to 29 times per year", 50, False, False),
        ("d", "Occasionally — fewer than 15 times per year", 25, False, False),
        ("e", "Rarely or not currently", 0, False, False),
    ]),
    (47, ENG, BF, "Are you currently part of a small group, Bible study, or intentional community within your church?", False, None, True, True, False, [
        ("a", "Yes, and I attend consistently", 100, False, False),
        ("b", "Yes, but I attend inconsistently", 60, False, False),
        ("c", "No, but I would like to be", 40, False, False),
        ("d", "No, and I'm not particularly drawn to it", 20, False, False),
    ]),
    (48, ENG, BF, "Are you currently serving in any capacity at your church?", False, None, True, True, False, [
        ("a", "Yes — in a regular, committed role", 100, False, False),
        ("b", "Occasionally, when needed", 60, False, False),
        ("c", "I used to serve but stepped back", 40, False, False),
        ("d", "No", 20, False, False),
    ]),
    (49, ENG, L, "My involvement at church goes beyond just attending services.", True, 47, False, True, False, []),
    (50, ENG, SC, "How would you describe your approach to financial giving to your church?", False, None, False, True, False, [
        ("a", "I give regularly and intentionally as an act of worship and trust in God", 100, True, False),
        ("b", "I give occasionally when I remember or when there's a specific need", 60, False, False),
        ("c", "I rarely or never give financially", 20, False, False),
        ("d", "I'm working on making this a consistent part of my life", 80, False, False),
    ]),
    (51, ENG, L, "I am personally involved in my church's mission, not just present for its programs.", False, None, False, True, False, []),
    (52, ENG, SC, "If your church closed tomorrow, which statement most honestly describes how you think your surrounding community would be affected?", False, None, True, True, False, [
        ("a", "Many people in my personal network would notice and be genuinely impacted", 100, True, False),
        ("b", "It would affect the people directly involved but not many outside", 60, False, False),
        ("c", "Honestly, I'm not sure it would make much of a difference beyond the members", 40, False, False),
        ("d", "I haven't thought about this before", 20, False, False),
    ]),

    # ── PILLAR 7: Drift & Vulnerability ───────────────────────────────────────
    (53, DRI, MC, "Which statement most honestly reflects your view of moral truth?", False, None, True, True, False, [
        ("a", "Right and wrong are defined by what benefits society at a given time", 20, False, True),
        ("b", "Each person must define moral truth based on their own experience", 20, False, True),
        ("c", "The Bible provides a fixed standard of right and wrong that applies to everyone", 100, True, False),
        ("d", "Religious communities define morality for their members, but standards vary by tradition", 40, False, True),
    ]),
    (54, DRI, SC, "Your church teaches something on sexuality, family, or ethics that directly conflicts with what your colleagues or friends believe. What most accurately describes your response?", True, 55, True, True, False, [
        ("a", "I hold to the biblical teaching — even when it's uncomfortable to explain", 100, True, False),
        ("b", "I privately agree with the church but avoid the topic in social settings", 60, False, True),
        ("c", "I find myself questioning whether the church's position is actually right", 40, False, True),
        ("d", "I think the church should consider updating its position to be more accessible", 20, False, True),
    ]),
    (55, DRI, L, "My beliefs and values are primarily shaped by Scripture rather than by culture, media, or popular opinion.", True, 54, True, True, False, []),
    (56, DRI, SC, "Media — news, social media, streaming content — is shaping how you think about life, relationships, and morality.", False, None, False, True, False, [
        ("a", "I'm aware of this tension and actively manage what I consume", 80, False, False),
        ("b", "Probably more than I should, but I haven't examined it carefully", 40, False, True),
        ("c", "I don't think this is a significant issue for me", 40, False, False),
        ("d", "I know I need to address this more seriously", 60, False, False),
    ]),
    (57, DRI, MC, "What is the primary reason you attend your church?", False, None, True, True, False, [
        ("a", "Habit or family tradition", 40, False, True),
        ("b", "I genuinely believe this community is where I should grow and serve", 100, True, False),
        ("c", "I like the people and the overall environment", 60, False, False),
        ("d", "The teaching and preaching is helpful for my life", 80, False, False),
    ]),
    (58, DRI, L, "I take seriously the possibility that parts of my life may not fully reflect genuine faith — and I sit with that honestly rather than dismissing it.", False, None, False, True, False, []),
    (59, DRI, SC, "You have been attending church for some time. Being honest: has your faith produced real, observable change in your life?", False, None, True, True, False, [
        ("a", "Yes — the change is real and I can point to specific evidence", 100, True, False),
        ("b", "I believe so, but it's genuinely hard to measure", 60, False, False),
        ("c", "Probably less change than I'd like to admit", 40, False, True),
        ("d", "I'm genuinely not sure", 20, False, True),
    ]),
    (60, DRI, OE, "Complete this sentence as honestly as you can: 'When it comes to my faith, the biggest gap between what I believe and how I actually live is...'", False, None, True, True, True, []),
]


async def seed():
    async with Session() as db:
        # Create template
        template = SurveyTemplate(
            name="BHIS Full Diagnostic Assessment",
            version="1.0",
            description="The complete 60-question Biblical Health Intelligence assessment covering all 7 pillars of spiritual maturity and church health.",
            question_count=60,
            estimated_minutes=12,
            is_active=True,
        )
        db.add(template)
        await db.flush()

        for (q_num, pillar, q_type, text, is_cc, cc_pair, church_sig, indiv_sig, qual_only, options) in QUESTIONS:
            question = Question(
                template_id=template.id,
                question_number=q_num,
                pillar=pillar,
                question_text=text,
                question_type=q_type,
                is_contradiction_check=is_cc,
                contradiction_pair_number=cc_pair,
                church_level_significance=church_sig,
                individual_level_significance=indiv_sig,
                qualitative_only=qual_only,
            )
            db.add(question)
            await db.flush()

            for (letter, opt_text, score, is_correct, is_drift) in options:
                db.add(QuestionOption(
                    question_id=question.id,
                    option_letter=letter,
                    option_text=opt_text,
                    score_value=score,
                    is_correct_answer=is_correct,
                    drift_signal=is_drift,
                ))

        await db.commit()
        print(f"✓ Seeded template '{template.name}' with {len(QUESTIONS)} questions")


if __name__ == "__main__":
    asyncio.run(seed())
