"""FastAPI dependency injection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from packages.core.config import get_settings
from packages.core.scheduler import APSchedulerBackend, PrefectBackend, create_scheduler
from packages.core.storage import PostgresStorage, SQLiteStorage, create_storage

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncSession

_storage: SQLiteStorage | PostgresStorage | None = None
_scheduler: APSchedulerBackend | PrefectBackend | None = None


def get_storage_instance() -> SQLiteStorage | PostgresStorage:
    global _storage
    if _storage is None:
        _storage = create_storage(get_settings())
    return _storage


def get_scheduler_instance() -> APSchedulerBackend | PrefectBackend:
    global _scheduler
    if _scheduler is None:
        _scheduler = create_scheduler(get_settings())
    return _scheduler


async def get_session() -> AsyncIterator[AsyncSession]:
    storage = get_storage_instance()
    async with storage.session() as session:
        yield session
