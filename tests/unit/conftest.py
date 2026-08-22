"""Unit test fixtures — gecici SQLite + TestClient (sunucu/playwright gerektirmez)."""
import os
import sys

# KRITIK: backend.main en basinda import edilmeli — boylece tum ORM modelleri
# Base.metadata'ya kayitli olur ve create_all bos metadata ile calismaz.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import backend.main  # noqa: F401  (modelleri Base.metadata'ya kaydeder)
from backend.database import Base, get_db


@pytest_asyncio.fixture
async def db_engine(tmp_path):
    """Her test icin izole gecici SQLite engine."""
    db_path = tmp_path / "kw_unit.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_sessionmaker(db_engine):
    return async_sessionmaker(db_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def client(db_engine, db_sessionmaker):
    """backend.main app + override edilmis DB dependency."""
    from backend.main import app

    async def override_get_db():
        async with db_sessionmaker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
