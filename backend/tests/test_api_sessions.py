"""
API tests for session management: list, single logout, and revoke-all.
Requires a Postgres test DB (see conftest.py).
"""
import pytest

from app.config import settings
from app.services.email import clear_outbox

pytestmark = pytest.mark.asyncio

A = "/api/v1/auth"


@pytest.fixture(autouse=True)
def _console_email():
    settings.EMAIL_BACKEND = "console"
    clear_outbox()
    yield
    clear_outbox()


async def _register(client, email="sess@test.org"):
    r = await client.post(f"{A}/register", json={
        "email": email, "password": "secret12", "first_name": "A", "last_name": "B", "role": "admin",
    })
    return r.json()


def _bearer(access_token):
    return {"Authorization": f"Bearer {access_token}"}


async def test_list_sessions_shows_active(client, db):
    tok = await _register(client)
    resp = await client.get(f"{A}/sessions", headers=_bearer(tok["access_token"]))
    assert resp.status_code == 200
    sessions = resp.json()
    assert len(sessions) == 1
    assert "id" in sessions[0] and "expires_at" in sessions[0]


async def test_logout_removes_that_session_keeps_others(client, db):
    tok = await _register(client)
    # log in a second time → two active sessions
    login = (await client.post(f"{A}/login", json={"email": "sess@test.org", "password": "secret12"})).json()
    assert len((await client.get(f"{A}/sessions", headers=_bearer(tok["access_token"]))).json()) == 2

    out = await client.post(f"{A}/logout", json={"refresh_token": tok["refresh_token"]})
    assert out.status_code == 200
    # the logged-out session is gone, the other remains
    assert len((await client.get(f"{A}/sessions", headers=_bearer(tok["access_token"]))).json()) == 1
    # the other session still refreshes
    assert (await client.post(f"{A}/refresh", json={"refresh_token": login["refresh_token"]})).status_code == 200


async def test_logged_out_token_cannot_refresh(client, db):
    tok = await _register(client)
    await client.post(f"{A}/logout", json={"refresh_token": tok["refresh_token"]})
    assert (await client.post(f"{A}/refresh", json={"refresh_token": tok["refresh_token"]})).status_code == 401


async def test_logout_is_idempotent_for_garbage(client, db):
    assert (await client.post(f"{A}/logout", json={"refresh_token": "nonsense"})).status_code == 200


async def test_revoke_all_signs_out_everywhere(client, db):
    tok = await _register(client)
    await client.post(f"{A}/login", json={"email": "sess@test.org", "password": "secret12"})
    resp = await client.post(f"{A}/sessions/revoke-all", headers=_bearer(tok["access_token"]))
    assert resp.status_code == 200
    # no active sessions, original refresh dead
    assert (await client.get(f"{A}/sessions", headers=_bearer(tok["access_token"]))).json() == []
    assert (await client.post(f"{A}/refresh", json={"refresh_token": tok["refresh_token"]})).status_code == 401


async def test_sessions_require_auth(client, db):
    assert (await client.get(f"{A}/sessions")).status_code in (401, 403)
    assert (await client.post(f"{A}/sessions/revoke-all")).status_code in (401, 403)
