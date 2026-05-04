import asyncio
from pathlib import Path

import pytest
import pytest_asyncio

from packages.core.config import Settings
from packages.core.models import Base
from packages.core.storage import SQLiteStorage


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def settings(tmp_dir):
    return Settings(
        mode="laptop",
        data_dir=tmp_dir,
        database_url=f"sqlite+aiosqlite:///{tmp_dir}/test.db",
        config_dir=Path("config"),
    )


@pytest_asyncio.fixture
async def storage(settings):
    s = SQLiteStorage(settings)
    await s.init()
    async with s.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield s
    await s.close()


@pytest_asyncio.fixture
async def session(storage):
    async with storage.session() as sess:
        yield sess
