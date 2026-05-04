"""Tests for the enrich stage."""

import pytest

from packages.core.models import Item
from packages.pipeline.enrich import content_hash, enrich_item


@pytest.mark.asyncio
async def test_enrich_with_interest_profile(storage):
    """Enrichment sets relevance score from interest profile."""
    profile = {
        "tag_affinities": {"ML": 1.0, "NLP": 0.8},
        "author_affinities": {"Alice": 1.0},
        "venue_affinities": {"NeurIPS": 1.0},
        "relevance_weights": {
            "tag_overlap": 0.2,
            "author_affinity": 0.2,
            "venue_affinity": 0.1,
        },
    }
    async with storage.session() as session:
        item = Item(
            source="test", source_id="enrich-001", kind="paper",
            title="ML Paper", abstract="About machine learning.",
            authors=["Alice"], tags=["ML"], venue="NeurIPS",
            url="https://example.com", raw={},
        )
        session.add(item)
        await session.flush()

        await enrich_item(item, interest_profile=profile)

        assert item.relevance_score is not None
        assert item.relevance_score > 0
        assert item.enrichment_status == "enriched"


@pytest.mark.asyncio
async def test_enrich_without_profile(storage):
    """Enrichment without interest profile still marks as enriched."""
    async with storage.session() as session:
        item = Item(
            source="test", source_id="enrich-002", kind="paper",
            title="No Profile Paper", url="https://example.com", raw={},
        )
        session.add(item)
        await session.flush()

        await enrich_item(item, interest_profile=None)

        assert item.enrichment_status == "enriched"


@pytest.mark.asyncio
async def test_enrich_already_enriched(storage):
    """Already enriched items are skipped."""
    async with storage.session() as session:
        item = Item(
            source="test", source_id="enrich-003", kind="paper",
            title="Already Done", url="https://example.com", raw={},
            enrichment_status="enriched",
            summary="Existing summary.",
        )
        session.add(item)
        await session.flush()

        await enrich_item(item, interest_profile=None)

        assert item.summary == "Existing summary."


def test_content_hash():
    h1 = content_hash("Title", "Abstract")
    h2 = content_hash("Title", "Abstract")
    h3 = content_hash("Different", "Abstract")
    assert h1 == h2
    assert h1 != h3
