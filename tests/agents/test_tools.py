"""Tests for agent tools."""

import pytest
from sqlalchemy import select

from packages.agents.tools.feedback import record_feedback
from packages.agents.tools.lookup import read_item
from packages.agents.tools.search import keyword_search, recent_items
from packages.core.models import FeedbackEvent, Item
from packages.core.types import FeedbackSignal


@pytest.mark.asyncio
async def test_keyword_search(storage):
    async with storage.session() as session:
        session.add(Item(
            source="test", source_id="search-001", kind="paper",
            title="Attention Mechanisms in Transformers",
            abstract="A study of attention.", url="https://example.com", raw={},
        ))
        session.add(Item(
            source="test", source_id="search-002", kind="paper",
            title="Convolutional Neural Networks",
            abstract="CNN architectures.", url="https://example.com", raw={},
        ))

    async with storage.session() as session:
        results = await keyword_search("attention", session)
        assert len(results) == 1
        assert "Attention" in results[0].title


@pytest.mark.asyncio
async def test_recent_items(storage):
    async with storage.session() as session:
        for i in range(5):
            session.add(Item(
                source="test", source_id=f"recent-{i}", kind="paper",
                title=f"Paper {i}", url="https://example.com", raw={},
            ))

    async with storage.session() as session:
        results = await recent_items(session, k=3)
        assert len(results) == 3


@pytest.mark.asyncio
async def test_read_item(storage):
    async with storage.session() as session:
        item = Item(
            source="test", source_id="read-001", kind="paper",
            title="Readable Paper", abstract="Full details.",
            url="https://example.com", doi="10.1234/read", raw={},
        )
        session.add(item)
        await session.flush()
        item_id = item.id

    async with storage.session() as session:
        detail = await read_item(item_id, session)
        assert detail is not None
        assert detail.title == "Readable Paper"
        assert detail.doi == "10.1234/read"


@pytest.mark.asyncio
async def test_read_item_not_found(storage):
    async with storage.session() as session:
        detail = await read_item(99999, session)
        assert detail is None


@pytest.mark.asyncio
async def test_record_feedback(storage):
    async with storage.session() as session:
        item = Item(
            source="test", source_id="fb-001", kind="paper",
            title="Feedback Paper", url="https://example.com", raw={},
        )
        session.add(item)
        await session.flush()

        event = await record_feedback(item.id, FeedbackSignal.LIKED, session)
        assert event.signal == "liked"

    async with storage.session() as session:
        result = await session.execute(select(FeedbackEvent))
        events = result.scalars().all()
        assert len(events) == 1
