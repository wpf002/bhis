"""
Async API test harness for BHIS.

Spins up a throwaway Postgres-backed app per test with the schema created from
the models, and overrides the get_db dependency. Requires a Postgres reachable
at TEST_DATABASE_URL (default: the local test container on :5433).

The engine is created *inside* a function-scoped fixture (NullPool) so all
create/use/dispose happens on a single event loop — avoiding the classic
async-SQLAlchemy "attached to a different loop" pitfall.
"""
import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from app.main import app
from app.database import Base, get_db
from app.core.ratelimit import reset_all as reset_rate_limits


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    # The limiter is process-global and in-memory; clear it so request counts
    # from one test don't trip 429s in the next.
    reset_rate_limits()
    yield
    reset_rate_limits()

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://bhis:bhis_dev@localhost:5433/bhis_test",
)


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def sessionmaker_(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db(sessionmaker_):
    async with sessionmaker_() as session:
        yield session


@pytest_asyncio.fixture
async def client(sessionmaker_):
    import app.database as dbmod

    async def override_get_db():
        async with sessionmaker_() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    # Background tasks open their own session via app.database.AsyncSessionLocal;
    # point it at the test engine so auto-scoring runs against the test DB.
    original_sessionmaker = dbmod.AsyncSessionLocal
    dbmod.AsyncSessionLocal = sessionmaker_

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    dbmod.AsyncSessionLocal = original_sessionmaker
    app.dependency_overrides.clear()
