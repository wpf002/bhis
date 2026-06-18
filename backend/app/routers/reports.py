from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import IndividualScore, ChurchAggregateScore, User
from app.services.recommendation_engine import generate_church_recommendations, generate_individual_recommendations
from app.services.privacy import apply_min_n_floor, is_below_floor, suppressed_payload
from app.core.dependencies import get_current_user, require_role

# ── Reports ───────────────────────────────────────────────────────────────────
router = APIRouter()


@router.get("/individual/{session_id}")
async def individual_report(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(IndividualScore)
        .where(IndividualScore.session_id == session_id)
        .options(
            selectinload(IndividualScore.pillar_scores),
            selectinload(IndividualScore.contradiction_flags),
        )
    )
    score = result.scalar_one_or_none()
    if not score:
        raise HTTPException(status_code=404, detail="Score not found")

    pillar_scores = {ps.pillar: ps.normalized_score for ps in score.pillar_scores}
    pillar_statuses = {ps.pillar: ps.status for ps in score.pillar_scores}
    recs = generate_individual_recommendations(pillar_scores, score.maturity_tier, score.credibility_warning)

    return {
        "composite_score": score.composite_score,
        "maturity_tier": score.maturity_tier,
        "contradiction_count": score.contradiction_count,
        "credibility_warning": score.credibility_warning,
        "drift_risk_level": score.drift_risk_level,
        "pillar_scores": pillar_scores,
        "pillar_statuses": pillar_statuses,
        "recommendations": [
            {
                "priority": r.priority,
                "pillar": r.pillar,
                "title": r.title,
                "urgency": r.urgency,
                "diagnosis": r.diagnosis,
                "biblical_anchor": r.biblical_anchor,
                "intervention": r.intervention,
                "timeline": r.timeline,
            }
            for r in recs
        ],
    }


@router.get("/church/{instance_id}")
async def church_report(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "leader")),
):
    result = await db.execute(
        select(ChurchAggregateScore)
        .where(ChurchAggregateScore.survey_instance_id == instance_id)
    )
    agg = result.scalar_one_or_none()
    if not agg:
        raise HTTPException(status_code=404, detail="Church score not found. Run aggregation first.")

    # Anonymity floor: below N_MIN respondents, withhold the entire breakdown
    # (and the recommendations that derive from it) to prevent re-identification.
    if is_below_floor(agg.respondent_count):
        return suppressed_payload(agg.respondent_count)

    recs = generate_church_recommendations(agg.pillar_scores or {}, agg.archetype or "")

    return {
        "health_score": agg.health_score,
        "archetype": agg.archetype,
        "respondent_count": agg.respondent_count,
        "drift_risk_level": agg.drift_risk_level,
        "drift_risk_score": agg.drift_risk_score,
        "maturity_distribution": agg.maturity_distribution,
        "pillar_scores": agg.pillar_scores,
        "suppressed": False,
        "recommendations": [
            {
                "priority": r.priority,
                "pillar": r.pillar,
                "title": r.title,
                "urgency": r.urgency,
                "diagnosis": r.diagnosis,
                "biblical_anchor": r.biblical_anchor,
                "intervention": r.intervention,
                "timeline": r.timeline,
            }
            for r in recs
        ],
    }
