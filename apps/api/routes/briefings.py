"""Briefings API — generate and retrieve research briefings."""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.deps import get_session
from packages.core.models import Item

router = APIRouter(prefix="/api/briefings", tags=["briefings"])

# We store briefings in a simple in-memory list for now
# (adding a DB table is trivial but overkill for v1)
_briefings: list[dict] = []


@router.get("/")
async def list_briefings() -> dict:
    return {"briefings": _briefings}


@router.get("/{briefing_id}")
async def get_briefing(briefing_id: int) -> dict:
    if 0 <= briefing_id < len(_briefings):
        return _briefings[briefing_id]
    return {"error": "not found"}


class GenerateRequest(BaseModel):
    period: str = "daily"


@router.post("/generate")
async def generate_briefing(
    req: GenerateRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Generate a briefing from top items. Works without LLM — uses item data directly."""
    # Get top items by relevance
    result = await session.execute(
        select(Item)
        .where(Item.relevance_score.isnot(None))
        .order_by(Item.relevance_score.desc())
        .limit(30)
    )
    items = result.scalars().all()

    if not items:
        return {"error": "No items with relevance scores. Run calibration first."}

    must_read = []
    on_radar = []
    for item in items:
        score = item.relevance_score or 0
        entry = {
            "title": item.title,
            "authors": item.authors[:3] if isinstance(item.authors, list) else [],
            "venue": item.venue,
            "url": item.url,
            "score": round(score, 2),
            "summary": item.summary,
            "source": item.source,
        }
        if score >= 0.7:
            must_read.append(entry)
        elif score >= 0.4:
            on_radar.append(entry)

    # Build markdown briefing
    now = datetime.now()
    lines = [f"# {req.period.title()} Research Briefing", f"*{now.strftime('%B %d, %Y')}*\n"]

    if must_read:
        lines.append("## Must-Read\n")
        for item in must_read[:10]:
            authors = ", ".join(item["authors"]) if item["authors"] else "Unknown"
            lines.append(f"### [{item['title']}]({item['url']})")
            lines.append(f"**{authors}**" + (f" — {item['venue']}" if item["venue"] else ""))
            lines.append(f"Relevance: {item['score']}")
            if item["summary"]:
                lines.append(f"\n{item['summary']}")
            lines.append("")

    if on_radar:
        lines.append("## On the Radar\n")
        for item in on_radar[:10]:
            lines.append(f"- [{item['title']}]({item['url']}) — {item['score']}")

    content = "\n".join(lines)

    briefing = {
        "id": len(_briefings),
        "period": req.period,
        "content": content,
        "created_at": now.isoformat(),
        "must_read_count": len(must_read),
        "on_radar_count": len(on_radar),
    }
    _briefings.insert(0, briefing)

    return briefing
