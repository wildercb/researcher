"""Tests for seed scout agent."""

import pytest

from packages.agents.seed_scout import scout_seeds
from packages.core.models import Item, Seed


@pytest.mark.asyncio
async def test_scout_finds_frequent_author(storage):
    async with storage.session() as session:
        for i in range(8):
            session.add(Item(
                source="test", source_id=f"scout-{i}", kind="paper",
                title=f"Paper {i}", url="https://example.com", raw={},
                authors=["Frequent Author"], relevance_score=0.8,
            ))

    async with storage.session() as session:
        proposals = await scout_seeds(session, min_items=5, min_relevance=0.6)
        author_proposals = [p for p in proposals if p.seed_type == "author"]
        assert any(p.identifier == "Frequent Author" for p in author_proposals)


@pytest.mark.asyncio
async def test_scout_ignores_existing_seeds(storage):
    async with storage.session() as session:
        session.add(Seed(
            seed_type="author", identifier="Already Seeded",
            label="Already Seeded", weight=1.0,
        ))
        for i in range(8):
            session.add(Item(
                source="test", source_id=f"scout-existing-{i}", kind="paper",
                title=f"Paper {i}", url="https://example.com", raw={},
                authors=["Already Seeded"], relevance_score=0.9,
            ))

    async with storage.session() as session:
        proposals = await scout_seeds(session, min_items=5)
        assert not any(p.identifier == "Already Seeded" for p in proposals)


@pytest.mark.asyncio
async def test_scout_empty_corpus(storage):
    async with storage.session() as session:
        proposals = await scout_seeds(session)
        assert proposals == []
