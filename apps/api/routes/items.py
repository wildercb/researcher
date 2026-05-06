from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.deps import get_session
from packages.core.models import FeedbackEvent, Item

router = APIRouter(prefix="/api/items", tags=["items"])


def _serialize_item(item: Item) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "abstract": item.abstract,
        "source": item.source,
        "kind": item.kind,
        "authors": item.authors if isinstance(item.authors, list) else [],
        "venue": item.venue,
        "published_at": item.published_at.isoformat() if item.published_at else None,
        "url": item.url,
        "pdf_url": item.pdf_url,
        "doi": item.doi,
        "arxiv_id": item.arxiv_id,
        "tags": item.tags if isinstance(item.tags, list) else [],
        "relevance_score": item.relevance_score,
        "summary": item.summary,
        "enrichment_status": item.enrichment_status,
    }


@router.get("/")
async def list_items(
    limit: int = 50,
    offset: int = 0,
    q: str | None = None,
    source: str | None = None,
    kind: str | None = None,
    sort: str = "date",
    session: AsyncSession = Depends(get_session),
) -> dict:
    stmt = select(Item)

    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(or_(Item.title.ilike(pattern), Item.abstract.ilike(pattern)))
    if source:
        stmt = stmt.where(Item.source == source)
    if kind:
        stmt = stmt.where(Item.kind == kind)

    if sort == "relevance":
        stmt = stmt.order_by(Item.relevance_score.desc().nullslast())
    else:
        stmt = stmt.order_by(Item.created_at.desc())

    stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(stmt)
    items = result.scalars().all()

    return {
        "items": [_serialize_item(item) for item in items],
        "total": len(items),
    }


@router.get("/{item_id}")
async def get_item(item_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    result = await session.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        return {"error": "not found"}
    return _serialize_item(item)


class FeedbackRequest(BaseModel):
    signal: str  # liked, hidden, read, deep_read, more_like_this


@router.post("/{item_id}/feedback")
async def item_feedback(
    item_id: int,
    req: FeedbackRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    event = FeedbackEvent(item_id=item_id, signal=req.signal)
    session.add(event)
    return {"status": "recorded", "signal": req.signal}


class EnrichRequest(BaseModel):
    summary: str | None = None
    relevance_score: float | None = None
    relevance_reason: str | None = None
    authors: list[str] | None = None
    venue: str | None = None
    published_at: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    url: str | None = None
    pdf_url: str | None = None
    tags: list[str] | None = None
    enrichment_status: str = "enriched"


@router.patch("/{item_id}")
async def patch_item(
    item_id: int,
    req: EnrichRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Update any item fields (used by Claude Code agent)."""
    result = await session.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        return {"error": "not found"}
    if req.summary is not None:
        item.summary = req.summary
    if req.relevance_score is not None:
        item.relevance_score = req.relevance_score
    if req.relevance_reason is not None:
        item.relevance_reason = req.relevance_reason
    if req.authors is not None:
        item.authors = req.authors
    if req.venue is not None:
        item.venue = req.venue
    if req.published_at is not None:
        from datetime import datetime
        try:
            item.published_at = datetime.fromisoformat(req.published_at)
        except (ValueError, TypeError):
            pass
    if req.doi is not None:
        item.doi = req.doi
    if req.arxiv_id is not None:
        item.arxiv_id = req.arxiv_id
    if req.url is not None:
        item.url = req.url
    if req.pdf_url is not None:
        item.pdf_url = req.pdf_url
    if req.tags is not None:
        item.tags = req.tags
    item.enrichment_status = req.enrichment_status
    return {"status": "updated", "id": item_id}
