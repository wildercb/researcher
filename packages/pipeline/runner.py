"""Pipeline runner — orchestrates fetch → parse → dedupe → enrich → store."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import structlog
import yaml

from packages.core.storage import PostgresStorage, SQLiteStorage
from packages.pipeline.dedupe import dedupe_item
from packages.pipeline.enrich import enrich_item, load_interest_profile
from packages.pipeline.fetch import fetch_and_persist
from packages.pipeline.parse import parse_raw_items
from packages.pipeline.store import store_item

logger = structlog.get_logger()


@dataclass
class PipelineResult:
    source: str
    fetched: int = 0
    parsed: int = 0
    new_items: int = 0
    duplicates: int = 0
    enriched: int = 0
    failed: int = 0
    started_at: datetime = field(default_factory=datetime.now)

    @property
    def elapsed_seconds(self) -> float:
        return (datetime.now() - self.started_at).total_seconds()


async def run_pipeline(
    source_name: str,
    storage: SQLiteStorage | PostgresStorage,
    since: datetime | None = None,
    enrich: bool = True,
) -> PipelineResult:
    """Run the full ingestion pipeline for a source.

    Fetch → Parse → Dedupe → Enrich → Store
    """
    import packages.sources  # noqa: F401 — trigger registration
    from packages.sources.registry import get_source

    result = PipelineResult(source=source_name)

    # Load source config
    config = _load_source_config(source_name)
    src_cls = get_source(source_name)
    src = src_cls(config)

    # Load interest profile for enrichment
    interest = load_interest_profile() if enrich else None

    async with storage.session() as session:
        # 1. Fetch
        try:
            raw_items = await fetch_and_persist(source_name, src, session, since=since)
            result.fetched = len(raw_items)
        except Exception as e:
            logger.error("pipeline_fetch_failed", source=source_name, error=str(e))
            result.failed += 1
            return result

        # 2. Parse
        normalized = parse_raw_items(src, raw_items)
        result.parsed = len(normalized)

        # 3. Dedupe + Store + Enrich
        for norm_item in normalized:
            try:
                existing, is_new = await dedupe_item(norm_item, session)

                if is_new:
                    item = await store_item(norm_item, session)
                    result.new_items += 1

                    # 4. Enrich
                    if enrich:
                        try:
                            await enrich_item(item, interest_profile=interest)
                            if item.enrichment_status == "enriched":
                                result.enriched += 1
                        except Exception as e:
                            logger.warning("enrich_failed", item_id=item.id, error=str(e))
                else:
                    result.duplicates += 1

            except Exception as e:
                result.failed += 1
                logger.warning(
                    "pipeline_item_failed",
                    source=source_name,
                    source_id=norm_item.source_id,
                    error=str(e),
                )

    logger.info(
        "pipeline_complete",
        source=source_name,
        fetched=result.fetched,
        parsed=result.parsed,
        new=result.new_items,
        dupes=result.duplicates,
        enriched=result.enriched,
        failed=result.failed,
        elapsed_s=round(result.elapsed_seconds, 1),
    )
    return result


def _load_source_config(source_name: str) -> dict:
    path = Path("config/sources.yaml")
    if path.exists():
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return data.get(source_name, {})
    return {}
