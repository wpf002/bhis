"""
API tests for refresh-token rotation, reuse detection, and login rate limiting.
Requires a Postgres test DB (see conftest.py).
"""
import pytest
from sqlalchemy import select

from app.config import settings
from app.models import RefreshToken
from app.services.email import clear_outbox

pytestmark = pytest.mark.asyncio

A = "/api/v1/auth"


@pytest.fixture(autouse=True)
def _console_email():
    settings.EMAIL_BACKEND = "console"
    clear_outbox()
    yield
    clear_outbox()


async def _register(client, email="rot@test.org"):
    r = await client.post(f"{A}/register", json={
        "email": email, "password": "secret12", "first_name": "A", "last_name": "B", "role": "admin",
    })
    return r.json()


# ── rotation ──────────────────────────────────────────────────────────────────

async def test_refresh_rotates_and_returns_new_token(client, db):
    tokens = await _register(client)
    old_refresh = tokens["refresh_token"]
    resp = await client.post(f"{A}/refresh", json={"refresh_token": old_refresh})
    assert resp.status_code == 200
    new_refresh = resp.json()["refresh_token"]
    assert new_refresh != old_refresh


async def test_old_refresh_token_rejected_after_rotation(client, db):
    tokens = await _register(client)
    old_refresh = tokens["refresh_token"]
    await client.post(f"{A}/refresh", json={"refresh_token": old_refresh})  # rotate once
    # the now-rotated token must not work again
    replay = await client.post(f"{A}/refresh", json={"refresh_token": old_refresh})
    assert replay.status_code == 401


async def test_reuse_detection_revokes_whole_family(client, db):
    tokens = await _register(client)
    r1 = tokens["refresh_token"]
    new = (await client.post(f"{A}/refresh", json={"refresh_token": r1})).json()["refresh_token"]
    # replay the old (revoked) token → theft signal → revoke all of the user's tokens
    assert (await client.post(f"{A}/refresh", json={"refresh_token": r1})).status_code == 401
    # even the legitimately-rotated token is now revoked
    assert (await client.post(f"{A}/refresh", json={"refresh_token": new})).status_code == 401
    rows = (await db.execute(select(RefreshToken))).scalars().all()
    assert rows and all(row.revoked for row in rows)


async def test_garbage_refresh_token_rejected(client, db):
    assert (await client.post(f"{A}/refresh", json={"refresh_token": "nonsense"})).status_code == 401


async def test_login_issues_tracked_refresh_token(client, db):
    await _register(client, email="login@test.org")
    resp = await client.post(f"{A}/login", json={"email": "login@test.org", "password": "secret12"})
    assert resp.status_code == 200
    # at least one un-revoked refresh row exists for the user
    rows = (await db.execute(select(RefreshToken))).scalars().all()
    assert any(not row.revoked for row in rows)


# ── rate limiting ─────────────────────────────────────────────────────────────

async def test_login_rate_limited(client, db):
    await _register(client, email="rl@test.org")
    settings.LOGIN_RATE_LIMIT  # documented limit; we just need to exceed it
    statuses = []
    for _ in range(settings.LOGIN_RATE_LIMIT + 2):
        r = await client.post(f"{A}/login", json={"email": "rl@test.org", "password": "secret12"})
        statuses.append(r.status_code)
    assert 429 in statuses
    assert statuses.count(200) <= settings.LOGIN_RATE_LIMIT


async def test_register_rate_limited(client, db):
    statuses = []
    for i in range(settings.REGISTER_RATE_LIMIT + 2):
        r = await client.post(f"{A}/register", json={
            "email": f"reg{i}@test.org", "password": "secret12",
            "first_name": "A", "last_name": "B", "role": "admin",
        })
        statuses.append(r.status_code)
    assert 429 in statuses
