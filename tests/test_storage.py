import pytest
from sqlalchemy import select

from packages.core.config import Settings
from packages.core.models import Item, Seed
from packages.core.storage import PostgresStorage, SQLiteStorage, create_storage


@pytest.mark.asyncio
async def test_sqlite_storage_init(storage):
    assert isinstance(storage, SQLiteStorage)
    assert storage.engine is not None


@pytest.mark.asyncio
async def test_create_and_read_item(storage):
    async with storage.session() as session:
        item = Item(
            source="test",
            source_id="test-001",
            kind="paper",
            title="Test Paper",
            abstract="A test abstract",
            authors=["Author One", "Author Two"],
            url="https://example.com/paper",
            raw={"key": "value"},
        )
        session.add(item)

    async with storage.session() as session:
        result = await session.execute(select(Item).where(Item.source_id == "test-001"))
        found = result.scalar_one()
        assert found.title == "Test Paper"
        assert found.source == "test"
        assert found.kind == "paper"


@pytest.mark.asyncio
async def test_create_seed(storage):
    async with storage.session() as session:
        seed = Seed(
            seed_type="paper",
            identifier="10.1234/test",
            label="Test Paper Seed",
            weight=1.0,
        )
        session.add(seed)

    async with storage.session() as session:
        result = await session.execute(select(Seed).where(Seed.identifier == "10.1234/test"))
        found = result.scalar_one()
        assert found.seed_type == "paper"
        assert found.label == "Test Paper Seed"


@pytest.mark.asyncio
async def test_session_rollback_on_error(storage):
    try:
        async with storage.session() as session:
            item = Item(
                source="test",
                source_id="rollback-test",
                kind="paper",
                title="Will Rollback",
                url="https://example.com",
                raw={},
            )
            session.add(item)
            raise ValueError("Force rollback")
    except ValueError:
        pass

    async with storage.session() as session:
        result = await session.execute(
            select(Item).where(Item.source_id == "rollback-test")
        )
        assert result.scalar_one_or_none() is None


def test_create_storage_laptop(settings):
    storage = create_storage(settings)
    assert isinstance(storage, SQLiteStorage)


def test_create_storage_vps(tmp_path):
    settings = Settings(
        mode="vps",
        database_url="postgresql+asyncpg://test:test@localhost/test",
        data_dir=tmp_path,
    )
    storage = create_storage(settings)
    assert isinstance(storage, PostgresStorage)
