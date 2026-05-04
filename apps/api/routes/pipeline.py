from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from packages.core.config import get_settings
from packages.core.storage import create_storage

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class PipelineRunRequest(BaseModel):
    source: str | None = None
    since: str | None = None
    enrich: bool = True


@router.post("/run")
async def trigger_pipeline(req: PipelineRunRequest, background_tasks: BackgroundTasks) -> dict:
    """Trigger pipeline run (async — returns immediately)."""
    background_tasks.add_task(_run_pipeline, req.source, req.since, req.enrich)
    return {"status": "started", "source": req.source or "all enabled"}


async def _run_pipeline(source: str | None, since: str | None, enrich: bool) -> None:
    from datetime import datetime

    import yaml

    from packages.pipeline.runner import run_pipeline

    settings = get_settings()
    storage = create_storage(settings)
    await storage.init()

    since_dt = datetime.strptime(since, "%Y-%m-%d") if since else None

    sources_to_run = []
    if source:
        sources_to_run = [source]
    else:
        from pathlib import Path

        config_path = Path("config/sources.yaml")
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
            sources_to_run = [name for name, cfg in config.items() if cfg.get("enabled")]

    for src in sources_to_run:
        try:
            await run_pipeline(src, storage, since=since_dt, enrich=enrich)
        except Exception:
            pass

    await storage.close()
