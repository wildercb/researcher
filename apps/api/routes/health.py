from fastapi import APIRouter

from packages.core.config import get_settings

router = APIRouter()


@router.get("/api/health")
async def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "mode": settings.mode.value,
        "version": "0.1.0",
    }
