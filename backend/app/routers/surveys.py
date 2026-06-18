import random
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import SurveyTemplate, SurveyInstance, Question, User
from app.schemas import SurveyInstanceCreate, SurveyInstanceResponse, QuestionSchema
from app.core.dependencies import get_current_user, require_role

router = APIRouter()

# Only these status moves are allowed; anything else is rejected.
ALLOWED_TRANSITIONS = {
    "draft": {"active"},
    "active": {"closed"},
    "closed": set(),
    "archived": set(),
}

# Question types whose options must be presented in random order to avoid
# position bias. Open-ended / likert / forced-prioritization keep their order.
SHUFFLE_TYPES = {"mc", "scenario"}


def _assert_transition(current: str, target: str) -> None:
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise HTTPException(status_code=400, detail=f"Cannot move survey from '{current}' to '{target}'")


async def _maybe_autoclose(instance: SurveyInstance, db: AsyncSession) -> None:
    """Lazily close an active survey whose close_date has passed (no scheduler)."""
    if (
        instance.status == "active"
        and instance.close_date is not None
        and instance.close_date < datetime.now(timezone.utc)
    ):
        instance.status = "closed"
        await db.commit()


async def _owned_instance(instance_id: str, current_user: User, db: AsyncSession) -> SurveyInstance:
    instance = (await db.execute(
        select(SurveyInstance).where(SurveyInstance.id == instance_id)
    )).scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Survey instance not found")
    if instance.church_id != current_user.church_id:
        raise HTTPException(status_code=403, detail="Survey belongs to another church")
    return instance


@router.get("/templates")
async def list_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SurveyTemplate).where(SurveyTemplate.is_active == True)  # noqa: E712
    )
    return result.scalars().all()


@router.post("/instances", response_model=SurveyInstanceResponse, status_code=201)
async def create_instance(
    payload: SurveyInstanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "leader")),
):
    instance = SurveyInstance(
        church_id=current_user.church_id,
        template_id=payload.template_id,
        assessment_cycle=payload.assessment_cycle,
        close_date=payload.close_date,
        created_by=current_user.id,
    )
    db.add(instance)
    await db.commit()
    await db.refresh(instance)
    return instance


@router.post("/instances/{instance_id}/launch", response_model=SurveyInstanceResponse)
async def launch_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "leader")),
):
    instance = await _owned_instance(instance_id, current_user, db)
    _assert_transition(instance.status, "active")
    instance.status = "active"
    instance.launch_date = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(instance)
    return instance


@router.post("/instances/{instance_id}/close", response_model=SurveyInstanceResponse)
async def close_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "leader")),
):
    instance = await _owned_instance(instance_id, current_user, db)
    _assert_transition(instance.status, "closed")
    instance.status = "closed"
    await db.commit()
    await db.refresh(instance)
    return instance


@router.get("/instances/{instance_id}")
async def instance_meta(instance_id: str, db: AsyncSession = Depends(get_db)):
    """Public survey metadata for the start screen (count + estimated time)."""
    instance = (await db.execute(
        select(SurveyInstance).where(SurveyInstance.id == instance_id)
    )).scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Survey not found")
    await _maybe_autoclose(instance, db)

    template = (await db.execute(
        select(SurveyTemplate).where(SurveyTemplate.id == instance.template_id)
    )).scalar_one_or_none()
    question_count = (await db.execute(
        select(func.count(Question.id)).where(Question.template_id == instance.template_id)
    )).scalar_one()

    return {
        "id": instance.id,
        "status": instance.status,
        "question_count": question_count,
        "estimated_minutes": template.estimated_minutes if template else None,
        "respondent_count": instance.respondent_count,
        "close_date": instance.close_date,
    }


@router.get("/instances/{instance_id}/questions", response_model=list[QuestionSchema])
async def get_questions(instance_id: str, db: AsyncSession = Depends(get_db)):
    instance = (await db.execute(
        select(SurveyInstance).where(SurveyInstance.id == instance_id)
    )).scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Survey not found or not active")
    await _maybe_autoclose(instance, db)
    if instance.status != "active":
        raise HTTPException(status_code=404, detail="Survey not found or not active")

    q_result = await db.execute(
        select(Question)
        .where(Question.template_id == instance.template_id)
        .options(selectinload(Question.options))
        .order_by(Question.question_number)
    )
    questions = q_result.scalars().all()

    payload = []
    for q in questions:
        options = list(q.options)
        if q.question_type in SHUFFLE_TYPES:
            random.shuffle(options)  # per-request order to avoid position bias
        payload.append({
            "id": q.id,
            "question_number": q.question_number,
            "pillar": q.pillar,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "qualitative_only": q.qualitative_only,
            "options": [
                {"id": o.id, "option_letter": o.option_letter, "option_text": o.option_text}
                for o in options
            ],
        })
    return payload
