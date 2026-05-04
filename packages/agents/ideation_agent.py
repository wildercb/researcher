"""Ideation agent — generates research directions from corpus."""

from __future__ import annotations

from packages.agents.base import run_agent


async def generate_ideas(
    context_papers: str,
    focus: str | None = None,
) -> dict:
    """Generate research ideas. Returns {"ideas": str, ...}."""
    input_text = f"""Based on these papers from the corpus:

{context_papers}"""

    if focus:
        input_text += f"\n\nFocus area: {focus}"

    result = await run_agent("ideation_agent", input_text, max_tokens=2000)
    return {
        "ideas": result.get("content", "").strip(),
        **{k: v for k, v in result.items() if k != "content"},
    }
