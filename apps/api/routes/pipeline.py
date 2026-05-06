"""Pipeline API — fetch new papers from sources."""

from datetime import datetime

import structlog
import yaml
from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.deps import get_session
from packages.core.config import get_settings
from packages.core.models import Item
from packages.core.storage import create_storage

logger = structlog.get_logger()

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

# Track pipeline runs
_pipeline_status: dict = {"running": False, "last_run": None, "results": []}


class PipelineRunRequest(BaseModel):
    source: str | None = None
    since: str | None = None
    enrich: bool = False  # default off — enrichment is slow


@router.post("/run")
async def trigger_pipeline(req: PipelineRunRequest, background_tasks: BackgroundTasks) -> dict:
    if _pipeline_status["running"]:
        return {"status": "already_running"}
    _pipeline_status["running"] = True
    _pipeline_status["results"] = []
    background_tasks.add_task(_run_pipeline, req.source, req.since, req.enrich)
    return {"status": "started", "source": req.source or "all enabled"}


@router.get("/status")
async def pipeline_status() -> dict:
    return _pipeline_status


@router.get("/stats")
async def pipeline_stats(session: AsyncSession = Depends(get_session)) -> dict:
    """Item counts per source."""
    result = await session.execute(
        select(Item.source, func.count(Item.id)).group_by(Item.source)
    )
    by_source = {row[0]: row[1] for row in result.all()}
    total = await session.execute(select(func.count(Item.id)))
    enriched = await session.execute(
        select(func.count(Item.id)).where(Item.enrichment_status == "enriched")
    )
    return {
        "total_items": total.scalar() or 0,
        "enriched_items": enriched.scalar() or 0,
        "by_source": by_source,
    }


async def _run_pipeline(source: str | None, since: str | None, enrich: bool) -> None:
    from pathlib import Path

    from packages.pipeline.runner import run_pipeline

    settings = get_settings()
    storage = create_storage(settings)
    await storage.init()

    since_dt = datetime.strptime(since, "%Y-%m-%d") if since else None

    sources_to_run = []
    if source:
        sources_to_run = [source]
    else:
        config_path = Path("config/sources.yaml")
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
            sources_to_run = [name for name, cfg in config.items() if cfg.get("enabled")]

    for src in sources_to_run:
        try:
            result = await run_pipeline(src, storage, since=since_dt, enrich=enrich)
            _pipeline_status["results"].append({
                "source": src,
                "fetched": result.fetched,
                "new": result.new_items,
                "dupes": result.duplicates,
                "elapsed": round(result.elapsed_seconds, 1),
            })
        except Exception as e:
            _pipeline_status["results"].append({
                "source": src,
                "error": str(e)[:200],
            })
            logger.warning("pipeline_source_failed", source=src, error=str(e))

    await storage.close()
    _pipeline_status["running"] = False
    _pipeline_status["last_run"] = datetime.now().isoformat()
