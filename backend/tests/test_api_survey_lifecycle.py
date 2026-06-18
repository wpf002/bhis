"""
API tests for survey instance lifecycle, metadata, auto-close, and option
randomization. Requires a Postgres test DB (see conftest.py).
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.core.security import create_access_token, hash_password
from app.models import (
    Church, User, SurveyTemplate, SurveyInstance, Question, QuestionOption,
    QuestionCondition,
)

pytestmark = pytest.mark.asyncio

S = "/api/v1/surveys"


async def _setup(db, status="draft", close_date=None):
    church = Church(name="Lifecycle Church")
    template = SurveyTemplate(name="Full", version="1.0", question_count=2, estimated_minutes=11)
    db.add_all([church, template])
    await db.flush()
    admin = User(email=f"a-{church.id[:8]}@t.org", password_hash=hash_password("x"),
                 role="admin", church_id=church.id, is_active=True)
    instance = SurveyInstance(church_id=church.id, template_id=template.id,
                              assessment_cycle="Q1-2026", status=status, close_date=close_date)
    db.add_all([admin, instance])
    await db.commit()
    await db.refresh(admin)
    await db.refresh(instance)
    return church, admin, template, instance


def _auth(user):
    return {"Authorization": f"Bearer {create_access_token({'sub': user.id})}"}


# ── transitions ───────────────────────────────────────────────────────────────

async def test_launch_then_close(client, db):
    church, admin, template, instance = await _setup(db)
    launched = await client.post(f"{S}/instances/{instance.id}/launch", headers=_auth(admin))
    assert launched.status_code == 200 and launched.json()["status"] == "active"
    closed = await client.post(f"{S}/instances/{instance.id}/close", headers=_auth(admin))
    assert closed.status_code == 200 and closed.json()["status"] == "closed"


async def test_cannot_launch_non_draft(client, db):
    church, admin, template, instance = await _setup(db, status="active")
    resp = await client.post(f"{S}/instances/{instance.id}/launch", headers=_auth(admin))
    assert resp.status_code == 400


async def test_cannot_close_a_draft(client, db):
    church, admin, template, instance = await _setup(db, status="draft")
    resp = await client.post(f"{S}/instances/{instance.id}/close", headers=_auth(admin))
    assert resp.status_code == 400


async def test_cannot_manage_another_churchs_survey(client, db):
    church, admin, template, instance = await _setup(db)
    other = User(email="other@t.org", password_hash=hash_password("x"),
                 role="admin", church_id=None, is_active=True)
    db.add(other)
    await db.commit()
    await db.refresh(other)
    resp = await client.post(f"{S}/instances/{instance.id}/launch", headers=_auth(other))
    assert resp.status_code == 403


# ── auto-close ────────────────────────────────────────────────────────────────

async def test_questions_autoclose_past_close_date(client, db):
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    church, admin, template, instance = await _setup(db, status="active", close_date=past)
    resp = await client.get(f"{S}/instances/{instance.id}/questions")
    assert resp.status_code == 404  # auto-closed, no longer active
    await db.refresh(instance)
    assert instance.status == "closed"


# ── metadata ──────────────────────────────────────────────────────────────────

async def test_instance_metadata(client, db):
    church, admin, template, instance = await _setup(db, status="active")
    resp = await client.get(f"{S}/instances/{instance.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["estimated_minutes"] == 11
    assert body["question_count"] == 0  # no questions seeded for this template
    assert body["status"] == "active"


# ── option randomization ──────────────────────────────────────────────────────

async def test_mc_options_preserved_when_shuffled(client, db):
    church, admin, template, instance = await _setup(db, status="active")
    q = Question(template_id=template.id, question_number=1, pillar="discipleship_depth",
                 question_text="Pick", question_type="mc")
    db.add(q)
    await db.flush()
    letters = ["a", "b", "c", "d"]
    for i, letter in enumerate(letters):
        db.add(QuestionOption(question_id=q.id, option_letter=letter,
                              option_text=f"opt-{letter}", score_value=i * 10))
    await db.commit()

    resp = await client.get(f"{S}/instances/{instance.id}/questions")
    assert resp.status_code == 200
    options = resp.json()[0]["options"]
    # shuffling must preserve the full option set (no loss/dupe)
    assert sorted(o["option_letter"] for o in options) == letters


async def test_question_conditions_table_exists():
    cols = set(QuestionCondition.__table__.columns.keys())
    assert {"question_id", "depends_on_question_id", "operator", "action"} <= cols
