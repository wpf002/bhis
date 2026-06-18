"""
API-level access-control tests for the anonymity guarantees.

These assert the *security* properties from docs/anonymity-design.md:
  - survey sessions are anonymous (no user_id) and reachable only by capability token
  - a church admin (JWT) has NO path to an individual's responses or report
  - the N_MIN floor suppresses church aggregates below threshold over HTTP
  - the optional account keyring is per-user and does not leak across users

Requires a Postgres test DB (see conftest.py).
"""
import pytest

from app.core.security import create_access_token, hash_password
from app.models import (
    Church, User, SurveyTemplate, SurveyInstance, Question,
    RespondentSession, IndividualScore, ChurchAggregateScore,
)

pytestmark = pytest.mark.asyncio

R = "/api/v1/responses"
REP = "/api/v1/reports"
CH = "/api/v1/churches"


# ── helpers ───────────────────────────────────────────────────────────────────

async def _make_active_survey(db) -> SurveyInstance:
    church = Church(name="Grace Test Church")
    template = SurveyTemplate(name="Full Diagnostic", version="1.0")
    db.add_all([church, template])
    await db.flush()
    instance = SurveyInstance(
        church_id=church.id, template_id=template.id, status="active",
    )
    db.add(instance)
    await db.commit()
    await db.refresh(instance)
    await db.refresh(church)
    return instance


