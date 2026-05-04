from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Protocol

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from packages.core.config import Settings


class Storage(Protocol):
    """Dual-mode storage abstraction. Implementations for SQLite (laptop) and Postgres (VPS)."""

    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]

    async def init(self) -> None: ...
    async def close(self) -> None: ...
    def session(self) -> AsyncIterator[AsyncSession]: ...


class SQLiteStorage:
    """SQLite + sqlite-vec storage for laptop mode."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.engine = create_async_engine(
            settings.effective_database_url,
            echo=settings.debug,
            connect_args={"check_same_thread": False},
            pool_size=1,
            max_overflow=0,
        )
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def init(self) -> None:
        self._settings.data_dir.mkdir(parents=True, exist_ok=True)
        # Enable WAL mode for better concurrent reads during writes
        async with self.engine.begin() as conn:
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA busy_timeout=5000"))

    async def close(self) -> None:
        await self.engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


class PostgresStorage:
    """Postgres + pgvector storage for VPS mode."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.engine = create_async_engine(
            settings.effective_database_url,
            echo=settings.debug,
            pool_size=10,
            max_overflow=20,
        )
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def init(self) -> None:
        pass

    async def close(self) -> None:
        await self.engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


def create_storage(settings: Settings) -> SQLiteStorage | PostgresStorage:
    if settings.is_sqlite:
        return SQLiteStorage(settings)
    return PostgresStorage(settings)
