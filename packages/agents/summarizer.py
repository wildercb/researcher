"""Summarizer agent — 2-sentence paper summaries."""

from __future__ import annotations

from packages.agents.base import run_agent


async def summarize(title: str, abstract: str) -> dict:
    """Summarize a paper in 2 sentences. Returns {"summary": str, ...}."""
    input_text = f"Title: {title}\n\nAbstract: {abstract}"

    result = await run_agent("summarizer", input_text, max_tokens=200)
    return {
        "summary": result.get("content", "").strip(),
        **{k: v for k, v in result.items() if k != "content"},
    }
