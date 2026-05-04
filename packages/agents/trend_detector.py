"""Trend detector agent — identifies emerging research topics."""

from __future__ import annotations

from packages.agents.base import run_agent


async def detect_trends(trends_data: str) -> dict:
    """Analyze topic trends. Returns {"analysis": str, ...}."""
    result = await run_agent("trend_detector", trends_data, max_tokens=1500)
    return {
        "analysis": result.get("content", "").strip(),
        **{k: v for k, v in result.items() if k != "content"},
    }


def format_trends_for_prompt(trends: list[dict]) -> str:
    """Format trend data for the prompt."""
    lines = ["Topic | Total Count | Recent (7d) | Velocity"]
    lines.append("---|---|---|---")
    for t in trends:
        lines.append(
            f"{t['topic']} | {t['count']} | {t['recent_count']} | {t['velocity']:.3f}"
        )
    return "\n".join(lines)
