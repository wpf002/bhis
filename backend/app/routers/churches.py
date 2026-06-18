from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Church, User, ChurchAggregateScore
from app.schemas import ChurchCreate, ChurchResponse, ChurchDashboardSchema
from app.services.privacy import is_below_floor, suppressed_payload
from app.core.dependencies import get_current_user, require_role

router = APIRouter()


@router.post("", response_model=ChurchResponse, status_code=201)
async def create_church(
    payload: ChurchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "leader")),
):
    church = Church(**payload.model_dump())
    db.add(church)
    await db.commit()
    await db.refresh(church)
    return church


@router.get("/{church_id}", response_model=ChurchResponse)
async def get_church(
    church_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Church).where(Church.id == church_id))
    church = result.scalar_one_or_none()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    return church


@router.get("/{church_id}/dashboard")
async def get_dashboard(
    church_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "leader")),
):
    result = await db.execute(select(Church).where(Church.id == church_id))
    church = result.scalar_one_or_none()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")

    # Get latest aggregate score
    agg_result = await db.execute(
        select(ChurchAggregateScore)
        .where(ChurchAggregateScore.church_id == church_id)
        .order_by(ChurchAggregateScore.calculated_at.desc())
        .limit(1)
    )
    agg = agg_result.scalar_one_or_none()

    # No responses scored yet — nothing to suppress, just an empty dashboard.
    if not agg:
        return {
            "church": church,
            "health_score": None,
            "archetype": None,
            "drift_risk_level": None,
            "drift_risk_score": None,
            "respondent_count": None,
            "maturity_distribution": None,
            "pillar_scores": None,
            "suppressed": False,
        }

    # Anonymity floor: below N_MIN respondents, withhold the breakdown.
    if is_below_floor(agg.respondent_count):
        return {"church": church, **suppressed_payload(agg.respondent_count)}

    return {
        "church": church,
        "health_score": agg.health_score,
        "archetype": agg.archetype,
        "drift_risk_level": agg.drift_risk_level,
        "drift_risk_score": agg.drift_risk_score,
        "respondent_count": agg.respondent_count,
        "maturity_distribution": agg.maturity_distribution,
        "pillar_scores": agg.pillar_scores,
        "suppressed": False,
    }
