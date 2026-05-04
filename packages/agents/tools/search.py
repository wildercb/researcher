"""Search tools — query the item corpus."""

from __future__ import annotations

from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.models import Item


class SearchResult(BaseModel):
    id: int
    title: str
    source: str
    kind: str
    authors: list
    venue: str | None
    relevance_score: float | None
    summary: str | None
    url: str


async def keyword_search(
    query: str,
    session: AsyncSession,
    k: int = 20,
    source_filter: str | None = None,
    kind_filter: str | None = None,
) -> list[SearchResult]:
    """Search items by keyword in title and abstract."""
    pattern = f"%{query}%"
    stmt = select(Item).where(
        or_(
            Item.title.ilike(pattern),
            Item.abstract.ilike(pattern),
        )
    )
    if source_filter:
        stmt = stmt.where(Item.source == source_filter)
    if kind_filter:
        stmt = stmt.where(Item.kind == kind_filter)

    stmt = stmt.order_by(Item.relevance_score.desc().nullslast()).limit(k)

    result = await session.execute(stmt)
    items = result.scalars().all()

    return [_item_to_result(item) for item in items]


async def recent_items(
    session: AsyncSession,
    k: int = 20,
    source_filter: str | None = None,
) -> list[SearchResult]:
    """Get the most recent items."""
    stmt = select(Item).order_by(Item.created_at.desc())
    if source_filter:
        stmt = stmt.where(Item.source == source_filter)
    stmt = stmt.limit(k)

    result = await session.execute(stmt)
    items = result.scalars().all()
    return [_item_to_result(item) for item in items]


async def top_relevant_items(
    session: AsyncSession,
    k: int = 20,
    min_score: float = 0.3,
) -> list[SearchResult]:
    """Get items with highest relevance scores."""
    stmt = (
        select(Item)
        .where(Item.relevance_score >= min_score)
        .order_by(Item.relevance_score.desc())
        .limit(k)
    )
    result = await session.execute(stmt)
    items = result.scalars().all()
    return [_item_to_result(item) for item in items]


def _item_to_result(item: Item) -> SearchResult:
    return SearchResult(
        id=item.id,
        title=item.title,
        source=item.source,
        kind=item.kind,
        authors=item.authors if isinstance(item.authors, list) else [],
        venue=item.venue,
        relevance_score=item.relevance_score,
        summary=item.summary,
        url=item.url,
    )
