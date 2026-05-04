"""Living taxonomy — dynamic topic clustering and classification.

No fixed taxonomy. Topics are discovered by clustering item embeddings/tags,
labeled by an LLM, and versioned. Daily refresh proposes merges, splits, and
new topics.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.models import Item, ItemTopic, Topic

logger = structlog.get_logger()


@dataclass
class TaxonomyProposal:
    """A proposed taxonomy change."""

    action: str  # "new", "merge", "split", "rename"
    topic_name: str
    details: str
    confidence: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TaxonomyVersion:
    version: int
    topics: list[dict]
    created_at: datetime = field(default_factory=datetime.now)


async def bootstrap_taxonomy(
    session: AsyncSession,
    min_cluster_size: int = 5,
    top_k: int = 50,
) -> list[Topic]:
    """Bootstrap taxonomy from existing item tags.

    Counts tag frequencies, creates topics for the most common ones.
    This is the simple boring-first approach — HDBSCAN clustering
    comes later when embeddings are populated.
    """
    result = await session.execute(select(Item))
    items = result.scalars().all()

    tag_counter: Counter[str] = Counter()
    for item in items:
        tags = item.tags if isinstance(item.tags, list) else []
        for tag in tags:
            if isinstance(tag, str) and tag.strip():
                tag_counter[tag.strip()] += 1

    # Filter to tags with enough items
    common_tags = [
        (tag, count) for tag, count in tag_counter.most_common(top_k)
        if count >= min_cluster_size
    ]

    created_topics: list[Topic] = []
    for tag_name, count in common_tags:
        # Check if topic already exists
        existing = await session.execute(
            select(Topic).where(Topic.name == tag_name)
        )
        if existing.scalar_one_or_none():
            continue

        topic = Topic(name=tag_name, description=f"Auto-discovered from {count} items", version=1)
        session.add(topic)
        created_topics.append(topic)

    if created_topics:
        await session.flush()
        logger.info("taxonomy_bootstrapped", new_topics=len(created_topics))

    return created_topics


async def classify_item(
    item: Item,
    session: AsyncSession,
) -> list[ItemTopic]:
    """Classify an item into existing taxonomy topics.

    Simple approach: match item tags against topic names.
    LLM-based classification in a future iteration.
    """
    item_tags = item.tags if isinstance(item.tags, list) else []
    if not item_tags:
        return []

    # Get all topics
    result = await session.execute(select(Topic))
    topics = {t.name.lower(): t for t in result.scalars().all()}

    assignments: list[ItemTopic] = []
    for tag in item_tags:
        tag_lower = tag.lower().strip() if isinstance(tag, str) else ""
        if tag_lower in topics:
            topic = topics[tag_lower]
            # Check if already assigned
            existing = await session.execute(
                select(ItemTopic).where(
                    ItemTopic.item_id == item.id,
                    ItemTopic.topic_id == topic.id,
                )
            )
            if existing.scalar_one_or_none():
                continue

            assignment = ItemTopic(
                item_id=item.id,
                topic_id=topic.id,
                confidence=1.0,
                taxonomy_version=topic.version,
            )
            session.add(assignment)
            assignments.append(assignment)

    if assignments:
        await session.flush()

    return assignments


async def propose_taxonomy_changes(
    session: AsyncSession,
    min_items_for_new: int = 10,
) -> list[TaxonomyProposal]:
    """Analyze current corpus and propose taxonomy changes.

    Proposes:
    - New topics for frequent unclassified tags
    - Merges for topics with high tag overlap
    """
    proposals: list[TaxonomyProposal] = []

    # Find frequent tags not in taxonomy
    result = await session.execute(select(Item))
    items = result.scalars().all()

    tag_counter: Counter[str] = Counter()
    for item in items:
        tags = item.tags if isinstance(item.tags, list) else []
        for tag in tags:
            if isinstance(tag, str) and tag.strip():
                tag_counter[tag.strip()] += 1

    # Existing topics
    topic_result = await session.execute(select(Topic))
    existing_names = {t.name.lower() for t in topic_result.scalars().all()}

    # Propose new topics
    for tag, count in tag_counter.most_common(100):
        if tag.lower() not in existing_names and count >= min_items_for_new:
            proposals.append(TaxonomyProposal(
                action="new",
                topic_name=tag,
                details=f"Found in {count} items but not in taxonomy",
                confidence=min(count / 50, 1.0),
            ))

    logger.info("taxonomy_proposals", count=len(proposals))
    return proposals


async def apply_proposal(
    proposal: TaxonomyProposal,
    session: AsyncSession,
) -> Topic | None:
    """Apply a taxonomy proposal."""
    if proposal.action == "new":
        existing = await session.execute(
            select(Topic).where(Topic.name == proposal.topic_name)
        )
        if existing.scalar_one_or_none():
            return None

        topic = Topic(
            name=proposal.topic_name,
            description=f"Proposed: {proposal.details}",
            version=1,
        )
        session.add(topic)
        await session.flush()
        logger.info("taxonomy_topic_created", name=proposal.topic_name)
        return topic

    return None


async def get_taxonomy_stats(session: AsyncSession) -> dict:
    """Get taxonomy statistics."""
    topic_count = await session.execute(select(func.count(Topic.id)))
    assignment_count = await session.execute(select(func.count(ItemTopic.id)))
    item_count = await session.execute(select(func.count(Item.id)))

    return {
        "topics": topic_count.scalar() or 0,
        "assignments": assignment_count.scalar() or 0,
        "items": item_count.scalar() or 0,
    }
