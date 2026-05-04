"""Tests for living taxonomy."""

import pytest
from sqlalchemy import select

from packages.core.models import Item, Topic
from packages.pipeline.taxonomy import (
    TaxonomyProposal,
    apply_proposal,
    bootstrap_taxonomy,
    classify_item,
    propose_taxonomy_changes,
)


@pytest.mark.asyncio
async def test_bootstrap_taxonomy(storage):
    # Create items with tags
    async with storage.session() as session:
        for i in range(10):
            session.add(Item(
                source="test", source_id=f"tax-{i}", kind="paper",
                title=f"Paper {i}", url="https://example.com", raw={},
                tags=["ML", "NLP"] if i < 7 else ["ML", "CV"],
            ))

    async with storage.session() as session:
        topics = await bootstrap_taxonomy(session, min_cluster_size=5)
        assert len(topics) >= 1
        names = {t.name for t in topics}
        assert "ML" in names  # appears in all 10 items


@pytest.mark.asyncio
async def test_classify_item(storage):
    # Create a topic
    async with storage.session() as session:
        session.add(Topic(name="ML", description="Machine Learning"))

    async with storage.session() as session:
        item = Item(
            source="test", source_id="classify-1", kind="paper",
            title="ML Paper", url="https://example.com", raw={},
            tags=["ML", "deep learning"],
        )
        session.add(item)
        await session.flush()

        assignments = await classify_item(item, session)
        assert len(assignments) == 1
        assert assignments[0].confidence == 1.0


@pytest.mark.asyncio
async def test_propose_new_topic(storage):
    async with storage.session() as session:
        for i in range(15):
            session.add(Item(
                source="test", source_id=f"prop-{i}", kind="paper",
                title=f"Paper {i}", url="https://example.com", raw={},
                tags=["emerging_topic"],
            ))

    async with storage.session() as session:
        proposals = await propose_taxonomy_changes(session, min_items_for_new=10)
        new_proposals = [p for p in proposals if p.action == "new"]
        assert any(p.topic_name == "emerging_topic" for p in new_proposals)


@pytest.mark.asyncio
async def test_apply_proposal(storage):
    proposal = TaxonomyProposal(
        action="new",
        topic_name="New Topic",
        details="Test proposal",
        confidence=0.8,
    )
    async with storage.session() as session:
        topic = await apply_proposal(proposal, session)
        assert topic is not None
        assert topic.name == "New Topic"

    # Verify it was persisted
    async with storage.session() as session:
        result = await session.execute(select(Topic).where(Topic.name == "New Topic"))
        found = result.scalar_one()
        assert found.description == "Proposed: Test proposal"
