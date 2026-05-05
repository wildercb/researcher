"""Briefings API — comprehensive research briefings with paper listings, trends, gaps, ideas."""

from collections import Counter
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
    mode: str = "basic"


@router.post("/generate")
async def generate_briefing(req: GenerateRequest, session: AsyncSession = Depends(get_session)) -> dict:
    result = await session.execute(
        select(Item).where(Item.relevance_score.isnot(None)).order_by(Item.relevance_score.desc()).limit(50)
    )
    items = result.scalars().all()
    if not items:
        return {"error": "No items with relevance scores. Run calibration first."}

    if req.mode == "deep":
        content = await _generate_deep_briefing(items, req.period)
    elif req.mode == "claude-code":
        return _claude_code_payload(items)
    else:
        content = _generate_comprehensive_briefing(items, req.period)

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


def _generate_comprehensive_briefing(items: list, period: str) -> str:
    """Generate a full briefing with paper listings, trends, gaps — no LLM needed."""
    now = datetime.now()
    must_read = [i for i in items if (i.relevance_score or 0) >= 0.7]
    on_radar = [i for i in items if 0.4 <= (i.relevance_score or 0) < 0.7]

    lines = [
        f"# {period.title()} Research Briefing",
        f"*{now.strftime('%B %d, %Y')}* — {len(must_read)} must-read, {len(on_radar)} on-radar\n",
    ]

    # --- Must-Read ---
    if must_read:
        lines.append("## Must-Read Papers\n")
        for item in must_read[:15]:
            authors = ", ".join(item.authors[:3]) if isinstance(item.authors, list) and item.authors else "Unknown"
            extra_authors = f" +{len(item.authors) - 3}" if isinstance(item.authors, list) and len(item.authors) > 3 else ""
            venue = item.venue or "Preprint"
            url = item.url or "#"
            pub = ""
            if item.published_at:
                pub = f" | {item.published_at.strftime('%b %Y')}"
            lines.append(f"### [{item.title}]({url})")
            lines.append(f"**{authors}{extra_authors}** — {venue}{pub} | Relevance: {item.relevance_score:.0%}")
            if item.summary:
                lines.append(f"\n{item.summary}")
            elif item.abstract:
                lines.append(f"\n{item.abstract[:200]}...")
            lines.append("")

    # --- On the Radar ---
    if on_radar:
        lines.append("## On the Radar\n")
        for item in on_radar[:15]:
            venue = item.venue or "Preprint"
            url = item.url or "#"
            score = f"{item.relevance_score:.0%}" if item.relevance_score else ""
            desc = ""
            if item.summary:
                desc = f" — {item.summary[:80]}..."
            lines.append(f"- [{item.title}]({url}) ({venue}, {score}){desc}")
        lines.append("")

    # --- Emerging Topics ---
    tag_counter: Counter = Counter()
    author_counter: Counter = Counter()
    venue_counter: Counter = Counter()
    for item in items:
        for tag in (item.tags if isinstance(item.tags, list) else []):
            if isinstance(tag, str) and tag:
                tag_counter[tag] += 1
        for author in (item.authors if isinstance(item.authors, list) else []):
            if isinstance(author, str) and author:
                author_counter[author] += 1
        if item.venue:
            venue_counter[item.venue] += 1

    if tag_counter:
        lines.append("## Emerging Topics\n")
        for tag, count in tag_counter.most_common(10):
            lines.append(f"- **{tag}** — {count} papers")
        lines.append("")

    # --- Active Authors ---
    if author_counter:
        lines.append("## Most Active Authors\n")
        for author, count in author_counter.most_common(10):
            if count >= 2:
                lines.append(f"- **{author}** — {count} papers")
        lines.append("")

    # --- Active Venues ---
    if venue_counter:
        lines.append("## Top Venues\n")
        for venue, count in venue_counter.most_common(8):
            if count >= 2:
                lines.append(f"- **{venue}** — {count} papers")
        lines.append("")

    # --- Key Observations ---
    lines.append("## Key Observations\n")
    lines.append("*For deeper analysis with research ideas and gap identification, use Deep or Claude Code mode.*\n")

    if must_read:
        top_topics = [t for t, _ in tag_counter.most_common(3)]
        if top_topics:
            lines.append(f"- Dominant themes: {', '.join(top_topics)}")
        lines.append(f"- {len(must_read)} papers scored above 70% relevance to your research interests")
        papers_with_summaries = sum(1 for i in items if i.summary)
        lines.append(f"- {papers_with_summaries}/{len(items)} papers have AI-generated summaries")

    return "\n".join(lines)


