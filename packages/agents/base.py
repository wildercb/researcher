"""Agent base — prompt loading and agent runner."""

from __future__ import annotations

from pathlib import Path

import structlog

from packages.agents.llm import completion

logger = structlog.get_logger()

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(agent_name: str, version: str = "v1") -> str:
    """Load a versioned prompt file for an agent."""
    path = PROMPTS_DIR / agent_name / f"{version}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text().strip()


def get_prompt_version(agent_name: str) -> str:
    """Get the latest prompt version for an agent."""
    agent_dir = PROMPTS_DIR / agent_name
    if not agent_dir.exists():
        return "v1"
    versions = sorted(
        [f.stem for f in agent_dir.glob("v*.md")],
        key=lambda v: int(v[1:]) if v[1:].isdigit() else 0,
        reverse=True,
    )
    return versions[0] if versions else "v1"


async def run_agent(
    agent_name: str,
    input_text: str,
    version: str | None = None,
    **kwargs,
) -> dict:
    """Run an agent with its versioned prompt.

    Returns dict with: content, model, cost_usd, latency_ms, prompt_version
    """
    ver = version or get_prompt_version(agent_name)
    system_prompt = load_prompt(agent_name, ver)

    result = await completion(
        prompt=input_text,
        system=system_prompt,
        agent_name=agent_name,
        **kwargs,
    )
    result["prompt_version"] = ver
    result["agent_name"] = agent_name

    logger.info(
        "agent_run",
        agent=agent_name,
        version=ver,
        model=result.get("model"),
        cost=result.get("cost_usd"),
    )
    return result
