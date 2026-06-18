"""
API tests for response validation: idempotent upsert, required-question
enforcement on complete, bot/fast-completion flagging, and blocking writes to
completed/closed surveys. Requires a Postgres test DB (see conftest.py).
"""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, func

from app.models import (
    Church, SurveyTemplate, SurveyInstance, Question, RespondentSession, Response,
)

pytestmark = pytest.mark.asyncio

R = "/api/v1/responses"


async def _setup(db, status="active"):
    church = Church(name="Validation Church")
    template = SurveyTemplate(name="Full", version="1.0")
    db.add_all([church, template])
    await db.flush()
    instance = SurveyInstance(church_id=church.id, template_id=template.id,
                              assessment_cycle="Q1-2026", status=status)
    db.add(instance)
    await db.flush()
    q1 = Question(template_id=template.id, question_number=1, pillar="spiritual_discipline",
                  question_text="Likert", question_type="likert")
    q2 = Question(template_id=template.id, question_number=2, pillar="discipleship_depth",
                  question_text="MC", question_type="mc")
    q3 = Question(template_id=template.id, question_number=3, pillar="church_health_trust",
                  question_text="Open", question_type="open_ended")
    db.add_all([q1, q2, q3])
    await db.commit()
    for o in (instance, q1, q2, q3):
        await db.refresh(o)
    return instance, q1, q2, q3


async def _start(client, instance):
    body = (await client.post(f"{R}/sessions", json={"survey_instance_id": instance.id})).json()
    return body["id"], body["anonymous_token"]


def _hdr(token):
    return {"X-Session-Token": token}


# ── idempotency ───────────────────────────────────────────────────────────────

async def test_resubmitting_a_question_overwrites(client, db):
    instance, q1, q2, q3 = await _setup(db)
    sid, token = await _start(client, instance)
    await client.put(f"{R}/sessions/{sid}", json={"responses": [{"question_id": q1.id, "likert_value": 3}]}, headers=_hdr(token))
    await client.put(f"{R}/sessions/{sid}", json={"responses": [{"question_id": q1.id, "likert_value": 5}]}, headers=_hdr(token))
    count = (await db.execute(
        select(func.count(Response.id)).where(Response.session_id == sid, Response.question_id == q1.id)
    )).scalar_one()
    assert count == 1
    row = (await db.execute(select(Response).where(Response.session_id == sid, Response.question_id == q1.id))).scalar_one()
    assert row.likert_value == 5


# ── required-question validation ──────────────────────────────────────────────

async def test_complete_blocked_when_required_unanswered(client, db):
    instance, q1, q2, q3 = await _setup(db)
    sid, token = await _start(client, instance)
    # answer only q1 (q2 required, still missing)
    await client.put(f"{R}/sessions/{sid}", json={"responses": [{"question_id": q1.id, "likert_value": 4}]}, headers=_hdr(token))
    resp = await client.post(f"{R}/sessions/{sid}/complete", headers=_hdr(token))
    assert resp.status_code == 400


async def test_complete_succeeds_with_required_answered_open_ended_optional(client, db):
    instance, q1, q2, q3 = await _setup(db)
    sid, token = await _start(client, instance)
    await client.put(f"{R}/sessions/{sid}", json={"responses": [
        {"question_id": q1.id, "likert_value": 4},
        {"question_id": q2.id, "selected_option_id": None, "likert_value": 2},
    ]}, headers=_hdr(token))
    # q3 (open_ended) intentionally unanswered
    resp = await client.post(f"{R}/sessions/{sid}/complete", headers=_hdr(token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "complete"


# ── bot / fast-completion flag ────────────────────────────────────────────────

async def test_fast_completion_is_flagged(client, db):
    instance, q1, q2, q3 = await _setup(db)
    sid, token = await _start(client, instance)
    await client.put(f"{R}/sessions/{sid}", json={"responses": [
        {"question_id": q1.id, "likert_value": 4},
        {"question_id": q2.id, "likert_value": 2},
    ]}, headers=_hdr(token))
    resp = await client.post(f"{R}/sessions/{sid}/complete", headers=_hdr(token))
    assert resp.json()["flagged_fast"] is True  # completed in well under 2 minutes


async def test_realistic_pace_not_flagged(client, db):
    instance, q1, q2, q3 = await _setup(db)
    sid, token = await _start(client, instance)
    # backdate the start so elapsed exceeds the threshold
    session = (await db.execute(select(RespondentSession).where(RespondentSession.id == sid))).scalar_one()
    session.started_at = datetime.now(timezone.utc) - timedelta(minutes=4)
    await db.commit()
    await client.put(f"{R}/sessions/{sid}", json={"responses": [
        {"question_id": q1.id, "likert_value": 4},
        {"question_id": q2.id, "likert_value": 2},
    ]}, headers=_hdr(token))
    resp = await client.post(f"{R}/sessions/{sid}/complete", headers=_hdr(token))
    assert resp.json()["flagged_fast"] is False


# ── no writes after completion / on closed surveys ────────────────────────────

async def test_cannot_submit_after_completion(client, db):
    instance, q1, q2, q3 = await _setup(db)
    sid, token = await _start(client, instance)
    await client.put(f"{R}/sessions/{sid}", json={"responses": [
        {"question_id": q1.id, "likert_value": 4}, {"question_id": q2.id, "likert_value": 2},
    ]}, headers=_hdr(token))
    assert (await client.post(f"{R}/sessions/{sid}/complete", headers=_hdr(token))).status_code == 200
    late = await client.put(f"{R}/sessions/{sid}", json={"responses": [{"question_id": q1.id, "likert_value": 1}]}, headers=_hdr(token))
    assert late.status_code == 409


async def test_complete_is_idempotent(client, db):
    instance, q1, q2, q3 = await _setup(db)
    sid, token = await _start(client, instance)
    await client.put(f"{R}/sessions/{sid}", json={"responses": [
        {"question_id": q1.id, "likert_value": 4}, {"question_id": q2.id, "likert_value": 2},
    ]}, headers=_hdr(token))
    assert (await client.post(f"{R}/sessions/{sid}/complete", headers=_hdr(token))).status_code == 200
    assert (await client.post(f"{R}/sessions/{sid}/complete", headers=_hdr(token))).status_code == 200


async def test_cannot_submit_to_closed_survey(client, db):
    instance, q1, q2, q3 = await _setup(db)
    sid, token = await _start(client, instance)
    # close the survey after the session started
    instance_row = (await db.execute(select(SurveyInstance).where(SurveyInstance.id == instance.id))).scalar_one()
    instance_row.status = "closed"
    await db.commit()
    resp = await client.put(f"{R}/sessions/{sid}", json={"responses": [{"question_id": q1.id, "likert_value": 4}]}, headers=_hdr(token))
    assert resp.status_code == 409