async def _generate_deep_briefing(items: list, period: str) -> str:
    """LLM-powered deep analysis on top of the paper listings."""
    # First build the paper listing (always included)
    base = _generate_comprehensive_briefing(items, period)

    try:
        from packages.agents.llm import completion

        paper_context = []
        for item in items[:25]:
            abstract = (item.abstract or "")[:400]
            summary = item.summary or ""
            venue = item.venue or "unknown"
            authors = ", ".join(item.authors[:3]) if isinstance(item.authors, list) else ""
            pub = item.published_at.strftime("%b %Y") if item.published_at else "unknown date"
            paper_context.append(
                f"- [{item.relevance_score:.0%}] {item.title}\n"
                f"  Authors: {authors} | Venue: {venue} | Date: {pub}\n"
                f"  Summary: {summary}\n"
                f"  Abstract excerpt: {abstract}"
            )

        prompt = "\n".join(paper_context)

        result = await completion(prompt=prompt, system=DEEP_BRIEFING_PROMPT, agent_name="briefing_writer", max_tokens=3000)
        analysis = result.get("content", "")

        return base + "\n\n---\n\n" + analysis

    except Exception as e:
        return base + f"\n\n---\n*Deep analysis unavailable ({e}). Switch to Claude Code mode for full analysis.*"


def _claude_code_payload(items: list) -> dict:
    """Return data for Claude Code agent to generate briefing."""
    return {
        "mode": "claude-code",
        "instruction": "Generate a deep research briefing. Include: executive summary, key trends with evidence, gaps in the literature, 5 concrete research paper ideas with target venues and deadlines, and what to watch. Then save via POST /api/briefings/save.",
        "items": [
            {
                "id": i.id,
                "title": i.title,
                "abstract": i.abstract[:500] if i.abstract else None,
                "authors": i.authors[:5] if isinstance(i.authors, list) else [],
                "venue": i.venue,
                "published_at": i.published_at.isoformat() if i.published_at else None,
                "url": i.url,
                "score": round(i.relevance_score or 0, 2),
                "summary": i.summary,
                "tags": i.tags if isinstance(i.tags, list) else [],
            }
            for i in items[:30]
        ],
    }


DEEP_BRIEFING_PROMPT = """You are a research intelligence analyst writing for an active researcher. Given papers from their feed (with relevance scores, venues, dates, summaries, and abstracts), produce ONLY the analysis sections below. The paper listings are already included separately — do NOT repeat them.

## Key Trends
What themes are accelerating? What connects multiple papers? (3-5 trends, cite specific papers as evidence)

## Gaps & Research Opportunities
What problems remain unsolved? Where do papers point to future work? (3-5 gaps, grounded in the papers)

## Research Paper Ideas
5 concrete paper ideas. For each:
- **Title**: proposed paper title
- **Key contribution**: 1-2 sentences on what it would contribute
- **Target venue**: specific venue (RE, ICSE, NeurIPS, COLM, FSE, ACM TOSEM, IEEE Software, etc.)
- **Why now**: what makes this timely based on the papers
- **Grounding**: which 2-3 papers from the feed motivate this

## Submission Timeline
Table of recommended venues with estimated deadlines and which idea fits best.

## What to Watch
Authors, labs, or emerging threads the researcher should follow.

Be specific and grounded. Every claim must trace to papers in the feed. No generic advice."""
