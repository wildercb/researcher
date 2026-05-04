"""Parse stage — converts raw items to normalized items."""

from __future__ import annotations

import structlog

from packages.sources.base import NormalizedItem, SourceRawItem

logger = structlog.get_logger()


def parse_raw_items(
    source_instance: object,
    raw_items: list[SourceRawItem],
) -> list[NormalizedItem]:
    """Parse raw items through the source's parse method.

    Skips items that fail to parse (logs warning).
    """
    normalized: list[NormalizedItem] = []
    errors = 0

    for raw in raw_items:
        try:
            item = source_instance.parse(raw)
            normalized.append(item)
        except Exception as e:
            errors += 1
            logger.warning(
                "parse_failed",
                source_id=raw.source_id,
                error=str(e),
            )

    if errors:
        logger.info("parse_complete", total=len(raw_items), parsed=len(normalized), errors=errors)

    return normalized
