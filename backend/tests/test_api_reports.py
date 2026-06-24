"""
API tests for report export (HTML always; PDF gated on optional WeasyPrint).
Also covers the report rendering service directly. Requires a Postgres test DB.
"""
import pytest

from app.core.security import create_access_token, hash_password
from app.models import (
    Church, User, SurveyTemplate, SurveyInstance, RespondentSession,
    IndividualScore, PillarScore, ChurchAggregateScore,
)
from app.services.reports import render_individual_html, render_church_html, weasyprint_available

# Note: no module-level asyncio mark — this file mixes sync (pure render) and
# async (API) tests; asyncio_mode=auto runs the async ones without a mark.

REP = "/api/v1/reports"


# ── pure rendering ────────────────────────────────────────────────────────────

def test_individual_html_contains_score_and_tier():
    html = render_individual_html({
        "composite_score": 71.0, "maturity_tier": "Grounded", "drift_risk_level": "low",
        "pillar_scores": {"doctrinal_integrity": 80.0}, "pillar_statuses": {"doctrinal_integrity": "strength"},
        "recommendations": [], "credibility_warning": False,
    })
    assert "<!DOCTYPE html>" in html
    # Grounded is remapped to "Growing" in display.
    assert "71.0" in html and "Growing" in html
    assert "Doctrinal Integrity" in html


def test_church_html_contains_archetype():
    html = render_church_html({
        "health_score": 68.0, "archetype": "Quietly Healthy", "respondent_count": 22,
        "pillar_scores": {"discipleship_depth": 61.0}, "maturity_distribution": {"Grounded": 50.0},
        "drift_risk_level": "low", "recommendations": [],
    })
    # Archetype is no longer rendered in the UI; verify the score + a pillar name instead.
    assert "68.0" in html and "Discipleship Depth" in html


# ── individual export ─────────────────────────────────────────────────────────

async def _scored_session(db, token="exp-tok-1"):
    church = Church(name="Report Church")
    template = SurveyTemplate(name="Full", version="1.0")
    db.add_all([church, template])
    await db.flush()
    instance = SurveyInstance(church_id=church.id, template_id=template.id,
                              assessment_cycle="Q1-2026", status="active")
    db.add(instance)
    await db.flush()
    session = RespondentSession(survey_instance_id=instance.id, anonymous_token=token)
    db.add(session)
    await db.flush()
    score = IndividualScore(session_id=session.id, composite_score=71.0, maturity_tier="Grounded")
    db.add(score)
    await db.flush()
    db.add(PillarScore(individual_score_id=score.id, pillar="doctrinal_integrity",
                       normalized_score=80.0, status="strength", question_count=10))
    await db.commit()
    return instance, token


async def test_export_individual_html(client, db):
    instance, token = await _scored_session(db)
    resp = await client.get(f"{REP}/individual/by-token/{token}/export")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    assert "Growing" in resp.text  # Grounded is remapped to Growing for display


async def test_export_individual_pdf_when_weasyprint_absent(client, db):
    instance, token = await _scored_session(db)
    resp = await client.get(f"{REP}/individual/by-token/{token}/export?fmt=pdf")
    if weasyprint_available():
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
    else:
        assert resp.status_code == 501


async def test_export_individual_unknown_token_404(client, db):
    resp = await client.get(f"{REP}/individual/by-token/nope/export")
    assert resp.status_code == 404


async def test_export_rejects_bad_format(client, db):
    instance, token = await _scored_session(db)
    resp = await client.get(f"{REP}/individual/by-token/{token}/export?fmt=xml")
    assert resp.status_code == 422  # Query pattern validation


# ── church export ─────────────────────────────────────────────────────────────

async def _church_with_agg(db, count):
    church = Church(name="Agg Church")
    template = SurveyTemplate(name="Full", version="1.0")
    db.add_all([church, template])
    await db.flush()
    instance = SurveyInstance(church_id=church.id, template_id=template.id,
                              assessment_cycle="Q1-2026", status="active")
    db.add(instance)
    await db.flush()
    admin = User(email=f"a-{church.id[:8]}@t.org", password_hash=hash_password("x"),
                 role="admin", church_id=church.id, is_active=True)
    db.add(admin)
    db.add(ChurchAggregateScore(
        survey_instance_id=instance.id, church_id=church.id, health_score=68.0,
        archetype="Quietly Healthy", respondent_count=count,
        pillar_scores={"discipleship_depth": 61.0}, maturity_distribution={"Grounded": 100.0},
        drift_risk_level="low", drift_risk_score=10.0,
    ))
    await db.commit()
    await db.refresh(admin)
    return instance, admin


def _auth(user):
    return {"Authorization": f"Bearer {create_access_token({'sub': user.id})}"}


async def test_export_church_html(client, db):
    instance, admin = await _church_with_agg(db, count=22)
    resp = await client.get(f"{REP}/church/{instance.id}/export", headers=_auth(admin))
    assert resp.status_code == 200
    assert "Church Health Report" in resp.text


async def test_export_church_works_at_low_count(client, db):
    # Floor is off: export succeeds from the first response.
    instance, admin = await _church_with_agg(db, count=3)
    resp = await client.get(f"{REP}/church/{instance.id}/export", headers=_auth(admin))
    assert resp.status_code == 200
    assert "Church Health Report" in resp.text
