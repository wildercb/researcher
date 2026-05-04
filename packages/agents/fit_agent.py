"""Fit agent — assesses where a research idea fits in the literature."""

from __future__ import annotations

from packages.agents.base import run_agent


async def assess_fit(
    idea: str,
    related_papers: str,
) -> dict:
    """Assess where an idea fits. Returns {"assessment": str, ...}."""
    input_text = f"""Research idea:
{idea}

Related papers from the corpus:
{related_papers}"""

    result = await run_agent("fit_agent", input_text, max_tokens=2000)
    return {
        "assessment": result.get("content", "").strip(),
        **{k: v for k, v in result.items() if k != "content"},
    }
