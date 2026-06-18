from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models import (
    IndividualScore, ChurchAggregateScore, RespondentSession,
    UserReportToken, ReportDelivery, User,
)
from app.schemas import ClaimReportRequest, DeliverReportRequest
from app.services.recommendation_engine import generate_church_recommendations, generate_individual_recommendations
from app.services.privacy import is_below_floor, suppressed_payload
from app.services.email import send_email
from app.services.email.templates import report_ready
from app.services.reports import (
    render_individual_html, render_church_html, render_pdf, ReportError,
)
from app.core.dependencies import get_current_user, require_role


def _export_response(html: str, fmt: str, filename: str) -> Response:
    """Render an HTML report, or a PDF if requested and WeasyPrint is available."""
    if fmt == "pdf":
        try:
            pdf = render_pdf(html)
        except ReportError as exc:
            raise HTTPException(status_code=501, detail=str(exc))
        return Response(
            content=pdf, media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'},
        )
    return Response(content=html, media_type="text/html")

# ── Reports ───────────────────────────────────────────────────────────────────
router = APIRouter()


def _serialize_individual_score(score: IndividualScore) -> dict:
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


async def _score_for_token(token: str, db: AsyncSession) -> IndividualScore:
    """Resolve an individual score from a capability token, with no identity
    lookup. The token is the authority — there is intentionally no JWT/role path
    to an individual's report, so a church admin cannot reach it (see
    docs/anonymity-design.md)."""
    session_result = await db.execute(
        select(RespondentSession).where(RespondentSession.anonymous_token == token)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Report not found")

    result = await db.execute(
        select(IndividualScore)
        .where(IndividualScore.session_id == session.id)
        .options(
            selectinload(IndividualScore.pillar_scores),
            selectinload(IndividualScore.contradiction_flags),
        )
    )
    score = result.scalar_one_or_none()
    if not score:
        raise HTTPException(status_code=404, detail="Report not scored yet")
    return score


@router.get("/individual/by-token/{token}")
async def individual_report_by_token(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """A member reads their OWN report by presenting the capability token they
    received at survey start. No login; no identity is ever resolved."""
    score = await _score_for_token(token, db)
    return _serialize_individual_score(score)


@router.post("/deliver", status_code=201)
async def deliver_report(
    payload: DeliverReportRequest,
    db: AsyncSession = Depends(get_db),
):
    """Email a member their own report link. Anonymous: authority is the
    capability token, not a login. The email address is recorded only to send,
    in a row with no church_id/user_id — the church cannot traverse to it."""
    session_result = await db.execute(
        select(RespondentSession).where(RespondentSession.anonymous_token == payload.session_token)
    )
    if session_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Report not found")

    delivery = ReportDelivery(session_token=payload.session_token, email=payload.email)
    db.add(delivery)

    report_url = f"{settings.FRONTEND_URL}/report/{payload.session_token}"
    subject, html = report_ready(report_url)
    send_email(to=payload.email, subject=subject, html=html)

    delivery.sent_at = datetime.utcnow()
    await db.commit()
    return {"status": "sent"}


@router.post("/claim", status_code=201)
async def claim_report(
    payload: ClaimReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Optional: attach a capability token to the logged-in user's personal
    keyring so they can find their report later. This stores an opaque token
    against the user — it creates NO link the church can traverse from a
    response back to the member."""
    # The token must actually resolve to a session (can't keyring a random string).
    session_result = await db.execute(
        select(RespondentSession).where(RespondentSession.anonymous_token == payload.session_token)
    )
    if session_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Report not found")

    existing = await db.execute(
        select(UserReportToken).where(
            UserReportToken.user_id == current_user.id,
            UserReportToken.session_token == payload.session_token,
        )
    )
    if existing.scalar_one_or_none() is None:
        db.add(UserReportToken(user_id=current_user.id, session_token=payload.session_token))
        await db.commit()
    return {"status": "claimed"}


@router.get("/mine")
async def my_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List the capability tokens on the current user's keyring."""
    result = await db.execute(
        select(UserReportToken).where(UserReportToken.user_id == current_user.id)
    )
    tokens = result.scalars().all()
    return {"reports": [{"session_token": t.session_token, "claimed_at": t.created_at} for t in tokens]}


def _church_report_data(agg: ChurchAggregateScore) -> dict:
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


async def _church_agg_or_404(instance_id: str, db: AsyncSession) -> ChurchAggregateScore:
    agg = (await db.execute(
        select(ChurchAggregateScore).where(ChurchAggregateScore.survey_instance_id == instance_id)
    )).scalar_one_or_none()
    if not agg:
        raise HTTPException(status_code=404, detail="Church score not found. Run aggregation first.")
    return agg


@router.get("/church/{instance_id}")
async def church_report(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "leader")),
):
    agg = await _church_agg_or_404(instance_id, db)
    # Anonymity floor: below N_MIN respondents, withhold the entire breakdown
    # (and the recommendations that derive from it) to prevent re-identification.
    if is_below_floor(agg.respondent_count):
        return suppressed_payload(agg.respondent_count)
    return _church_report_data(agg)


@router.get("/individual/by-token/{token}/export")
async def export_individual_report(
    token: str,
    fmt: str = Query("html", pattern="^(html|pdf)$"),
    db: AsyncSession = Depends(get_db),
):
    """Download a member's own report (HTML, or PDF if WeasyPrint is installed),
    authorized solely by the capability token."""
    score = await _score_for_token(token, db)
    html = render_individual_html(_serialize_individual_score(score))
    return _export_response(html, fmt, filename="bhis-report")


@router.get("/church/{instance_id}/export")
async def export_church_report(
    instance_id: str,
    fmt: str = Query("html", pattern="^(html|pdf)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "leader")),
):
    """Download the church report. Suppressed below the anonymity floor."""
    agg = await _church_agg_or_404(instance_id, db)
    if is_below_floor(agg.respondent_count):
        raise HTTPException(status_code=409, detail="Report suppressed: below the anonymity threshold")
    html = render_church_html(_church_report_data(agg))
    return _export_response(html, fmt, filename="bhis-church-report")
