"""Chat router — routes user messages to appropriate agents."""

from __future__ import annotations

import structlog

from packages.agents.base import run_agent
from packages.agents.llm import completion

logger = structlog.get_logger()

# Intent detection keywords
BRIEFING_KEYWORDS = {"briefing", "brief", "update", "digest", "summary of recent", "what's new"}
IDEATION_KEYWORDS = {"idea", "research direction", "what should i work on", "explore", "brainstorm"}
FIT_KEYWORDS = {"where does", "how does", "fit", "novelty", "novel", "prior work", "related work"}
TREND_KEYWORDS = {"trend", "trending", "emerging", "what's hot", "accelerating"}


def detect_intent(message: str) -> str:
    """Detect intent from user message using keyword heuristics.

    Returns: "briefing", "ideation", "fit", "trends", or "general"
    """
    msg_lower = message.lower()

    for kw in BRIEFING_KEYWORDS:
        if kw in msg_lower:
            return "briefing"

    for kw in FIT_KEYWORDS:
        if kw in msg_lower:
            return "fit"

    for kw in IDEATION_KEYWORDS:
        if kw in msg_lower:
            return "ideation"

    for kw in TREND_KEYWORDS:
        if kw in msg_lower:
            return "trends"

    return "general"


async def route_message(
    message: str,
    context: str = "",
) -> dict:
    """Route a user message to the appropriate agent.

    Returns dict with: response, agent_used, intent, cost_usd, etc.
    """
    intent = detect_intent(message)
    logger.info("chat_routed", intent=intent, message_preview=message[:50])

    if intent == "briefing":
        result = await run_agent("briefing_writer", message)
    elif intent == "ideation":
        result = await run_agent("ideation_agent", f"{message}\n\nContext:\n{context}")
    elif intent == "fit":
        result = await run_agent("fit_agent", f"{message}\n\nRelated papers:\n{context}")
    elif intent == "trends":
        result = await run_agent("trend_detector", message)
    else:
        # General RAG: just use completion with context
        system = "You are Atlas, a research intelligence assistant. Answer the user's question using the provided research context. Cite specific papers when possible. Be concise and factual."
        result = await completion(
            prompt=f"{message}\n\nContext:\n{context}" if context else message,
            system=system,
            agent_name="general",
        )

    return {
        "response": result.get("content", ""),
        "agent_used": result.get("agent_name", intent),
        "intent": intent,
        "model": result.get("model"),
        "cost_usd": result.get("cost_usd", 0),
        "latency_ms": result.get("latency_ms", 0),
        "prompt_version": result.get("prompt_version"),
    }
