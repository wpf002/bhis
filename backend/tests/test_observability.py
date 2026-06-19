"""
Tests for health, request timing headers, and the consistent error shape.
Requires a Postgres test DB (see conftest.py).
"""
import pytest

pytestmark = pytest.mark.asyncio


async def test_health_reports_db_and_uptime(client, db):
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["db"] is True
    assert "uptime_seconds" in body


async def test_responses_carry_timing_headers(client, db):
    resp = await client.get("/health")
    assert "x-request-id" in resp.headers
    assert "x-process-time-ms" in resp.headers


async def test_http_error_has_detail_and_code(client, db):
    resp = await client.get("/api/v1/reports/individual/by-token/does-not-exist/export")
    assert resp.status_code == 404
    body = resp.json()
    assert body["detail"]
    assert body["code"] == "not_found"


async def test_validation_error_shape(client, db):
    # missing required register fields → 422 with normalized shape
    resp = await client.post("/api/v1/auth/register", json={"email": "not-an-email"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "validation_error"
    assert "field" in body
    assert "errors" in body
