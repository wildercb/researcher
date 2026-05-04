"""Tests for the store stage."""


import pytest
from sqlalchemy import select

from packages.core.models import Item
from packages.pipeline.store import store_item
from packages.sources.base import NormalizedItem


@pytest.mark.asyncio
async def test_store_item(storage):
    normalized = NormalizedItem(
        source="test",
        source_id="store-001",
        kind="paper",
        title="Stored Paper",
        abstract="An abstract.",
        authors=["Alice"],
        url="https://example.com/paper",
        doi="10.1234/store",
        tags=["ML"],
    )
    async with storage.session() as session:
        item = await store_item(normalized, session)
        assert item.id is not None
        assert item.title == "Stored Paper"
        assert item.enrichment_status == "pending"

    # Verify in DB
    async with storage.session() as session:
        result = await session.execute(select(Item).where(Item.source_id == "store-001"))
        found = result.scalar_one()
        assert found.doi == "10.1234/store"
        assert found.abstract == "An abstract."


@pytest.mark.asyncio
async def test_store_item_minimal(storage):
    normalized = NormalizedItem(
        source="test",
        source_id="store-002",
        kind="post",
        title="Minimal Item",
        url="https://example.com",
    )
    async with storage.session() as session:
        item = await store_item(normalized, session)
        assert item.id is not None
        assert item.kind == "post"
