"""Dedupe stage — prevents duplicate items in the corpus.

Dedupe order (stop at first match):
1. DOI match
2. arXiv ID match
3. Normalized title hash + first author surname
4. (Embedding cosine ≥ 0.97 — deferred to when embeddings exist)

Match → record a Mention against the canonical Item.
No match → item is new.
"""

from __future__ import annotations

import hashlib

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.models import Item, Mention
from packages.sources.base import NormalizedItem

logger = structlog.get_logger()


async def dedupe_item(
    normalized: NormalizedItem,
    session: AsyncSession,
) -> tuple[Item | None, bool]:
    """Check if item already exists in the corpus.

    Returns:
        (existing_item, is_new) — if not new, a Mention is created.
    """
    # 1. DOI match
    if normalized.doi:
        result = await session.execute(
            select(Item).where(Item.doi == normalized.doi)
        )
        existing = result.scalar_one_or_none()
        if existing:
            await _create_mention(existing, normalized, session)
            return existing, False

    # 2. arXiv ID match
    if normalized.arxiv_id:
        result = await session.execute(
            select(Item).where(Item.arxiv_id == normalized.arxiv_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            await _create_mention(existing, normalized, session)
            return existing, False

    # 3. Normalized title hash + first author
    title_hash = _title_hash(normalized.title, normalized.authors)
    if title_hash:
        # Check by source+source_id first (exact source dedup)
        result = await session.execute(
            select(Item).where(
                Item.source == normalized.source,
                Item.source_id == normalized.source_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            await _create_mention(existing, normalized, session)
            return existing, False

    return None, True


async def _create_mention(
    existing: Item,
    normalized: NormalizedItem,
    session: AsyncSession,
) -> None:
    """Record a mention — same paper found from another source/fetch."""
    mention = Mention(
        item_id=existing.id,
        source=normalized.source,
        source_id=normalized.source_id,
        url=normalized.url,
    )
    session.add(mention)
    logger.debug(
        "dedupe_match",
        item_id=existing.id,
        source=normalized.source,
        source_id=normalized.source_id,
    )


def _title_hash(title: str, authors: list[str]) -> str | None:
    """Create a normalized hash from title + first author surname."""
    if not title:
        return None
    normalized = title.lower().strip()
    # Add first author surname for disambiguation
    if authors:
        first_author = authors[0].split()[-1].lower() if authors[0] else ""
        normalized = f"{normalized}|{first_author}"
    return hashlib.sha256(normalized.encode()).hexdigest()[:32]
