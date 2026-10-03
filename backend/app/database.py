from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


# Tiny idempotent migrations: `Base.metadata.create_all` creates missing tables
# but never adds columns to existing ones. For dev/demo we accept the simpler
# "ALTER TABLE ... ADD COLUMN" pattern and swallow the duplicate-column error.
# Anything more sophisticated (multiple migrations) should move to Alembic.
_ADDITIVE_COLUMNS: list[tuple[str, str, str]] = [
    # (table, column, ddl-fragment)
    ("users", "password_hash", "VARCHAR(255)"),
]


async def _apply_additive_columns() -> None:
    async with engine.begin() as conn:
        for table, column, ddl in _ADDITIVE_COLUMNS:
            try:
                await conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {ddl}'))
            except Exception:
                # Column already exists (Postgres / SQLite raise different errors).
                pass


async def init_db() -> None:
    # Import models so they're registered with Base.metadata
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _apply_additive_columns()
