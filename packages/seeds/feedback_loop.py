"""Feedback loop — updates interest profile drift from user signals.

Implicit feedback:
- liked → strong positive on item + tags + authors
- hidden → negative
- read/deep_read → weak positive
- more_like_this → strong positive on cluster

Drift is bounded: feedback shifts but cannot erase seed-derived anchors.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path

import structlog
import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.models import FeedbackEvent, Item

logger = structlog.get_logger()

# Signal weights
SIGNAL_WEIGHTS = {
    "liked": 1.0,
    "more_like_this": 1.5,
    "read": 0.3,
    "deep_read": 0.5,
    "hidden": -1.0,
}

# Drift is bounded to this fraction of the seed-derived profile
MAX_DRIFT_RATIO = 0.3


async def compute_drift(
    session: AsyncSession,
    since: datetime | None = None,
) -> dict:
    """Compute drift adjustments from feedback events.

    Returns dict with tag_drift, author_drift, venue_drift (deltas to affinities).
    """
    stmt = select(FeedbackEvent)
    if since:
        stmt = stmt.where(FeedbackEvent.created_at >= since)
    result = await session.execute(stmt)
    events = result.scalars().all()

    tag_drift: Counter[str] = Counter()
    author_drift: Counter[str] = Counter()
    venue_drift: Counter[str] = Counter()

    for event in events:
        weight = SIGNAL_WEIGHTS.get(event.signal, 0)
        if weight == 0:
            continue

        # Fetch the item
        item_result = await session.execute(
            select(Item).where(Item.id == event.item_id)
        )
        item = item_result.scalar_one_or_none()
        if not item:
            continue

        tags = item.tags if isinstance(item.tags, list) else []
        authors = item.authors if isinstance(item.authors, list) else []

        for tag in tags:
            if isinstance(tag, str) and tag:
                tag_drift[tag] += weight

        for author in authors:
            if isinstance(author, str) and author:
                author_drift[author] += weight

        if item.venue:
            venue_drift[item.venue] += weight

    logger.info(
        "drift_computed",
        events=len(events),
        tag_changes=len(tag_drift),
        author_changes=len(author_drift),
        venue_changes=len(venue_drift),
    )

    return {
        "tag_drift": dict(tag_drift.most_common(50)),
        "author_drift": dict(author_drift.most_common(50)),
        "venue_drift": dict(venue_drift.most_common(30)),
        "event_count": len(events),
    }


def apply_drift_to_profile(
    profile: dict,
    drift: dict,
    output_path: str | Path = "config/interest.yaml",
) -> dict:
    """Apply drift adjustments to the interest profile.

    Drift is bounded: each drift value is capped at MAX_DRIFT_RATIO
    of the max affinity value.
    """
    tag_affinities = dict(profile.get("tag_affinities", {}))
    author_affinities = dict(profile.get("author_affinities", {}))
    venue_affinities = dict(profile.get("venue_affinities", {}))

    # Apply tag drift
    max_tag = max(tag_affinities.values(), default=1.0)
    for tag, delta in drift.get("tag_drift", {}).items():
        bounded = max(-MAX_DRIFT_RATIO * max_tag, min(delta * 0.1, MAX_DRIFT_RATIO * max_tag))
        current = tag_affinities.get(tag, 0)
        tag_affinities[tag] = round(max(0, min(1.0, current + bounded)), 4)

    # Apply author drift
    max_author = max(author_affinities.values(), default=1.0)
    for author, delta in drift.get("author_drift", {}).items():
        bounded = max(-MAX_DRIFT_RATIO * max_author, min(delta * 0.1, MAX_DRIFT_RATIO * max_author))
        current = author_affinities.get(author, 0)
        author_affinities[author] = round(max(0, min(1.0, current + bounded)), 4)

    # Apply venue drift
    max_venue = max(venue_affinities.values(), default=1.0)
    for venue, delta in drift.get("venue_drift", {}).items():
        bounded = max(-MAX_DRIFT_RATIO * max_venue, min(delta * 0.1, MAX_DRIFT_RATIO * max_venue))
        current = venue_affinities.get(venue, 0)
        venue_affinities[venue] = round(max(0, min(1.0, current + bounded)), 4)

    profile["tag_affinities"] = tag_affinities
    profile["author_affinities"] = author_affinities
    profile["venue_affinities"] = venue_affinities
    profile["drift"] = {
        "feedback_events": drift.get("event_count", 0),
        "last_updated": datetime.now().isoformat(),
    }

    # Write updated profile
    output_path = Path(output_path)
    with open(output_path, "w") as f:
        f.write("# Atlas interest profile — DERIVED, not hand-edited.\n")
        f.write("# Updated with feedback drift.\n\n")
        yaml.dump(profile, f, default_flow_style=False, sort_keys=False)

    logger.info("drift_applied", events=drift.get("event_count", 0))
    return profile
