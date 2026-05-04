from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.deps import get_session
from packages.core.models import Seed

router = APIRouter(prefix="/api/seeds", tags=["seeds"])


class AddSeedRequest(BaseModel):
    type: str  # paper, author, venue, keyword
    identifier: str
    weight: float = 1.0
    is_negative: bool = False


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


@router.post("/")
async def add_seed(req: AddSeedRequest, session: AsyncSession = Depends(get_session)) -> dict:
    seed = Seed(
        seed_type=req.type,
        identifier=req.identifier,
        label=req.identifier,
        weight=req.weight,
        is_negative=req.is_negative,
    )
    session.add(seed)
    await session.flush()
    return {"id": seed.id, "status": "added"}


@router.delete("/{seed_id}")
async def delete_seed(seed_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    await session.execute(delete(Seed).where(Seed.id == seed_id))
    return {"status": "deleted"}
