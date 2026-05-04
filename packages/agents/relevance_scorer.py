"""Relevance scorer agent — scores items against interest profile."""

from __future__ import annotations

import json

from packages.agents.base import run_agent


async def score_relevance(
    title: str,
    abstract: str | None,
    authors: list[str],
    venue: str | None,
    tags: list[str],
    interest_summary: str = "",
) -> dict:
    """Score an item's relevance. Returns {"score": float, "reason": str}."""
    input_text = f"""Item:
Title: {title}
Abstract: {abstract or 'N/A'}
Authors: {', '.join(authors) if authors else 'N/A'}
Venue: {venue or 'N/A'}
Tags: {', '.join(tags) if tags else 'N/A'}

Interest Profile:
{interest_summary or 'No profile available — score based on general academic quality.'}"""

    result = await run_agent("relevance_scorer", input_text)
    content = result.get("content", "")

    # Parse JSON response
    try:
        parsed = json.loads(content)
        return {
            "score": float(parsed.get("score", 0.5)),
            "reason": parsed.get("reason", ""),
            **{k: v for k, v in result.items() if k != "content"},
        }
    except (json.JSONDecodeError, ValueError):
        return {
            "score": 0.5,
            "reason": content[:200],
            **{k: v for k, v in result.items() if k != "content"},
        }
