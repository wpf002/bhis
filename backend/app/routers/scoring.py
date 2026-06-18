from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from statistics import mean

from app.database import get_db
from app.models import (
    RespondentSession, Response, Question, QuestionOption,
    IndividualScore, PillarScore, ContradictionFlag,
    SurveyInstance, ChurchAggregateScore, User
)
from app.services.scoring_engine import (
    QuestionScore, score_individual,
    normalize_likert, normalize_option_score,
)
from app.services.archetype_engine import classify_archetype
from app.core.dependencies import get_current_user, require_role

router = APIRouter()


async def _build_question_scores(session_id: str, db: AsyncSession):
    """Pull responses and build QuestionScore list for the scoring engine."""
    result = await db.execute(
        select(Response)
        .where(Response.session_id == session_id)
        .options(
            selectinload(Response.question),
            selectinload(Response.selected_option),
        )
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

        question_scores.append(QuestionScore(
            question_number=q.question_number,
            pillar=q.pillar,
            normalized_score=normalized,
            question_type=q.question_type,
            qualitative_only=q.qualitative_only,
        ))

    return question_scores


@router.post("/individual/{session_id}")
async def score_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(RespondentSession).where(RespondentSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session or not session.is_complete:
        raise HTTPException(status_code=404, detail="Session not found or not complete")

    question_scores = await _build_question_scores(session_id, db)
    scoring_result = score_individual(question_scores)

    # Persist
    individual_score = IndividualScore(
        session_id=session_id,
        composite_score=scoring_result.composite_score,
        maturity_tier=scoring_result.maturity_tier,
        contradiction_count=scoring_result.contradiction_count,
        credibility_warning=scoring_result.credibility_warning,
        drift_risk_level=scoring_result.drift_risk_level,
        drift_signal_count=scoring_result.drift_signal_count,
    )
    db.add(individual_score)
    await db.flush()

    for pillar, pr in scoring_result.pillar_results.items():
        db.add(PillarScore(
            individual_score_id=individual_score.id,
            pillar=pillar,
            raw_score=pr.raw_score,
            normalized_score=pr.normalized_score,
            question_count=pr.question_count,
            status=pr.status,
        ))

    for cr in scoring_result.contradiction_results:
        db.add(ContradictionFlag(
            individual_score_id=individual_score.id,
            pair_id=cr.pair_id,
            question_a_number=cr.question_a,
            question_b_number=cr.question_b,
            score_a=cr.score_a,
            score_b=cr.score_b,
            delta=cr.delta,
            flagged=cr.flagged,
        ))

    await db.commit()
    return {"status": "scored", "composite_score": scoring_result.composite_score, "tier": scoring_result.maturity_tier}


@router.post("/church/{instance_id}")
async def aggregate_church(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "leader")),
):
    result = await db.execute(
        select(SurveyInstance)
        .where(SurveyInstance.id == instance_id)
        .options(selectinload(SurveyInstance.sessions))
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Survey instance not found")

    # Collect all individual scores for this instance
    complete_sessions = [s for s in instance.sessions if s.is_complete]
    if not complete_sessions:
        raise HTTPException(status_code=400, detail="No completed responses yet")

    individual_scores_data = []
    all_pillar_scores = {p: [] for p in [
        "doctrinal_integrity", "spiritual_discipline", "transformation_fruit",
        "discipleship_depth", "church_health_trust", "engagement_alignment"
    ]}
    tier_counts = {"Spiritually Disengaged": 0, "Nominal": 0, "Growing": 0, "Grounded": 0, "Multiplying Disciple": 0}

    for session in complete_sessions:
        score_result = await db.execute(
            select(IndividualScore)
            .where(IndividualScore.session_id == session.id)
            .options(selectinload(IndividualScore.pillar_scores))
        )
        ind_score = score_result.scalar_one_or_none()
        if not ind_score:
            continue

        individual_scores_data.append(ind_score.composite_score)
        tier_counts[ind_score.maturity_tier] = tier_counts.get(ind_score.maturity_tier, 0) + 1

        for ps in ind_score.pillar_scores:
            if ps.pillar in all_pillar_scores:
                all_pillar_scores[ps.pillar].append(ps.normalized_score)

    if not individual_scores_data:
        raise HTTPException(status_code=400, detail="No scored responses found")

    health_score = round(mean(individual_scores_data), 2)
    pillar_avgs = {p: round(mean(scores), 2) if scores else 0 for p, scores in all_pillar_scores.items()}
    total = len(individual_scores_data)
    maturity_dist = {k: round(v / total * 100, 1) for k, v in tier_counts.items()}
    archetype = classify_archetype(pillar_avgs)

    # Drift risk
    drift_score = round((1 - pillar_avgs.get("drift_vulnerability", 50) / 100) * 100, 2)

    if drift_score <= 25:
        drift_level = "low"
    elif drift_score <= 50:
        drift_level = "moderate"
    elif drift_score <= 75:
        drift_level = "high"
    else:
        drift_level = "critical"

    agg = ChurchAggregateScore(
        survey_instance_id=instance_id,
        church_id=instance.church_id,
        health_score=health_score,
        respondent_count=total,
        archetype=archetype,
        drift_risk_score=drift_score,
        drift_risk_level=drift_level,
        maturity_distribution=maturity_dist,
        pillar_scores=pillar_avgs,
    )
    db.add(agg)
    await db.commit()

    return {
        "health_score": health_score,
        "archetype": archetype,
        "respondent_count": total,
        "pillar_scores": pillar_avgs,
        "maturity_distribution": maturity_dist,
        "drift_risk_level": drift_level,
    }
