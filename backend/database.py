import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

_DB_DIR = os.path.join(os.path.dirname(__file__), "..", "memory")
os.makedirs(_DB_DIR, exist_ok=True)
DB_PATH = os.path.join(_DB_DIR, "kurowatch.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    from backend import models  # noqa: F401  — register models with Base
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Migration: genres kolonu
        try:
            await conn.execute(text("ALTER TABLE content ADD COLUMN genres TEXT"))
        except Exception:
            pass
        # Migration: episode season kolonu
        try:
            await conn.execute(text("ALTER TABLE episode ADD COLUMN season INTEGER NOT NULL DEFAULT 1"))
        except Exception:
            pass
        # Migration: site.is_dead kolonu
        try:
            await conn.execute(text("ALTER TABLE site ADD COLUMN is_dead INTEGER"))
        except Exception:
            pass
        # Migration: FAZ-4 intro_timestamp tablosu (create_all ile zaten oluşur, sadece safeguard)
        try:
            await conn.execute(text(
                "CREATE TABLE IF NOT EXISTS intro_timestamp "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, content_id INTEGER NOT NULL, "
                "episode_number INTEGER NOT NULL, intro_start FLOAT NOT NULL, "
                "intro_end FLOAT NOT NULL, confidence FLOAT NOT NULL DEFAULT 1.0, "
                "created_at DATETIME NOT NULL)"
            ))
        except Exception:
            pass
        # Migration: FAZ-4 outro_timestamp tablosu
        try:
            await conn.execute(text(
                "CREATE TABLE IF NOT EXISTS outro_timestamp "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, content_id INTEGER NOT NULL, "
                "episode_number INTEGER NOT NULL, outro_start FLOAT NOT NULL, "
                "outro_end FLOAT NOT NULL, confidence FLOAT NOT NULL DEFAULT 0.85, "
                "created_at DATETIME NOT NULL)"
            ))
        except Exception:
            pass
