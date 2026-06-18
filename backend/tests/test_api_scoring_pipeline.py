"""
API/pipeline tests: auto-scoring on completion, scoring idempotency, and
aggregation idempotency. Requires a Postgres test DB (see conftest.py).
"""
import pytest
from sqlalchemy import select, func

from app.models import (
    Church, SurveyTemplate, SurveyInstance, Question, RespondentSession,
    IndividualScore, ChurchAggregateScore,
)
from app.services.scoring_pipeline import score_session, aggregate_church

pytestmark = pytest.mark.asyncio

R = "/api/v1/responses"


async def _setup(db):
    church = Church(name="Scoring Church")
    template = SurveyTemplate(name="Full", version="1.0", estimated_minutes=10)
    db.add_all([church, template])
    await db.flush()
    instance = SurveyInstance(church_id=church.id, template_id=template.id,
                              assessment_cycle="Q1-2026", status="active")
    db.add(instance)
    await db.flush()
    q1 = Question(template_id=template.id, question_number=1, pillar="doctrinal_integrity",
                  question_text="d", question_type="likert")
    q2 = Question(template_id=template.id, question_number=11, pillar="spiritual_discipline",
                  question_text="s", question_type="likert")
    db.add_all([q1, q2])
    await db.commit()
    for o in (church, instance, q1, q2):
        await db.refresh(o)
    return instance, q1, q2


async def _complete_a_session(client, instance, q1, q2):
    start = (await client.post(f"{R}/sessions", json={"survey_instance_id": instance.id})).json()
    sid, token = start["id"], start["anonymous_token"]
    hdr = {"X-Session-Token": token}
    await client.put(f"{R}/sessions/{sid}", json={"responses": [
        {"question_id": q1.id, "likert_value": 5},
        {"question_id": q2.id, "likert_value": 4},
    ]}, headers=hdr)
    resp = await client.post(f"{R}/sessions/{sid}/complete", headers=hdr)
    assert resp.status_code == 200
    return sid


async def test_completion_auto_scores_and_aggregates(client, db):
    instance, q1, q2 = await _setup(db)
    sid = await _complete_a_session(client, instance, q1, q2)

    # background task ran: individual score persisted with a version
    score = (await db.execute(
        select(IndividualScore).where(IndividualScore.session_id == sid)
    )).scalar_one_or_none()
    assert score is not None
    assert score.score_version == "1.0"

    # and the church aggregate was refreshed
    agg = (await db.execute(
        select(ChurchAggregateScore).where(ChurchAggregateScore.survey_instance_id == instance.id)
    )).scalar_one_or_none()
    assert agg is not None
    assert agg.respondent_count == 1


async def test_scoring_is_idempotent(client, db):
    instance, q1, q2 = await _setup(db)
    sid = await _complete_a_session(client, instance, q1, q2)
    # re-score twice more — still exactly one row, no duplicates
    await score_session(sid, db)
    await score_session(sid, db)
    count = (await db.execute(
        select(func.count(IndividualScore.id)).where(IndividualScore.session_id == sid)
    )).scalar_one()
    assert count == 1


async def test_aggregation_is_idempotent(client, db):
    instance, q1, q2 = await _setup(db)
    await _complete_a_session(client, instance, q1, q2)
    await aggregate_church(instance.id, db)
    await aggregate_church(instance.id, db)
    count = (await db.execute(
        select(func.count(ChurchAggregateScore.id))
        .where(ChurchAggregateScore.survey_instance_id == instance.id)
    )).scalar_one()
    assert count == 1
