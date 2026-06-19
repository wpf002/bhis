"""
Guards against the bug class the model-based harness (create_all) cannot see:
model/migration drift and column-width-vs-data mismatches. These run the REAL
Alembic migrations and the REAL seed against a throwaway database.

They would have caught both production bugs from commit f6a3cfb:
  - column/table parity flags the UUID-vs-String id type drift
  - seeding all 60 questions exercises the longest values (the question_type
    String(20) overflow on 'forced_prioritization')

We assert parity on COLUMNS and TABLES (type/width/nullability/presence) — the
drift that actually breaks at runtime. Index/constraint-naming differences are
tolerated: migration 0001 adds some useful indexes the models don't declare, and
that cosmetic drift isn't worth rewriting migration history over.

Requires the test Postgres (see conftest.py).
"""
import os
import subprocess
import sys

import asyncpg
import pytest
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.database import Base
from app.models import models  # noqa: F401 — register all models on Base.metadata
from tests.conftest import TEST_DATABASE_URL

pytestmark = pytest.mark.asyncio

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARITY_DB = "bhis_parity"

_BASE = TEST_DATABASE_URL.rsplit("/", 1)[0]                       # ...@host:port
_MAINT_DB = TEST_DATABASE_URL.rsplit("/", 1)[1]
_ADMIN_DSN = _BASE.replace("+asyncpg", "") + "/" + _MAINT_DB      # plain DSN, maintenance db
_PARITY_URL = f"{_BASE}/{PARITY_DB}"                              # +asyncpg, for alembic/seed
_PARITY_DSN = _BASE.replace("+asyncpg", "") + f"/{PARITY_DB}"     # plain DSN, parity db

# compare_metadata ops that represent runtime-dangerous drift.
_DANGEROUS_OPS = {
    "add_table", "remove_table",
    "add_column", "remove_column",
    "modify_type", "modify_nullable",
}


async def _recreate_parity_db():
    conn = await asyncpg.connect(_ADMIN_DSN)
    try:
        await conn.execute(f'DROP DATABASE IF EXISTS "{PARITY_DB}" WITH (FORCE)')
        await conn.execute(f'CREATE DATABASE "{PARITY_DB}"')
    finally:
        await conn.close()


def _alembic_upgrade_head():
    return subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR, env={**os.environ, "DATABASE_URL": _PARITY_URL},
        capture_output=True, text=True,
    )


def _flatten(diffs):
    """compare_metadata returns tuples and (for table-level changes) lists of
    tuples; flatten one level so we can inspect op names."""
    for d in diffs:
        if isinstance(d, list):
            yield from d
        else:
            yield d


@pytest.fixture
async def parity_engine():
    try:
        await _recreate_parity_db()
    except Exception as exc:  # pragma: no cover - infra not available
        pytest.skip(f"parity DB unavailable: {exc}")
    up = _alembic_upgrade_head()
    assert up.returncode == 0, "alembic upgrade head failed:\n" + up.stdout + up.stderr
    engine = create_async_engine(_PARITY_URL, poolclass=NullPool)
    yield engine
    await engine.dispose()


async def test_no_column_or_table_drift(parity_engine):
    async with parity_engine.connect() as conn:
        diffs = await conn.run_sync(
            lambda sync_conn: compare_metadata(
                MigrationContext.configure(sync_conn), Base.metadata
            )
        )
    dangerous = [d for d in _flatten(diffs) if d and d[0] in _DANGEROUS_OPS]
    assert not dangerous, "Models and migrations disagree on columns/tables:\n" + "\n".join(map(str, dangerous))


async def test_full_seed_loads_60_questions(parity_engine):
    seed = subprocess.run(
        [sys.executable, "seeds/seed_questions.py"],
        cwd=BACKEND_DIR, env={**os.environ, "DATABASE_URL": _PARITY_URL},
        capture_output=True, text=True,
    )
    assert seed.returncode == 0, seed.stdout + seed.stderr
    conn = await asyncpg.connect(_PARITY_DSN)
    try:
        assert await conn.fetchval("SELECT count(*) FROM questions") == 60
    finally:
        await conn.close()
