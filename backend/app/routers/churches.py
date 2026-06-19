from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models import Church, User, ChurchAggregateScore, ChurchInvite
from app.schemas import (
    ChurchCreate, ChurchResponse, ChurchDashboardSchema,
    InviteCreate, InviteResponse, ChurchSettingsUpdate,
)
from app.services.privacy import is_below_floor, suppressed_payload
from app.core.security import generate_capability_token, hash_token
from app.core.dependencies import get_current_user, require_role

router = APIRouter()


@router.post("/{church_id}/invites", response_model=InviteResponse, status_code=201)
async def create_invite(
    church_id: str,
    payload: InviteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "leader")),
):
    """Generate a single-use invite to register into this church with a preset
    role. An admin/leader may only invite into their OWN church."""
    church = (await db.execute(select(Church).where(Church.id == church_id))).scalar_one_or_none()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    if current_user.church_id != church_id:
        raise HTTPException(status_code=403, detail="Cannot invite into another church")

    raw = generate_capability_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=payload.expires_in_days)
    db.add(ChurchInvite(
        church_id=church_id,
        role=payload.role,
        email=payload.email,
        token_hash=hash_token(raw),
        expires_at=expires_at,
        created_by=current_user.id,
    ))
    await db.commit()
    return InviteResponse(
        token=raw,
        join_url=f"{settings.FRONTEND_URL}/join/{raw}",
        role=payload.role,
        expires_at=expires_at,
    )


@router.post("", response_model=ChurchResponse, status_code=201)
async def create_church(
    payload: ChurchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "leader")),
):
    church = Church(**payload.model_dump())
    db.add(church)
    await db.flush()
    # Onboarding: link the creating admin/leader to their new church if unassigned.
    if current_user.church_id is None:
        current_user.church_id = church.id
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
    if not church or not church.is_active:
        raise HTTPException(status_code=404, detail="Church not found")
    return church


@router.put("/{church_id}/settings", response_model=ChurchResponse)
async def update_church_settings(
    church_id: str,
    payload: ChurchSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "leader")),
):
    """Update a church's settings. Admins/leaders may only edit their own church."""
    church = (await db.execute(select(Church).where(Church.id == church_id))).scalar_one_or_none()
    if not church or not church.is_active:
        raise HTTPException(status_code=404, detail="Church not found")
    if current_user.church_id != church_id:
        raise HTTPException(status_code=403, detail="Cannot edit another church")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(church, field, value)
    await db.commit()
    await db.refresh(church)
    return church


@router.delete("/{church_id}", status_code=200)
async def deactivate_church(
    church_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Soft-delete: deactivate the church (preserve data), admins of that church only."""
    church = (await db.execute(select(Church).where(Church.id == church_id))).scalar_one_or_none()
    if not church or not church.is_active:
        raise HTTPException(status_code=404, detail="Church not found")
    if current_user.church_id != church_id:
        raise HTTPException(status_code=403, detail="Cannot deactivate another church")

    church.is_active = False
    await db.commit()
    return {"status": "deactivated", "church_id": church_id}


@router.get("/{church_id}/dashboard")
async def get_dashboard(
    church_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "leader")),
):
    result = await db.execute(select(Church).where(Church.id == church_id))
    church = result.scalar_one_or_none()
    if not church or not church.is_active:
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
        "survey_instance_id": agg.survey_instance_id,
        "health_score": agg.health_score,
        "archetype": agg.archetype,
        "drift_risk_level": agg.drift_risk_level,
        "drift_risk_score": agg.drift_risk_score,
        "respondent_count": agg.respondent_count,
        "maturity_distribution": agg.maturity_distribution,
        "pillar_scores": agg.pillar_scores,
        "suppressed": False,
    }
