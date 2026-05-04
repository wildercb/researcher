"""Tests for deduplication logic."""

import pytest
from sqlalchemy import select

from packages.core.models import Item, Mention
from packages.pipeline.dedupe import _title_hash, dedupe_item
from packages.sources.base import NormalizedItem


def _make_normalized(**kwargs):
    defaults = {
        "source": "test",
        "source_id": "test-001",
        "kind": "paper",
        "title": "Test Paper",
        "url": "https://example.com",
    }
    defaults.update(kwargs)
    return NormalizedItem(**defaults)


@pytest.mark.asyncio
async def test_new_item_no_match(storage):
    async with storage.session() as session:
        item = _make_normalized()
        existing, is_new = await dedupe_item(item, session)
        assert is_new is True
        assert existing is None


@pytest.mark.asyncio
async def test_doi_match(storage):
    # Insert an existing item with DOI
    async with storage.session() as session:
        session.add(Item(
            source="arxiv", source_id="orig-001", kind="paper",
            title="Original", url="https://example.com", doi="10.1234/test",
            raw={},
        ))

    # Try to dedupe a new item with same DOI
    async with storage.session() as session:
        item = _make_normalized(doi="10.1234/test", source_id="new-001")
        existing, is_new = await dedupe_item(item, session)
        assert is_new is False
        assert existing is not None
        assert existing.doi == "10.1234/test"


@pytest.mark.asyncio
async def test_arxiv_match(storage):
    async with storage.session() as session:
        session.add(Item(
            source="arxiv", source_id="orig-002", kind="preprint",
            title="ArXiv Paper", url="https://arxiv.org", arxiv_id="2401.12345",
            raw={},
        ))

    async with storage.session() as session:
        item = _make_normalized(arxiv_id="2401.12345", source_id="new-002")
        existing, is_new = await dedupe_item(item, session)
        assert is_new is False
        assert existing.arxiv_id == "2401.12345"


@pytest.mark.asyncio
async def test_source_id_match(storage):
    async with storage.session() as session:
        session.add(Item(
            source="test", source_id="same-id", kind="paper",
            title="Same Source", url="https://example.com", raw={},
        ))

    async with storage.session() as session:
        item = _make_normalized(source="test", source_id="same-id")
        existing, is_new = await dedupe_item(item, session)
        assert is_new is False


@pytest.mark.asyncio
async def test_mention_created_on_match(storage):
    async with storage.session() as session:
        session.add(Item(
            source="arxiv", source_id="orig-003", kind="paper",
            title="Mentioned Paper", url="https://example.com", doi="10.5678/mention",
            raw={},
        ))

    async with storage.session() as session:
        item = _make_normalized(
            source="openalex", source_id="oa-003", doi="10.5678/mention",
            url="https://openalex.org/W123",
        )
        existing, is_new = await dedupe_item(item, session)
        assert is_new is False

    # Verify mention was created
    async with storage.session() as session:
        result = await session.execute(select(Mention))
        mentions = result.scalars().all()
        assert len(mentions) == 1
        assert mentions[0].source == "openalex"


def test_title_hash():
    h1 = _title_hash("Test Paper", ["John Smith"])
    h2 = _title_hash("Test Paper", ["John Smith"])
    h3 = _title_hash("Different Paper", ["John Smith"])
    assert h1 == h2
    assert h1 != h3


def test_title_hash_none():
    assert _title_hash("", []) is None
