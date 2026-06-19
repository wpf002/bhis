"""
End-to-end integration: onboard admin -> create church -> launch survey ->
15 anonymous members complete -> auto-score + auto-aggregate -> church report
shows real data. Plus a protected-route auth sweep.

Requires a Postgres test DB (see conftest.py).
"""
import pytest

from app.config import settings
from app.models import SurveyTemplate, Question
from app.services.email import clear_outbox

pytestmark = pytest.mark.asyncio

A = "/api/v1/auth"
CH = "/api/v1/churches"
S = "/api/v1/surveys"
R = "/api/v1/responses"
REP = "/api/v1/reports"


@pytest.fixture(autouse=True)
def _console_email():
    settings.EMAIL_BACKEND = "console"
    clear_outbox()
    yield
    clear_outbox()


async def test_full_assessment_cycle(client, db):
    # 1. admin onboards
    reg = (await client.post(f"{A}/register", json={
        "email": "pastor@e2e.org", "password": "secret12",
        "first_name": "P", "last_name": "Q", "role": "admin",
    })).json()
    hdr = {"Authorization": f"Bearer {reg['access_token']}"}

    # 2. create church (links the admin to it)
    church = (await client.post(f"{CH}", json={"name": "E2E Church"}, headers=hdr)).json()
    assert church["id"]

    # 3. seed a template + two required questions (no template-authoring endpoint yet)
    template = SurveyTemplate(name="Full", version="1.0", estimated_minutes=10)
    db.add(template)
    await db.flush()
    q1 = Question(template_id=template.id, question_number=1, pillar="doctrinal_integrity",
                  question_text="d", question_type="likert")
    q2 = Question(template_id=template.id, question_number=11, pillar="spiritual_discipline",
                  question_text="s", question_type="likert")
    db.add_all([q1, q2])
    await db.commit()
    for o in (template, q1, q2):
        await db.refresh(o)

    # 4. create + launch a survey instance
    inst = (await client.post(f"{S}/instances", json={
        "template_id": template.id, "assessment_cycle": "Q1-2026",
    }, headers=hdr)).json()
    instance_id = inst["id"]
    launched = await client.post(f"{S}/instances/{instance_id}/launch", headers=hdr)
    assert launched.status_code == 200 and launched.json()["status"] == "active"

    # 5. 15 anonymous members complete (≥ N_MIN so the report is not suppressed)
    for _ in range(15):
        start = (await client.post(f"{R}/sessions", json={"survey_instance_id": instance_id})).json()
        sid, token = start["id"], start["anonymous_token"]
        h = {"X-Session-Token": token}
        await client.put(f"{R}/sessions/{sid}", json={"responses": [
            {"question_id": q1.id, "likert_value": 5},
            {"question_id": q2.id, "likert_value": 4},
        ]}, headers=h)
        done = await client.post(f"{R}/sessions/{sid}/complete", headers=h)
        assert done.status_code == 200

    # 6. the church report shows real, unsuppressed data (auto-scored + aggregated)
    rep = await client.get(f"{REP}/church/{instance_id}", headers=hdr)
    assert rep.status_code == 200
    body = rep.json()
    assert body["suppressed"] is False
    assert body["respondent_count"] == 15
    assert body["health_score"] is not None
    assert body["archetype"]


async def test_protected_routes_reject_anonymous(client, db):
    cases = [
        ("post", f"{CH}"),
        ("get", f"{CH}/x/dashboard"),
        ("get", f"{REP}/church/x"),
        ("post", f"{S}/instances"),
        ("get", f"{A}/sessions"),
        ("post", f"{A}/sessions/revoke-all"),
    ]
    for method, path in cases:
        resp = await client.request(method, path, json={} if method == "post" else None)
        assert resp.status_code in (401, 403), f"{method} {path} -> {resp.status_code}"
