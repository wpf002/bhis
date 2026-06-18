from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.services.scoring_pipeline import score_session, aggregate_church
from app.core.dependencies import get_current_user, require_role

router = APIRouter()


@router.post("/individual/{session_id}")
async def score_session_endpoint(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    score = await score_session(session_id, db)
    if score is None:
        raise HTTPException(status_code=404, detail="Session not found or not complete")
    return {"status": "scored", "composite_score": score.composite_score, "tier": score.maturity_tier}


@router.post("/church/{instance_id}")
async def aggregate_church_endpoint(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "leader")),
):
    agg = await aggregate_church(instance_id, db)
    if agg is None:
        raise HTTPException(status_code=400, detail="No completed/scored responses yet")
    return {
        "health_score": agg.health_score,
        "archetype": agg.archetype,
        "respondent_count": agg.respondent_count,
        "pillar_scores": agg.pillar_scores,
        "maturity_distribution": agg.maturity_distribution,
        "drift_risk_level": agg.drift_risk_level,
    }
