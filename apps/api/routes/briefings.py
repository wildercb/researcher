"""Briefings API — comprehensive research briefings with variety."""

import random
from collections import Counter
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
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
    mode: str = "claude-code"


@router.post("/generate")
async def generate_briefing(
    req: GenerateRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> dict:
    # Get a DIVERSE set of papers — not just top-50 by score every time
    items = await _get_diverse_items(session)
    if not items:
        return {"error": "No items found. Run calibration or pipeline first."}

    base_content = _generate_comprehensive_briefing(items, req.period)
    now = datetime.now()

    if req.mode == "basic":
        content = base_content
    elif req.mode in ("ollama", "api"):
        model_override = _get_api_model() if req.mode == "api" else None
        content = await _generate_llm_analysis(items, req.period, base_content, model_override)
    elif req.mode == "claude-code":
        briefing_id = len(_briefings)
        briefing = {
            "id": briefing_id,
            "period": req.period,
            "mode": "claude-code",
            "content": base_content,
            "created_at": now.isoformat(),
            "must_read_count": sum(1 for i in items if (i.relevance_score or 0) >= 0.7),
            "on_radar_count": sum(1 for i in items if 0.4 <= (i.relevance_score or 0) < 0.7),
            "generating": True,
        }
        _briefings.insert(0, briefing)
        import asyncio
        asyncio.get_event_loop().create_task(
            _background_llm_analysis(briefing_id, items, req.period, base_content)
        )
        return briefing
    else:
        content = base_content

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


# ---------------------------------------------------------------------------
# Diverse paper selection — avoids the "same papers every time" problem
# ---------------------------------------------------------------------------

async def _get_diverse_items(session: AsyncSession) -> list:
    """Get a diverse mix of papers for briefing generation.

    Combines: top by relevance, recent additions, random sample,
    and items not yet featured in a briefing.
    """
    all_items = []
    seen_ids: set[int] = set()

    # 1. Top 15 by relevance (the core must-reads)
    result = await session.execute(
        select(Item).where(Item.relevance_score.isnot(None))
        .order_by(Item.relevance_score.desc()).limit(15)
    )
    for item in result.scalars().all():
        if item.id not in seen_ids:
            all_items.append(item)
            seen_ids.add(item.id)

    # 2. 15 most recently added items (freshness)
    result = await session.execute(
        select(Item).order_by(Item.created_at.desc()).limit(15)
    )
    for item in result.scalars().all():
        if item.id not in seen_ids:
            all_items.append(item)
            seen_ids.add(item.id)

    # 3. 10 random items with summaries (variety)
    result = await session.execute(
        select(Item).where(Item.summary.isnot(None))
        .order_by(func.random()).limit(10)
    )
    for item in result.scalars().all():
        if item.id not in seen_ids:
            all_items.append(item)
            seen_ids.add(item.id)

    # 4. 10 random items WITHOUT summaries (surface new stuff)
    result = await session.execute(
        select(Item).where(Item.summary.is_(None))
        .order_by(func.random()).limit(10)
    )
    for item in result.scalars().all():
        if item.id not in seen_ids:
            all_items.append(item)
            seen_ids.add(item.id)

    # Shuffle the non-top items to vary ordering
    top = all_items[:15]
    rest = all_items[15:]
    random.shuffle(rest)
    return top + rest


# ---------------------------------------------------------------------------
# Paper listing generation
# ---------------------------------------------------------------------------

def _generate_comprehensive_briefing(items: list, period: str) -> str:
    now = datetime.now()
    must_read = [i for i in items if (i.relevance_score or 0) >= 0.7]
    on_radar = [i for i in items if 0.4 <= (i.relevance_score or 0) < 0.7]
    new_items = [i for i in items if not i.summary]

    lines = [
        f"# {period.title()} Research Briefing",
        f"*{now.strftime('%B %d, %Y')}* — {len(must_read)} must-read, {len(on_radar)} on-radar, {len(new_items)} new/unreviewed\n",
    ]

    if must_read:
        lines.append("## Must-Read Papers\n")
        for item in must_read[:15]:
            lines.extend(_format_paper(item))

    if on_radar:
        lines.append("## On the Radar\n")
        for item in on_radar[:15]:
            url = item.url or "#"
            desc = f" — {item.summary[:80]}..." if item.summary else ""
            lines.append(f"- [{item.title}]({url}) ({item.venue or 'Preprint'}, {item.relevance_score:.0%}){desc}")
        lines.append("")

    if new_items:
        lines.append("## New / Unreviewed\n")
        lines.append("*These items haven't been summarized yet. Ask Claude Code to enrich them.*\n")
        for item in new_items[:10]:
            url = item.url or "#"
            venue = item.venue or "unknown"
            abstract_snip = (item.abstract or "")[:100] + "..." if item.abstract else ""
            lines.append(f"- [{item.title}]({url}) ({venue})")
            if abstract_snip:
                lines.append(f"  {abstract_snip}")
        lines.append("")

    # Stats
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
        lines.append("## Topics in This Briefing\n")
        for tag, count in tag_counter.most_common(10):
            lines.append(f"- **{tag}** — {count} papers")
        lines.append("")
    if author_counter:
        lines.append("## Active Authors\n")
        for author, count in author_counter.most_common(10):
            if count >= 2:
                lines.append(f"- **{author}** — {count} papers")
        lines.append("")

    return "\n".join(lines)


def _format_paper(item) -> list[str]:
    lines = []
    authors = ", ".join(item.authors[:3]) if isinstance(item.authors, list) and item.authors else "Unknown"
    extra = f" +{len(item.authors) - 3}" if isinstance(item.authors, list) and len(item.authors) > 3 else ""
    venue = item.venue or "Preprint"
    url = item.url or "#"
    pub = f" | {item.published_at.strftime('%b %Y')}" if item.published_at else ""
    lines.append(f"### [{item.title}]({url})")
    lines.append(f"**{authors}{extra}** — {venue}{pub} | Relevance: {item.relevance_score:.0%}")
    if item.summary:
        lines.append(f"\n{item.summary}")
    elif item.abstract:
        lines.append(f"\n{item.abstract[:250]}...")
    lines.append("")
    return lines


# ---------------------------------------------------------------------------
# LLM analysis
# ---------------------------------------------------------------------------

async def _generate_llm_analysis(items: list, period: str, base_content: str, model_override: str | None = None) -> str:
    try:
        from packages.agents.llm import completion

        paper_context = _build_paper_context(items[:25])
        kwargs = {}
        if model_override:
            kwargs["model"] = model_override

        result = await completion(
            prompt=paper_context,
            system=DEEP_ANALYSIS_PROMPT,
            agent_name="briefing_writer",
            max_tokens=3000,
            **kwargs,
        )
        analysis = result.get("content", "")
        model_used = result.get("model", "unknown")
        return base_content + f"\n\n---\n*Analysis by {model_used}*\n\n{analysis}"

    except Exception as e:
        return base_content + f"\n\n---\n*LLM analysis failed: {e}*"


async def _background_llm_analysis(briefing_id: int, items: list, period: str, base_content: str) -> None:
    try:
        content = await _generate_llm_analysis(items, period, base_content, None)
        for b in _briefings:
            if b.get("id") == briefing_id:
                b["content"] = content
                b["generating"] = False
                break
    except Exception as e:
        for b in _briefings:
            if b.get("id") == briefing_id:
                b["content"] = base_content + f"\n\n---\n*Analysis failed: {e}*"
                b["generating"] = False
                break


def _build_paper_context(items: list) -> str:
    lines = []
    for item in items:
        abstract = (item.abstract or "")[:400]
        summary = item.summary or ""
        venue = item.venue or "unknown"
        authors = ", ".join(item.authors[:3]) if isinstance(item.authors, list) else ""
        pub = item.published_at.strftime("%b %Y") if item.published_at else "unknown date"
        score = f"{item.relevance_score:.0%}" if item.relevance_score else "unscored"
        lines.append(
            f"- [{score}] {item.title}\n"
            f"  Authors: {authors} | Venue: {venue} | Date: {pub}\n"
            f"  Summary: {summary}\n"
            f"  Abstract: {abstract}"
        )
    return "\n".join(lines)


def _get_api_model() -> str | None:
    from pathlib import Path

    import yaml
    path = Path("config/models.yaml")
    if not path.exists():
        return None
    with open(path) as f:
        config = yaml.safe_load(f) or {}
    model = config.get("default", {}).get("model", "")
    if model.startswith("ollama/"):
        return "anthropic/claude-haiku-4-5-20251001"
    return model


DEEP_ANALYSIS_PROMPT = """You are a research intelligence analyst. Given papers from a researcher's feed (with relevance scores, venues, dates, summaries, and abstracts), produce analysis. The paper listings are included separately — focus on ANALYSIS only.

You MUST include ALL of these sections:

## Key Trends
3-5 trends. What's accelerating? What connects multiple papers? Name specific papers as evidence.

## Gaps & Research Opportunities
3-5 gaps. What problems are unsolved? Where do papers call for future work? Each should be specific enough to become a paper.

## Research Paper Ideas
5 concrete ideas. For each:
- **Title**: realistic paper title
- **Key contribution**: 1-2 sentences
- **Target venue**: RE, ICSE, NeurIPS, COLM, FSE, TOSEM, IEEE Software
- **Why now**: what makes this timely
- **Grounding**: 2-3 papers that motivate this

## Submission Timeline
| Venue | Estimated Deadline | Best-fit idea |
Table with at least 5 rows.

## What to Watch
Specific authors, labs, threads to follow. Name names.

Rules: every claim traces to a paper. No generic advice. Be specific."""
