"""Trends tools — topic and tag analysis."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.models import Item


class TopicTrend(BaseModel):
    topic: str
    count: int
    recent_count: int  # last 7 days
    velocity: float  # recent / total ratio


async def topic_trends(
    session: AsyncSession,
    days: int = 30,
    top_k: int = 20,
) -> list[TopicTrend]:
    """Compute topic trends from item tags over a time window."""
    since = datetime.now() - timedelta(days=days)
    recent_cutoff = datetime.now() - timedelta(days=7)

    result = await session.execute(
        select(Item).where(Item.created_at >= since)
    )
    items = result.scalars().all()

    total_counts: Counter[str] = Counter()
    recent_counts: Counter[str] = Counter()

    for item in items:
        tags = item.tags if isinstance(item.tags, list) else []
        for tag in tags:
            if isinstance(tag, str) and tag:
                total_counts[tag] += 1
                if item.created_at and item.created_at >= recent_cutoff:
                    recent_counts[tag] += 1

    trends = []
    for topic, count in total_counts.most_common(top_k):
        recent = recent_counts.get(topic, 0)
        velocity = recent / max(count, 1)
        trends.append(TopicTrend(
            topic=topic,
            count=count,
            recent_count=recent,
            velocity=round(velocity, 3),
        ))

    # Sort by velocity (accelerating topics first)
    trends.sort(key=lambda t: t.velocity, reverse=True)
    return trends