async def _make_admin(db, church_id=None):
    admin = User(
        email="pastor@test.org", password_hash=hash_password("x"),
        role="admin", church_id=church_id, is_active=True,
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


def _auth(user) -> dict:
    return {"Authorization": f"Bearer {create_access_token({'sub': user.id})}"}


# ── anonymous session lifecycle ───────────────────────────────────────────────

async def test_start_session_needs_no_auth_and_returns_capability_token(client, db):
    instance = await _make_active_survey(db)
    resp = await client.post(f"{R}/sessions", json={"survey_instance_id": instance.id})
    assert resp.status_code == 201
    body = resp.json()
    assert body["anonymous_token"]
    assert len(body["anonymous_token"]) >= 32
    # response must not leak any identity field
    assert "user_id" not in body


async def test_session_model_has_no_user_id_column():
    # Structural severance: the column is gone, so nothing can populate it.
    assert "user_id" not in RespondentSession.__table__.columns


async def test_submit_requires_matching_token(client, db):
    instance = await _make_active_survey(db)
    question = Question(
        template_id=instance.template_id, question_number=1,
        pillar="doctrinal_integrity", question_text="Q1", question_type="likert",
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)
    start = (await client.post(f"{R}/sessions", json={"survey_instance_id": instance.id})).json()
    sid, token = start["id"], start["anonymous_token"]
    payload = {"responses": [{"question_id": question.id, "likert_value": 4}]}

    # wrong token → indistinguishable from "doesn't exist"
    bad = await client.put(f"{R}/sessions/{sid}", json=payload, headers={"X-Session-Token": "wrong"})
    assert bad.status_code == 404
    # missing token → unauthorized
    none = await client.put(f"{R}/sessions/{sid}", json=payload)
    assert none.status_code == 401
    # correct token → accepted
    ok = await client.put(f"{R}/sessions/{sid}", json=payload, headers={"X-Session-Token": token})
    assert ok.status_code == 200


async def test_complete_requires_token(client, db):
    instance = await _make_active_survey(db)
    start = (await client.post(f"{R}/sessions", json={"survey_instance_id": instance.id})).json()
    sid, token = start["id"], start["anonymous_token"]
    assert (await client.post(f"{R}/sessions/{sid}/complete")).status_code == 401
    assert (await client.post(f"{R}/sessions/{sid}/complete",
                              headers={"X-Session-Token": token})).status_code == 200


# ── individual report: capability token only, never church-role ───────────────

async def _seed_scored_session(db, instance):
    session = RespondentSession(survey_instance_id=instance.id, anonymous_token="cap-secret-123")
    db.add(session)
    await db.flush()
    db.add(IndividualScore(session_id=session.id, composite_score=68.0, maturity_tier="Grounded"))
    await db.commit()
    return session


async def test_member_reads_own_report_by_token(client, db):
    instance = await _make_active_survey(db)
    await _seed_scored_session(db, instance)
    resp = await client.get(f"{REP}/individual/by-token/cap-secret-123")
    assert resp.status_code == 200
    assert resp.json()["composite_score"] == 68.0


async def test_wrong_token_cannot_read_report(client, db):
    instance = await _make_active_survey(db)
    await _seed_scored_session(db, instance)
    assert (await client.get(f"{REP}/individual/by-token/not-the-token")).status_code == 404


async def test_no_session_id_route_for_individual_report(client, db):
    # The old GET /individual/{session_id} (any-authed-user) leak is GONE.
    instance = await _make_active_survey(db)
    session = await _seed_scored_session(db, instance)
    admin = await _make_admin(db)
    # Even with a valid admin JWT, there is no by-session-id path to an individual.
    resp = await client.get(f"{REP}/individual/{session.id}", headers=_auth(admin))
    assert resp.status_code == 404


async def test_church_admin_cannot_reach_individual_without_token(client, db):
    # An admin who does not hold the capability token cannot read the report,
    # because authority is the token, not the role.
    instance = await _make_active_survey(db)
    await _seed_scored_session(db, instance)
    admin = await _make_admin(db, church_id=instance.church_id)
    # Admin guessing the by-token endpoint without the secret gets nothing.
    resp = await client.get(f"{REP}/individual/by-token/guessed", headers=_auth(admin))
    assert resp.status_code == 404


# ── church aggregate N_MIN floor over HTTP ────────────────────────────────────

async def _seed_aggregate(db, instance, count):
    db.add(ChurchAggregateScore(
        survey_instance_id=instance.id, church_id=instance.church_id,
        health_score=72.0, archetype="Quietly Healthy", respondent_count=count,
        pillar_scores={"doctrinal_integrity": 80.0}, maturity_distribution={"Grounded": count},
    ))
    await db.commit()


async def test_church_report_suppressed_below_floor(client, db):
    instance = await _make_active_survey(db)
    await _seed_aggregate(db, instance, count=9)
    admin = await _make_admin(db, church_id=instance.church_id)
    resp = await client.get(f"{REP}/church/{instance.id}", headers=_auth(admin))
    assert resp.status_code == 200
    body = resp.json()
    assert body["suppressed"] is True
    assert "pillar_scores" not in body
    assert "health_score" not in body


async def test_church_report_visible_at_floor(client, db):
    instance = await _make_active_survey(db)
    await _seed_aggregate(db, instance, count=20)
    admin = await _make_admin(db, church_id=instance.church_id)
    resp = await client.get(f"{REP}/church/{instance.id}", headers=_auth(admin))
    assert resp.status_code == 200
    body = resp.json()
    assert body["suppressed"] is False
    assert body["pillar_scores"]["doctrinal_integrity"] == 80.0


# ── optional account keyring is per-user ──────────────────────────────────────

async def test_keyring_claim_and_isolation(client, db):
    instance = await _make_active_survey(db)
    session = await _seed_scored_session(db, instance)  # token cap-secret-123
    user_a = await _make_admin(db)
    user_b = User(email="b@test.org", password_hash=hash_password("x"), role="respondent", is_active=True)
    db.add(user_b)
    await db.commit()
    await db.refresh(user_b)

    # A claims the token
    claimed = await client.post(f"{REP}/claim", json={"session_token": "cap-secret-123"}, headers=_auth(user_a))
    assert claimed.status_code == 201
    # A sees it; B does not
    mine_a = (await client.get(f"{REP}/mine", headers=_auth(user_a))).json()["reports"]
    mine_b = (await client.get(f"{REP}/mine", headers=_auth(user_b))).json()["reports"]
    assert any(r["session_token"] == "cap-secret-123" for r in mine_a)
    assert mine_b == []


async def test_keyring_rejects_unknown_token(client, db):
    user = await _make_admin(db)
    resp = await client.post(f"{REP}/claim", json={"session_token": "does-not-exist"}, headers=_auth(user))
    assert resp.status_code == 404
