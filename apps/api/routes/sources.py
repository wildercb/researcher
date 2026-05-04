from fastapi import APIRouter

from packages.sources.registry import list_sources

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("/")
async def get_sources() -> dict:
    return {"sources": list_sources()}
