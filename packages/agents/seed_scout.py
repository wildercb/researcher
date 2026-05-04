"""Seed scout agent — proposes new seeds based on observed high-relevance non-seeds."""

from __future__ import annotations

from dataclasses import dataclass

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.models import Item, Seed

logger = structlog.get_logger()


@dataclass
class SeedProposal:
    seed_type: str  # "author" or "venue"
    identifier: str
    reason: str
    score: float  # how strongly this should be a seed


async def scout_seeds(
    session: AsyncSession,
    min_items: int = 5,
    min_relevance: float = 0.6,
    top_k: int = 10,
) -> list[SeedProposal]:
    """Find authors and venues that consistently produce high-relevance items
    but aren't already seeds.

    Returns proposed promotions.
    """
    proposals: list[SeedProposal] = []

    # Get existing seed identifiers
    seed_result = await session.execute(select(Seed))
    existing_seeds = {s.identifier.lower() for s in seed_result.scalars().all()}

    # Get high-relevance items
    result = await session.execute(
        select(Item).where(Item.relevance_score >= min_relevance)
    )
    items = result.scalars().all()

    # Count authors
    from collections import Counter
    author_counts: Counter[str] = Counter()
    author_scores: dict[str, list[float]] = {}

    venue_counts: Counter[str] = Counter()
    venue_scores: dict[str, list[float]] = {}

    for item in items:
        score = item.relevance_score or 0

        authors = item.authors if isinstance(item.authors, list) else []
        for author in authors:
            if isinstance(author, str) and author:
                author_counts[author] += 1
                author_scores.setdefault(author, []).append(score)

        if item.venue:
            venue_counts[item.venue] += 1
            venue_scores.setdefault(item.venue, []).append(score)

    # Propose top authors
    for author, count in author_counts.most_common(top_k * 2):
        if count < min_items:
            continue
        if author.lower() in existing_seeds:
            continue
        avg_score = sum(author_scores[author]) / len(author_scores[author])
        proposals.append(SeedProposal(
            seed_type="author",
            identifier=author,
            reason=f"{count} high-relevance papers, avg score {avg_score:.2f}",
            score=avg_score,
        ))

    # Propose top venues
    for venue, count in venue_counts.most_common(top_k):
        if count < min_items:
            continue
        if venue.lower() in existing_seeds:
            continue
        avg_score = sum(venue_scores[venue]) / len(venue_scores[venue])
        proposals.append(SeedProposal(
            seed_type="venue",
            identifier=venue,
            reason=f"{count} high-relevance papers, avg score {avg_score:.2f}",
            score=avg_score,
        ))

    # Sort by score
    proposals.sort(key=lambda p: p.score, reverse=True)

    logger.info("seed_scout", proposals=len(proposals))
    return proposals[:top_k]
