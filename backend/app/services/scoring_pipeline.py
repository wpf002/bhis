"""
Scoring pipeline — DB-facing orchestration around the pure scoring engine.

Idempotent: re-scoring a session or re-aggregating a church replaces the prior
result rather than duplicating it. Used by both the scoring router (manual
trigger) and the auto-trigger background task fired on survey completion.
"""
from statistics import mean
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    RespondentSession, Response, Question,
    IndividualScore, PillarScore, ContradictionFlag,
    SurveyInstance, ChurchAggregateScore,
)
from app.services.scoring_engine import (
    QuestionScore, score_individual, normalize_likert, normalize_option_score,
)
from app.services.doctrinal_framework import doctrinal_question_weight
from app.services.archetype_engine import classify_archetype

SCORE_VERSION = "1.0"

_AGG_PILLARS = [
    "doctrinal_integrity", "spiritual_discipline", "transformation_fruit",
    "discipleship_depth", "church_health_trust", "engagement_alignment",
]


async def build_question_scores(session_id: str, db: AsyncSession):
    """Build the QuestionScore list for the engine, applying Watermark doctrine
    weights to the Pillar 1 (doctrinal_integrity) questions."""
    result = await db.execute(
        select(Response)
        .where(Response.session_id == session_id)
        .options(selectinload(Response.question), selectinload(Response.selected_option))
    )
    responses = result.scalars().all()

    question_scores = []
    for r in responses:
        q: Question = r.question
        if q.qualitative_only:
            continue

        normalized = 0.0
        if q.question_type == "likert" and r.likert_value:
            normalized = normalize_likert(r.likert_value)
        elif r.selected_option:
            normalized = normalize_option_score(r.selected_option.score_value)

        weight = 1.0
        if q.pillar == "doctrinal_integrity":
            weight = doctrinal_question_weight(q.question_number)

        question_scores.append(QuestionScore(
            question_number=q.question_number,
            pillar=q.pillar,
            normalized_score=normalized,
            question_type=q.question_type,
            qualitative_only=q.qualitative_only,
            weight=weight,
        ))
    return question_scores


async def score_session(session_id: str, db: AsyncSession) -> Optional[IndividualScore]:
    """Score one completed session. Idempotent: replaces any prior score."""
    session = (await db.execute(
        select(RespondentSession).where(RespondentSession.id == session_id)
    )).scalar_one_or_none()
    if not session or not session.is_complete:
        return None

    # Drop any prior score (+children) so re-scoring produces a single result.
    existing = (await db.execute(
        select(IndividualScore).where(IndividualScore.session_id == session_id)
    )).scalar_one_or_none()
    if existing is not None:
        await db.execute(delete(PillarScore).where(PillarScore.individual_score_id == existing.id))
        await db.execute(delete(ContradictionFlag).where(ContradictionFlag.individual_score_id == existing.id))
        await db.delete(existing)
        await db.flush()

    question_scores = await build_question_scores(session_id, db)
    result = score_individual(question_scores)

    individual_score = IndividualScore(
        session_id=session_id,
        composite_score=result.composite_score,
        maturity_tier=result.maturity_tier,
        contradiction_count=result.contradiction_count,
        credibility_warning=result.credibility_warning,
        drift_risk_level=result.drift_risk_level,
        drift_signal_count=result.drift_signal_count,
        score_version=SCORE_VERSION,
    )
    db.add(individual_score)
    await db.flush()

    for pillar, pr in result.pillar_results.items():
        db.add(PillarScore(
            individual_score_id=individual_score.id,
            pillar=pillar, raw_score=pr.raw_score, normalized_score=pr.normalized_score,
            question_count=pr.question_count, status=pr.status,
        ))
    # Persist ALL contradiction pairs (flagged or not) for auditability.
    for cr in result.contradiction_results:
        db.add(ContradictionFlag(
            individual_score_id=individual_score.id,
            pair_id=cr.pair_id, question_a_number=cr.question_a, question_b_number=cr.question_b,
            score_a=cr.score_a, score_b=cr.score_b, delta=cr.delta, flagged=cr.flagged,
        ))

    await db.commit()
    return individual_score


async def aggregate_church(instance_id: str, db: AsyncSession) -> Optional[ChurchAggregateScore]:
    """Aggregate all scored sessions for an instance. Idempotent: replaces any
    prior aggregate for the instance."""
    instance = (await db.execute(
        select(SurveyInstance).where(SurveyInstance.id == instance_id)
        .options(selectinload(SurveyInstance.sessions))
    )).scalar_one_or_none()
    if not instance:
        return None

    composites = []
    pillar_lists = {p: [] for p in _AGG_PILLARS}
    tier_counts = {
        "Spiritually Disengaged": 0, "Nominal": 0, "Growing": 0,
        "Grounded": 0, "Multiplying Disciple": 0,
    }

    for session in instance.sessions:
        if not session.is_complete:
            continue
        ind = (await db.execute(
            select(IndividualScore).where(IndividualScore.session_id == session.id)
            .options(selectinload(IndividualScore.pillar_scores))
        )).scalar_one_or_none()
        if not ind:
            continue
        composites.append(ind.composite_score)
        tier_counts[ind.maturity_tier] = tier_counts.get(ind.maturity_tier, 0) + 1
        for ps in ind.pillar_scores:
            if ps.pillar in pillar_lists:
                pillar_lists[ps.pillar].append(ps.normalized_score)

    if not composites:
        return None

    total = len(composites)
    health = round(mean(composites), 2)
    pillar_avgs = {p: round(mean(v), 2) if v else 0 for p, v in pillar_lists.items()}
    maturity_dist = {k: round(v / total * 100, 1) for k, v in tier_counts.items()}
    archetype = classify_archetype(pillar_avgs)
    drift_score = round((1 - pillar_avgs.get("drift_vulnerability", 50) / 100) * 100, 2)
    drift_level = (
        "low" if drift_score <= 25 else
        "moderate" if drift_score <= 50 else
        "high" if drift_score <= 75 else "critical"
    )

    # Replace any prior aggregate (survey_instance_id is unique).
    prior = (await db.execute(
        select(ChurchAggregateScore).where(ChurchAggregateScore.survey_instance_id == instance_id)
    )).scalar_one_or_none()
    if prior is not None:
        await db.delete(prior)
        await db.flush()

    agg = ChurchAggregateScore(
        survey_instance_id=instance_id, church_id=instance.church_id,
        health_score=health, respondent_count=total, archetype=archetype,
        drift_risk_score=drift_score, drift_risk_level=drift_level,
        maturity_distribution=maturity_dist, pillar_scores=pillar_avgs,
    )
    db.add(agg)
    await db.commit()
    return agg


async def score_and_aggregate(session_id: str) -> None:
    """Auto-trigger entry point (background task): score the session, then refresh
    its church aggregate. Opens its own DB session so it can run after the request
    has returned."""
    from app.database import AsyncSessionLocal  # resolved at call time (test-overridable)

    async with AsyncSessionLocal() as db:
        score = await score_session(session_id, db)
        if score is None:
            return
        session = (await db.execute(
            select(RespondentSession).where(RespondentSession.id == session_id)
        )).scalar_one_or_none()
        if session is not None:
            await aggregate_church(session.survey_instance_id, db)
