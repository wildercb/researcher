"""LLM router — all model calls go through here via LiteLLM.

No provider SDK should be imported in agent code.
This module handles: model selection, cost tracking, fallback, logging.
"""

from __future__ import annotations

import time
from typing import Any

import structlog
import yaml

logger = structlog.get_logger()


def _load_models_config(config_path: str = "config/models.yaml") -> dict[str, Any]:
    with open(config_path) as f:
        return yaml.safe_load(f)


async def completion(
    prompt: str,
    agent_name: str | None = None,
    system: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    config_path: str = "config/models.yaml",
    **kwargs: Any,
) -> dict[str, Any]:
    """Make an LLM completion call through LiteLLM.

    Resolves model from: explicit param > agent config > global default.
    Logs cost, latency, tokens to structured log (and agent_runs table in Phase 3).
    """
    import litellm

    config = _load_models_config(config_path)

    # Resolve model
    if model is None:
        if agent_name and agent_name in config.get("agents", {}):
            agent_config = config["agents"][agent_name]
            model = agent_config.get("model", config["default"]["model"])
            if temperature is None:
                temperature = agent_config.get("temperature")
        else:
            model = config["default"]["model"]

    if temperature is None:
        temperature = config["default"].get("temperature", 0.3)
    if max_tokens is None:
        max_tokens = config["default"].get("max_tokens", 4096)

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    start = time.monotonic()
    try:
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        latency_ms = int((time.monotonic() - start) * 1000)

        usage = response.usage
        cost = litellm.completion_cost(completion_response=response)

        logger.info(
            "llm_call",
            agent=agent_name,
            model=model,
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
        )

        return {
            "content": response.choices[0].message.content,
            "model": model,
            "input_tokens": usage.prompt_tokens,
            "output_tokens": usage.completion_tokens,
            "cost_usd": cost,
            "latency_ms": latency_ms,
        }
    except Exception as e:
        latency_ms = int((time.monotonic() - start) * 1000)
        logger.error("llm_call_failed", agent=agent_name, model=model, error=str(e))

        # Try fallback
        fallback_config = config.get("fallback", {})
        if fallback_config.get("enabled") and model != fallback_config.get("model"):
            logger.info("llm_fallback", original_model=model, fallback=fallback_config["model"])
            return await completion(
                prompt=prompt,
                agent_name=agent_name,
                system=system,
                model=fallback_config["model"],
                temperature=temperature,
                max_tokens=max_tokens,
                config_path=config_path,
                **kwargs,
            )
        raise


async def embed(
    texts: list[str],
    config_path: str = "config/models.yaml",
) -> list[list[float]]:
    """Embed texts through LiteLLM."""
    import litellm

    config = _load_models_config(config_path)
    embedding_config = config.get("embedding", {})
    model = embedding_config.get("model", "openai/text-embedding-3-small")

    start = time.monotonic()
    response = await litellm.aembedding(model=model, input=texts)
    latency_ms = int((time.monotonic() - start) * 1000)

    logger.info(
        "embedding_call",
        model=model,
        num_texts=len(texts),
        latency_ms=latency_ms,
    )

    return [item["embedding"] for item in response.data]
