from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.models import RespondentSession, Response, SurveyInstance
from app.schemas import SessionStart, SessionResponse, BulkResponseSubmit
from app.core.security import generate_capability_token

router = APIRouter()


async def _authorize_session(
    session_id: str,
    token: Optional[str],
    db: AsyncSession,
) -> RespondentSession:
    """Resolve a session and prove the caller holds its capability token.

    Survey participation is anonymous: there is no logged-in user to check
    against. Authority comes from possessing the unguessable token returned at
    session start. A mismatched/missing token is indistinguishable from not
    knowing the session exists, so we 404 rather than 403 to avoid confirming ids.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Missing session token")
    result = await db.execute(
        select(RespondentSession).where(RespondentSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session or session.anonymous_token != token:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def start_session(
    payload: SessionStart,
    db: AsyncSession = Depends(get_db),
):
    """Start an anonymous survey session. No authentication: a member follows an
    invite link and begins. The session carries no user_id; it is reachable only
    via the capability token returned here."""
    result = await db.execute(
        select(SurveyInstance).where(SurveyInstance.id == payload.survey_instance_id)
    )
    instance = result.scalar_one_or_none()
    if not instance or instance.status != "active":
        raise HTTPException(status_code=404, detail="Survey not found or not active")

    session = RespondentSession(
        survey_instance_id=payload.survey_instance_id,
        anonymous_token=generate_capability_token(),
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
    x_session_token: Optional[str] = Header(default=None),
):
    session = await _authorize_session(session_id, x_session_token, db)

    for r in payload.responses:
        response = Response(
            session_id=session.id,
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
    x_session_token: Optional[str] = Header(default=None),
):
    session = await _authorize_session(session_id, x_session_token, db)

    session.is_complete = True
    session.completed_at = datetime.utcnow()
    await db.commit()
    return {"status": "complete", "session_id": session_id}
