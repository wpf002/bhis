"""
API tests for the church invite system + invite-based registration.
Requires a Postgres test DB (see conftest.py).
"""
import pytest
from sqlalchemy import select

from app.config import settings
from app.core.security import create_access_token, hash_password
from app.models import Church, User, ChurchInvite
from app.services.email import clear_outbox

pytestmark = pytest.mark.asyncio

CH = "/api/v1/churches"
A = "/api/v1/auth"


@pytest.fixture(autouse=True)
def _console_email():
    settings.EMAIL_BACKEND = "console"
    clear_outbox()
    yield
    clear_outbox()


async def _church(db, name="Invite Test Church"):
    church = Church(name=name)
    db.add(church)
    await db.commit()
    await db.refresh(church)
    return church


async def _admin(db, church_id):
    admin = User(email=f"admin-{church_id[:8]}@test.org", password_hash=hash_password("x"),
                 role="admin", church_id=church_id, is_active=True)
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


def _auth(user):
    return {"Authorization": f"Bearer {create_access_token({'sub': user.id})}"}


# ── creating invites ──────────────────────────────────────────────────────────

async def test_admin_creates_invite_for_own_church(client, db):
    church = await _church(db)
    admin = await _admin(db, church.id)
    resp = await client.post(f"{CH}/{church.id}/invites", json={"role": "leader"}, headers=_auth(admin))
    assert resp.status_code == 201
    body = resp.json()
    assert body["token"]
    assert body["join_url"].endswith(body["token"])
    assert body["role"] == "leader"
    # only the hash is stored
    row = (await db.execute(select(ChurchInvite))).scalar_one()
    assert row.token_hash != body["token"]


async def test_admin_cannot_invite_into_another_church(client, db):
    church_a = await _church(db, "A")
    church_b = await _church(db, "B")
    admin_a = await _admin(db, church_a.id)
    resp = await client.post(f"{CH}/{church_b.id}/invites", json={"role": "leader"}, headers=_auth(admin_a))
    assert resp.status_code == 403


async def test_respondent_cannot_create_invite(client, db):
    church = await _church(db)
    member = User(email="m@test.org", password_hash=hash_password("x"),
                  role="respondent", church_id=church.id, is_active=True)
    db.add(member)
    await db.commit()
    await db.refresh(member)
    resp = await client.post(f"{CH}/{church.id}/invites", json={"role": "leader"}, headers=_auth(member))
    assert resp.status_code == 403


async def test_create_invite_requires_auth(client, db):
    church = await _church(db)
    resp = await client.post(f"{CH}/{church.id}/invites", json={"role": "leader"})
    assert resp.status_code in (401, 403)


# ── registering via invite ────────────────────────────────────────────────────

async def _make_invite(client, db, role="leader", email=None):
    church = await _church(db)
    admin = await _admin(db, church.id)
    body = {"role": role}
    if email:
        body["email"] = email
    resp = await client.post(f"{CH}/{church.id}/invites", json=body, headers=_auth(admin))
    return church, resp.json()["token"]


async def test_register_via_invite_assigns_church_and_role(client, db):
    church, token = await _make_invite(client, db, role="leader")
    resp = await client.post(f"{A}/register-via-invite", json={
        "token": token, "password": "secret12", "first_name": "New", "last_name": "Leader",
        "email": "new.leader@test.org",
    })
    assert resp.status_code == 201
    assert resp.json()["role"] == "leader"
    user = (await db.execute(select(User).where(User.email == "new.leader@test.org"))).scalar_one()
    assert user.church_id == church.id
    assert user.role == "leader"


async def test_invite_is_single_use(client, db):
    church, token = await _make_invite(client, db)
    first = await client.post(f"{A}/register-via-invite", json={
        "token": token, "password": "secret12", "first_name": "A", "last_name": "B",
        "email": "first@test.org",
    })
    assert first.status_code == 201
    second = await client.post(f"{A}/register-via-invite", json={
        "token": token, "password": "secret12", "first_name": "C", "last_name": "D",
        "email": "second@test.org",
    })
    assert second.status_code == 400


async def test_register_via_invite_rejects_garbage(client, db):
    resp = await client.post(f"{A}/register-via-invite", json={
        "token": "nope", "password": "secret12", "first_name": "A", "last_name": "B",
        "email": "x@test.org",
    })
    assert resp.status_code == 400


async def test_pinned_email_invite_uses_invite_email(client, db):
    church, token = await _make_invite(client, db, email="pinned@test.org")
    # payload omits email entirely; the invite's email is used
    resp = await client.post(f"{A}/register-via-invite", json={
        "token": token, "password": "secret12", "first_name": "P", "last_name": "Q",
    })
    assert resp.status_code == 201
    user = (await db.execute(select(User).where(User.email == "pinned@test.org"))).scalar_one()
    assert user.church_id == church.id
