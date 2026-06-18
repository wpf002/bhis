"""
API tests for church settings update + soft-delete.
Requires a Postgres test DB (see conftest.py).
"""
import pytest

from app.core.security import create_access_token, hash_password
from app.models import Church, User

pytestmark = pytest.mark.asyncio

CH = "/api/v1/churches"


async def _church(db, name="Mgmt Test Church"):
    church = Church(name=name)
    db.add(church)
    await db.commit()
    await db.refresh(church)
    return church


async def _user(db, church_id, role="admin"):
    u = User(email=f"{role}-{church_id[:8]}@test.org", password_hash=hash_password("x"),
             role=role, church_id=church_id, is_active=True)
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


def _auth(user):
    return {"Authorization": f"Bearer {create_access_token({'sub': user.id})}"}


# ── settings ──────────────────────────────────────────────────────────────────

async def test_admin_updates_own_church_settings(client, db):
    church = await _church(db)
    admin = await _user(db, church.id)
    resp = await client.put(f"{CH}/{church.id}/settings",
                            json={"denomination": "Baptist", "city": "Dallas"}, headers=_auth(admin))
    assert resp.status_code == 200
    await db.refresh(church)
    assert church.denomination == "Baptist"
    assert church.city == "Dallas"
    assert church.name == "Mgmt Test Church"  # untouched fields preserved


async def test_settings_partial_update_only_sets_provided(client, db):
    church = await _church(db)
    church.denomination = "Reformed"
    await db.commit()
    admin = await _user(db, church.id)
    await client.put(f"{CH}/{church.id}/settings", json={"city": "Austin"}, headers=_auth(admin))
    await db.refresh(church)
    assert church.denomination == "Reformed"  # not overwritten with null
    assert church.city == "Austin"


async def test_admin_cannot_edit_another_church(client, db):
    church_a = await _church(db, "A")
    church_b = await _church(db, "B")
    admin_a = await _user(db, church_a.id)
    resp = await client.put(f"{CH}/{church_b.id}/settings", json={"city": "X"}, headers=_auth(admin_a))
    assert resp.status_code == 403


# ── soft delete ───────────────────────────────────────────────────────────────

async def test_admin_soft_deletes_own_church(client, db):
    church = await _church(db)
    admin = await _user(db, church.id)
    resp = await client.delete(f"{CH}/{church.id}", headers=_auth(admin))
    assert resp.status_code == 200
    # row preserved but deactivated (refresh past the test session's cached copy)
    await db.refresh(church)
    assert church.is_active is False
    # now invisible via GET and dashboard
    assert (await client.get(f"{CH}/{church.id}", headers=_auth(admin))).status_code == 404
    assert (await client.get(f"{CH}/{church.id}/dashboard", headers=_auth(admin))).status_code == 404


async def test_leader_cannot_soft_delete(client, db):
    church = await _church(db)
    leader = await _user(db, church.id, role="leader")
    resp = await client.delete(f"{CH}/{church.id}", headers=_auth(leader))
    assert resp.status_code == 403


async def test_admin_cannot_delete_another_church(client, db):
    church_a = await _church(db, "A")
    church_b = await _church(db, "B")
    admin_a = await _user(db, church_a.id)
    resp = await client.delete(f"{CH}/{church_b.id}", headers=_auth(admin_a))
    assert resp.status_code == 403
