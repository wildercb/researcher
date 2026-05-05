"""Briefings API — generate and retrieve research briefings.

Supports two modes:
- "basic": structured summary from item data (no LLM needed)
- "deep": LLM analyzes papers for trends, gaps, research ideas, venue targets
- "claude-code": returns items for Claude Code agent to generate briefing via PATCH
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.deps import get_session
from packages.core.models import Item

router = APIRouter(prefix="/api/briefings", tags=["briefings"])

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
    mode: str = "basic"  # "basic", "deep", or "claude-code"


@router.post("/generate")
async def generate_briefing(
    req: GenerateRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Generate a briefing from top items."""
    # Get top items with abstracts for deep analysis
    result = await session.execute(
        select(Item)
        .where(Item.relevance_score.isnot(None))
        .order_by(Item.relevance_score.desc())
        .limit(50)
    )
    items = result.scalars().all()

    if not items:
        return {"error": "No items with relevance scores. Run calibration first."}

    if req.mode == "claude-code":
        # Return raw data for Claude Code agent to generate briefing
        return {
            "mode": "claude-code",
            "instruction": "Generate a deep research briefing using the items below. Include: key trends, gaps in the literature, research ideas with target venues, and an executive summary.",
            "items": [
                {
                    "id": item.id,
                    "title": item.title,
                    "abstract": item.abstract[:500] if item.abstract else None,
                    "authors": item.authors[:5] if isinstance(item.authors, list) else [],
                    "venue": item.venue,
                    "url": item.url,
                    "score": round(item.relevance_score or 0, 2),
                    "summary": item.summary,
                    "tags": item.tags if isinstance(item.tags, list) else [],
                }
                for item in items[:30]
            ],
        }

    if req.mode == "deep":
        # Try LLM-powered deep analysis
        content = await _generate_deep_briefing(items)
    else:
        content = _generate_basic_briefing(items, req.period)

    now = datetime.now()
    briefing = {
        "id": len(_briefings),
        "period": req.period,
        "mode": req.mode,
        "content": content,
        "created_at": now.isoformat(),
        "must_read_count": sum(1 for i in items if (i.relevance_score or 0) >= 0.7),
        "on_radar_count": sum(1 for i in items if 0.4 <= (i.relevance_score or 0) < 0.7),
    }
    _briefings.insert(0, briefing)
    return briefing


class SaveBriefingRequest(BaseModel):
    content: str
    period: str = "daily"


@router.post("/save")
async def save_briefing(req: SaveBriefingRequest) -> dict:
    """Save a Claude Code-generated briefing."""
    now = datetime.now()
    briefing = {
        "id": len(_briefings),
        "period": req.period,
        "mode": "claude-code",
        "content": req.content,
        "created_at": now.isoformat(),
        "must_read_count": 0,
        "on_radar_count": 0,
    }
    _briefings.insert(0, briefing)
    return briefing


def _generate_basic_briefing(items: list, period: str) -> str:
    """Generate structured briefing without LLM."""
    now = datetime.now()
    lines = [f"# {period.title()} Research Briefing", f"*{now.strftime('%B %d, %Y')}*\n"]

    must_read = [i for i in items if (i.relevance_score or 0) >= 0.7]
    on_radar = [i for i in items if 0.4 <= (i.relevance_score or 0) < 0.7]

    if must_read:
        lines.append("## Must-Read\n")
        for item in must_read[:10]:
            authors = ", ".join(item.authors[:3]) if isinstance(item.authors, list) else "Unknown"
            url = item.url or "#"
            lines.append(f"### [{item.title}]({url})")
            lines.append(f"**{authors}**" + (f" — {item.venue}" if item.venue else ""))
            lines.append(f"Relevance: {item.relevance_score:.2f}")
            if item.summary:
                lines.append(f"\n{item.summary}")
            lines.append("")

    if on_radar:
        lines.append("## On the Radar\n")
        for item in on_radar[:10]:
            url = item.url or "#"
            lines.append(f"- [{item.title}]({url}) — {item.relevance_score:.2f}")

    # Basic trends from tags
    from collections import Counter

    tag_counter: Counter = Counter()
    for item in items:
        tags = item.tags if isinstance(item.tags, list) else []
        for tag in tags:
            if isinstance(tag, str):
                tag_counter[tag] += 1
    if tag_counter:
        lines.append("\n## Emerging Topics\n")
        for tag, count in tag_counter.most_common(8):
            lines.append(f"- **{tag}** ({count} papers)")

    return "\n".join(lines)


async def _generate_deep_briefing(items: list) -> str:
    """Generate LLM-powered deep briefing with trends, gaps, and research ideas."""
    try:
        from packages.agents.llm import completion

        # Build context from papers
        paper_context = []
        for item in items[:20]:
            abstract = (item.abstract or "")[:300]
            summary = item.summary or ""
            paper_context.append(
                f"- {item.title} ({item.venue or 'unknown venue'}, score={item.relevance_score:.2f})\n"
                f"  Summary: {summary}\n"
                f"  Abstract: {abstract}"
            )

        prompt = "\n".join(paper_context)

        system = """You are a research intelligence analyst. Given the following papers from a researcher's feed, generate a comprehensive briefing with these sections:

## Executive Summary
2-3 sentences: what's happening in this researcher's field right now.

## Key Trends
What themes are accelerating? What's getting more attention? (3-5 trends with evidence from the papers)

## Gaps & Opportunities
What's missing? Where do the papers point to unsolved problems or underexplored areas? (3-5 gaps)

## Research Ideas
Concrete research paper ideas grounded in the gaps above. For each:
- **Title**: proposed paper title
- **Key contribution**: what it would contribute
- **Target venue**: where to submit (RE, ICSE, NeurIPS, COLM, etc.)
- **Grounding**: which papers from the feed motivate this

## What to Watch
Authors, labs, or threads to follow based on this feed.

Be specific and grounded. Every claim should trace to papers in the feed."""

        result = await completion(prompt=prompt, system=system, agent_name="briefing_writer", max_tokens=3000)
        return f"# Deep Research Briefing\n*{datetime.now().strftime('%B %d, %Y')}*\n\n{result.get('content', '')}"

    except Exception as e:
        # Fall back to basic if LLM unavailable
        return _generate_basic_briefing(items, "daily") + f"\n\n---\n*Deep analysis unavailable: {e}*"
