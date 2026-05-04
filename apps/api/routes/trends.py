from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.deps import get_session
from packages.agents.tools.trends import topic_trends

router = APIRouter(prefix="/api/trends", tags=["trends"])


@router.get("/")
async def get_trends(
    days: int = 30,
    top_k: int = 20,
    session: AsyncSession = Depends(get_session),
) -> dict:
    trends = await topic_trends(session, days=days, top_k=top_k)
    return {
        "trends": [
            {
                "topic": t.topic,
                "count": t.count,
                "recent_count": t.recent_count,
                "velocity": t.velocity,
            }
            for t in trends
        ],
    }
