"""Citation graph tools."""

from __future__ import annotations

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.models import Citation, Item


class CitationLink(BaseModel):
    citing_id: int
    citing_title: str
    cited_id: int | None
    cited_doi: str | None
    cited_title: str | None


async def citation_graph(
    item_id: int,
    session: AsyncSession,
    direction: str = "both",  # "citing", "cited", "both"
    depth: int = 1,
) -> list[CitationLink]:
    """Get citation links for an item."""
    links: list[CitationLink] = []

    if direction in ("citing", "both"):
        result = await session.execute(
            select(Citation).where(Citation.citing_item_id == item_id)
        )
        for cit in result.scalars().all():
            cited_title = cit.cited_title
            if cit.cited_item_id:
                item_result = await session.execute(
                    select(Item.title).where(Item.id == cit.cited_item_id)
                )
                row = item_result.first()
                if row:
                    cited_title = row[0]

            links.append(CitationLink(
                citing_id=item_id,
                citing_title="",
                cited_id=cit.cited_item_id,
                cited_doi=cit.cited_doi,
                cited_title=cited_title,
            ))

    if direction in ("cited", "both"):
        result = await session.execute(
            select(Citation).where(Citation.cited_item_id == item_id)
        )
        for cit in result.scalars().all():
            citing_result = await session.execute(
                select(Item.title).where(Item.id == cit.citing_item_id)
            )
            row = citing_result.first()
            citing_title = row[0] if row else ""

            links.append(CitationLink(
                citing_id=cit.citing_item_id,
                citing_title=citing_title,
                cited_id=item_id,
                cited_doi=None,
                cited_title="",
            ))

    return links
