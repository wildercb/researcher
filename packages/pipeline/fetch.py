"""Fetch stage — pulls raw items from a source and persists them."""

from __future__ import annotations

from datetime import datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.models import RawItem as RawItemModel
from packages.sources.base import SourceRawItem

logger = structlog.get_logger()


async def fetch_and_persist(
    source_name: str,
    source_instance: object,
    session: AsyncSession,
    since: datetime | None = None,
) -> list[SourceRawItem]:
    """Fetch raw items from a source and persist to raw_items table.

    Idempotent on (source, source_id) — skips items already stored.
    Returns list of newly persisted raw items.
    """
    new_items: list[SourceRawItem] = []
    count = 0
    skipped = 0

    async for raw in source_instance.fetch(since=since):
        count += 1
        # Check if already exists
        existing = await session.execute(
            select(RawItemModel).where(
                RawItemModel.source == source_name,
                RawItemModel.source_id == raw.source_id,
            )
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        # Persist immediately
        db_raw = RawItemModel(
            source=source_name,
            source_id=raw.source_id,
            payload=raw.payload,
            fetched_at=raw.fetched_at,
        )
        session.add(db_raw)
        new_items.append(raw)

    await session.flush()

    logger.info(
        "fetch_complete",
        source=source_name,
        total=count,
        new=len(new_items),
        skipped=skipped,
    )
    return new_items
