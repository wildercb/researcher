from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.deps import get_session
from packages.core.models import Seed

router = APIRouter(prefix="/api/seeds", tags=["seeds"])


@router.get("/")
async def list_seeds(session: AsyncSession = Depends(get_session)) -> dict:
    result = await session.execute(select(Seed).order_by(Seed.created_at.desc()))
    seeds = result.scalars().all()
    return {
        "seeds": [
            {
                "id": s.id,
                "type": s.seed_type,
                "identifier": s.identifier,
                "label": s.label,
                "weight": s.weight,
                "is_negative": s.is_negative,
            }
            for s in seeds
        ],
    }
