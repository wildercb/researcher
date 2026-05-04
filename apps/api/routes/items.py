from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.deps import get_session
from packages.core.models import Item

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("/")
async def list_items(
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await session.execute(
        select(Item).order_by(Item.created_at.desc()).limit(limit).offset(offset)
    )
    items = result.scalars().all()
    return {
        "items": [
            {
                "id": item.id,
                "title": item.title,
                "source": item.source,
                "kind": item.kind,
                "authors": item.authors,
                "venue": item.venue,
                "published_at": item.published_at.isoformat() if item.published_at else None,
                "url": item.url,
                "relevance_score": item.relevance_score,
                "summary": item.summary,
            }
            for item in items
        ],
        "total": len(items),
    }
