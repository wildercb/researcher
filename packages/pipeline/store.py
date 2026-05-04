"""Store stage — persists normalized items to the items table."""

from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.models import Item
from packages.sources.base import NormalizedItem

logger = structlog.get_logger()


async def store_item(
    normalized: NormalizedItem,
    session: AsyncSession,
) -> Item:
    """Create an Item from a NormalizedItem and persist it."""
    item = Item(
        source=normalized.source,
        source_id=normalized.source_id,
        kind=normalized.kind,
        title=normalized.title,
        abstract=normalized.abstract,
        authors=normalized.authors,
        affiliations=normalized.affiliations,
        venue=normalized.venue,
        published_at=normalized.published_at,
        url=normalized.url,
        pdf_url=normalized.pdf_url,
        doi=normalized.doi,
        arxiv_id=normalized.arxiv_id,
        tags=normalized.tags,
        raw=normalized.raw,
        enrichment_status="pending",
    )
    session.add(item)
    await session.flush()  # get the ID

    logger.debug(
        "item_stored",
        item_id=item.id,
        source=normalized.source,
        title=normalized.title[:80],
    )
    return item
