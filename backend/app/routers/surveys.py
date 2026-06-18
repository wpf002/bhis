from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import SurveyTemplate, SurveyInstance, Question, User
from app.schemas import SurveyInstanceCreate, SurveyInstanceResponse, QuestionSchema
from app.core.dependencies import get_current_user, require_role
from datetime import datetime

router = APIRouter()


@router.get("/templates")
async def list_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SurveyTemplate).where(SurveyTemplate.is_active == True)
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
    result = await db.execute(select(SurveyInstance).where(SurveyInstance.id == instance_id))
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Survey instance not found")
    if instance.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft surveys can be launched")

    instance.status = "active"
    instance.launch_date = datetime.utcnow()
    await db.commit()
    await db.refresh(instance)
    return instance


@router.get("/instances/{instance_id}/questions", response_model=list[QuestionSchema])
async def get_questions(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SurveyInstance).where(SurveyInstance.id == instance_id))
    instance = result.scalar_one_or_none()
    if not instance or instance.status != "active":
        raise HTTPException(status_code=404, detail="Survey not found or not active")

    q_result = await db.execute(
        select(Question)
        .where(Question.template_id == instance.template_id)
        .options(selectinload(Question.options))
        .order_by(Question.question_number)
    )
    return q_result.scalars().all()
