"""Lookup tools — read items and author profiles."""

from __future__ import annotations

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.models import Item


class ItemDetail(BaseModel):
    id: int
    title: str
    abstract: str | None
    source: str
    kind: str
    authors: list
    venue: str | None
    published_at: str | None
    url: str
    pdf_url: str | None
    doi: str | None
    arxiv_id: str | None
    tags: list
    summary: str | None
    relevance_score: float | None


class AuthorProfile(BaseModel):
    name: str
    paper_count: int
    recent_papers: list[dict]
    venues: list[str]


async def read_item(item_id: int, session: AsyncSession) -> ItemDetail | None:
    """Get full details for an item."""
    result = await session.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        return None

    return ItemDetail(
        id=item.id,
        title=item.title,
        abstract=item.abstract,
        source=item.source,
        kind=item.kind,
        authors=item.authors if isinstance(item.authors, list) else [],
        venue=item.venue,
        published_at=item.published_at.isoformat() if item.published_at else None,
        url=item.url,
        pdf_url=item.pdf_url,
        doi=item.doi,
        arxiv_id=item.arxiv_id,
        tags=item.tags if isinstance(item.tags, list) else [],
        summary=item.summary,
        relevance_score=item.relevance_score,
    )


async def author_profile(name: str, session: AsyncSession) -> AuthorProfile | None:
    """Build an author profile from the corpus."""
    # Find items by this author (JSON array contains check varies by DB)
    # Simple approach: search items where authors list contains the name
    result = await session.execute(
        select(Item).order_by(Item.created_at.desc()).limit(500)
    )
    all_items = result.scalars().all()

    papers = []
    venues: set[str] = set()
    for item in all_items:
        authors = item.authors if isinstance(item.authors, list) else []
        if any(name.lower() in a.lower() for a in authors):
            papers.append({
                "id": item.id,
                "title": item.title,
                "venue": item.venue,
                "year": item.published_at.year if item.published_at else None,
            })
            if item.venue:
                venues.add(item.venue)

    if not papers:
        return None

    return AuthorProfile(
        name=name,
        paper_count=len(papers),
        recent_papers=papers[:20],
        venues=sorted(venues),
    )
