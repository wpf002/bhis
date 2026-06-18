"""
API tests for the report-delivery (email) send path.

Confirms a member can have their own report link emailed via the capability
token, that the delivery row is severed from church/user identity, and that the
console backend captures the message (nothing actually sends).

Requires a Postgres test DB (see conftest.py).
"""
import pytest
from sqlalchemy import select

from app.config import settings
from app.models import Church, SurveyTemplate, SurveyInstance, RespondentSession, ReportDelivery
from app.services.email import outbox, clear_outbox

pytestmark = pytest.mark.asyncio

REP = "/api/v1/reports"


@pytest.fixture(autouse=True)
def _console_email():
    settings.EMAIL_BACKEND = "console"
    clear_outbox()
    yield
    clear_outbox()


async def _session_with_token(db, token="cap-deliver-xyz"):
    church = Church(name="Deliver Test Church")
    template = SurveyTemplate(name="Full Diagnostic", version="1.0")
    db.add_all([church, template])
    await db.flush()
    instance = SurveyInstance(church_id=church.id, template_id=template.id, status="active")
    db.add(instance)
    await db.flush()
    session = RespondentSession(survey_instance_id=instance.id, anonymous_token=token)
    db.add(session)
    await db.commit()
    return token


async def test_deliver_sends_and_records_severed_row(client, db):
    token = await _session_with_token(db)
    resp = await client.post(f"{REP}/deliver", json={"session_token": token, "email": "me@home.org"})
    assert resp.status_code == 201
    assert resp.json()["status"] == "sent"

    # Email captured by the console backend (nothing left the machine).
    assert len(outbox) == 1
    assert outbox[0].to == "me@home.org"
    assert token in outbox[0].html  # report link carries the capability token

    # Delivery row exists, severed from identity.
    row = (await db.execute(select(ReportDelivery))).scalar_one()
    assert row.session_token == token
    assert row.email == "me@home.org"
    assert row.sent_at is not None
    cols = set(ReportDelivery.__table__.columns.keys())
    assert "church_id" not in cols
    assert "user_id" not in cols


async def test_deliver_unknown_token_404(client, db):
    resp = await client.post(f"{REP}/deliver", json={"session_token": "nope", "email": "me@home.org"})
    assert resp.status_code == 404
    assert outbox == []


async def test_deliver_rejects_bad_email(client, db):
    token = await _session_with_token(db)
    resp = await client.post(f"{REP}/deliver", json={"session_token": token, "email": "not-an-email"})
    assert resp.status_code == 422  # pydantic EmailStr validation
    assert outbox == []
