"""Backfill — re-enriches items with pending or failed enrichment status."""

from __future__ import annotations

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.models import Item
from packages.pipeline.enrich import enrich_item, load_interest_profile

logger = structlog.get_logger()


async def backfill_enrichment(
    session: AsyncSession,
    limit: int = 100,
) -> int:
    """Re-enrich items that are pending or failed.

    Returns the number of items successfully enriched.
    """
    interest = load_interest_profile()

    result = await session.execute(
        select(Item)
        .where(Item.enrichment_status.in_(["pending", "failed"]))
        .limit(limit)
    )
    items = result.scalars().all()

    enriched_count = 0
    for item in items:
        try:
            await enrich_item(item, interest_profile=interest)
            if item.enrichment_status == "enriched":
                enriched_count += 1
        except Exception as e:
            logger.warning("backfill_item_failed", item_id=item.id, error=str(e))

    logger.info("backfill_complete", total=len(items), enriched=enriched_count)
    return enriched_count
