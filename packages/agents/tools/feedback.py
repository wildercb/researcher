"""Feedback tool — record user signals on items."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.models import FeedbackEvent
from packages.core.types import FeedbackSignal


async def record_feedback(
    item_id: int,
    signal: FeedbackSignal,
    session: AsyncSession,
    metadata: dict | None = None,
) -> FeedbackEvent:
    """Record a feedback event for an item."""
    event = FeedbackEvent(
        item_id=item_id,
        signal=signal.value,
        metadata_=metadata or {},
    )
    session.add(event)
    await session.flush()
    return event
