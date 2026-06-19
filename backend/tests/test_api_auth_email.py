"""
API tests for email verification + password reset flows.

Tokens are delivered via the console email backend; tests pull the raw token
out of the captured email link (the same way a user clicks it).
Requires a Postgres test DB (see conftest.py).
"""
import re
from urllib.parse import urlparse, parse_qs

import pytest
from sqlalchemy import select

from app.config import settings
from app.core.security import verify_password
from app.models import User, AuthToken
from app.services.email import outbox, clear_outbox

pytestmark = pytest.mark.asyncio

A = "/api/v1/auth"


@pytest.fixture(autouse=True)
def _console_email():
    settings.EMAIL_BACKEND = "console"
    clear_outbox()
    yield
    clear_outbox()


def _token_from_last_email(param="token") -> str:
    assert outbox, "no email captured"
    m = re.search(r'href="([^"]+)"', outbox[-1].html)
    assert m, "no link in email"
    return parse_qs(urlparse(m.group(1)).query)[param][0]


async def _register(client, email="newpastor@test.org"):
    return await client.post(f"{A}/register", json={
        "email": email, "password": "secret12", "first_name": "A", "last_name": "B", "role": "admin",
    })


# ── verification ──────────────────────────────────────────────────────────────

async def test_register_sends_verification_email(client, db):
    resp = await _register(client)
    assert resp.status_code == 201
    assert len(outbox) == 1
    assert "confirm" in outbox[0].subject.lower()
    user = (await db.execute(select(User).where(User.email == "newpastor@test.org"))).scalar_one()
    assert user.email_verified is False


async def test_verify_email_happy_path(client, db):
    await _register(client)
    token = _token_from_last_email()
    resp = await client.post(f"{A}/verify-email", json={"token": token})
    assert resp.status_code == 200
    user = (await db.execute(select(User).where(User.email == "newpastor@test.org"))).scalar_one()
    assert user.email_verified is True


async def test_verify_token_is_single_use(client, db):
    await _register(client)
    token = _token_from_last_email()
    assert (await client.post(f"{A}/verify-email", json={"token": token})).status_code == 200
    # second use rejected
    assert (await client.post(f"{A}/verify-email", json={"token": token})).status_code == 400


async def test_verify_rejects_garbage_token(client, db):
    resp = await client.post(f"{A}/verify-email", json={"token": "not-a-real-token"})
    assert resp.status_code == 400


async def test_resend_verification_is_silent_for_unknown_email(client, db):
    resp = await client.post(f"{A}/resend-verification", json={"email": "nobody@test.org"})
    assert resp.status_code == 200
    assert outbox == []  # no email, no enumeration


# ── password reset ────────────────────────────────────────────────────────────

async def test_forgot_password_silent_for_unknown_email(client, db):
    resp = await client.post(f"{A}/forgot-password", json={"email": "nobody@test.org"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "sent"
    assert outbox == []


async def test_reset_password_happy_path(client, db):
    await _register(client)
    clear_outbox()
    await client.post(f"{A}/forgot-password", json={"email": "newpastor@test.org"})
    token = _token_from_last_email()

    resp = await client.post(f"{A}/reset-password", json={"token": token, "new_password": "brandnew99"})
    assert resp.status_code == 200

    user = (await db.execute(select(User).where(User.email == "newpastor@test.org"))).scalar_one()
    assert verify_password("brandnew99", user.password_hash)
    # old password no longer works
    assert not verify_password("secret12", user.password_hash)


async def test_reset_token_single_use(client, db):
    await _register(client)
    clear_outbox()
    await client.post(f"{A}/forgot-password", json={"email": "newpastor@test.org"})
    token = _token_from_last_email()
    assert (await client.post(f"{A}/reset-password", json={"token": token, "new_password": "x1234567"})).status_code == 200
    assert (await client.post(f"{A}/reset-password", json={"token": token, "new_password": "y1234567"})).status_code == 400


async def test_only_token_hash_is_stored(client, db):
    await _register(client)
    token = _token_from_last_email()
    # The raw token must not be stored anywhere; only its hash.
    rows = (await db.execute(select(AuthToken))).scalars().all()
    assert len(rows) == 1
    assert rows[0].token_hash != token
    assert len(rows[0].token_hash) == 64


async def test_me_returns_current_user(client, db):
    await _register(client, email="me@test.org")
    login = (await client.post(f"{A}/login", json={"email": "me@test.org", "password": "secret12"})).json()
    resp = await client.get(f"{A}/me", headers={"Authorization": f"Bearer {login['access_token']}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "me@test.org"
    assert body["role"] == "admin"
    assert "church_id" in body


async def test_me_requires_auth(client, db):
    assert (await client.get(f"{A}/me")).status_code in (401, 403)
