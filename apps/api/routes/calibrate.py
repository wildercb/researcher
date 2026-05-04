import os

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

router = APIRouter(prefix="/api/calibrate", tags=["calibrate"])


class CalibrateRequest(BaseModel):
    depth: int = 1
    max_items: int = 500


@router.post("/")
async def trigger_calibrate(req: CalibrateRequest, background_tasks: BackgroundTasks) -> dict:
    """Trigger calibration crawl (async)."""
    background_tasks.add_task(_run_calibrate, req.depth, req.max_items)
    return {"status": "started", "depth": req.depth, "max_items": req.max_items}


async def _run_calibrate(depth: int, max_items: int) -> None:
    from packages.seeds.crawl import run_calibration

    s2_key = os.environ.get("S2_API_KEY") or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    await run_calibration(
        seeds_path="config/seeds.yaml",
        depth=depth,
        max_items=max_items,
        s2_api_key=s2_key,
    )
