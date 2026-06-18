from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.database import get_db
from app.models import RespondentSession, Response, SurveyInstance, User
from app.schemas import SessionStart, SessionResponse, BulkResponseSubmit
from app.core.dependencies import get_current_user

router = APIRouter()


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def start_session(
    payload: SessionStart,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SurveyInstance).where(SurveyInstance.id == payload.survey_instance_id)
    )
    instance = result.scalar_one_or_none()
    if not instance or instance.status != "active":
        raise HTTPException(status_code=404, detail="Survey not found or not active")

    session = RespondentSession(
        survey_instance_id=payload.survey_instance_id,
        user_id=current_user.id,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.put("/sessions/{session_id}")
async def submit_responses(
    session_id: str,
    payload: BulkResponseSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(RespondentSession).where(RespondentSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your session")

    for r in payload.responses:
        response = Response(
            session_id=session_id,
            question_id=r.question_id,
            selected_option_id=r.selected_option_id,
            likert_value=r.likert_value,
            text_response=r.text_response,
            ranking_order=r.ranking_order,
            response_time_seconds=r.response_time_seconds,
        )
        db.add(response)

    await db.commit()
    return {"status": "saved", "count": len(payload.responses)}


@router.post("/sessions/{session_id}/complete")
async def complete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(RespondentSession).where(RespondentSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.is_complete = True
    session.completed_at = datetime.utcnow()
    await db.commit()
    return {"status": "complete", "session_id": session_id}
