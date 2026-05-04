"""Briefing writer agent — generates daily/weekly research briefings."""

from __future__ import annotations

from packages.agents.base import run_agent


async def write_briefing(
    items_summary: str,
    period: str = "daily",
) -> dict:
    """Generate a research briefing. Returns {"briefing": str, ...}."""
    input_text = f"""Generate a {period} research briefing from these items:

{items_summary}"""

    result = await run_agent("briefing_writer", input_text, max_tokens=2000)
    return {
        "briefing": result.get("content", "").strip(),
        "period": period,
        **{k: v for k, v in result.items() if k != "content"},
    }


def format_items_for_briefing(items: list[dict]) -> str:
    """Format item dicts into text for the briefing prompt."""
    lines = []
    for item in items:
        line = f"- [{item.get('kind', 'paper')}] {item['title']}"
        if item.get("authors"):
            authors = item["authors"][:3]
            line += f" by {', '.join(authors)}"
        if item.get("venue"):
            line += f" ({item['venue']})"
        if item.get("relevance_score"):
            line += f" [relevance: {item['relevance_score']:.2f}]"
        if item.get("url"):
            line += f"\n  URL: {item['url']}"
        if item.get("summary"):
            line += f"\n  Summary: {item['summary']}"
        lines.append(line)
    return "\n".join(lines)
