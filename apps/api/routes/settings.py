"""Settings API — model provider configuration."""

from pathlib import Path

import yaml
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/settings", tags=["settings"])

MODELS_PATH = Path("config/models.yaml")

PROVIDERS = {
    "claude-code": {
        "label": "Claude Code (free with subscription)",
        "description": "Uses your Claude Code agent to enrich items via PATCH API. No API key needed.",
        "requires_key": False,
        "key_env": None,
    },
    "ollama": {
        "label": "Ollama (local)",
        "description": "Runs models locally via Ollama. No API key needed. Make sure ollama is running.",
        "requires_key": False,
        "key_env": None,
        "models": ["granite4:micro", "qwen2.5:1.5b", "llama3.1", "mistral"],
    },
    "anthropic": {
        "label": "Anthropic Claude API",
        "description": "Uses Claude models via Anthropic API. Best quality.",
        "requires_key": True,
        "key_env": "ANTHROPIC_API_KEY",
        "models": ["claude-haiku-4-5-20251001", "claude-sonnet-4-20250514"],
    },
    "openai": {
        "label": "OpenAI",
        "description": "Uses GPT models via OpenAI API.",
        "requires_key": True,
        "key_env": "OPENAI_API_KEY",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"],
    },
}


@router.get("/")
async def get_settings() -> dict:
    """Get current model settings and available providers."""
    config = _load_config()
    current_model = config.get("default", {}).get("model", "")

    # Detect current provider
    if current_model.startswith("ollama/"):
        current_provider = "ollama"
    elif current_model.startswith("anthropic/"):
        current_provider = "anthropic"
    elif current_model.startswith("openai/"):
        current_provider = "openai"
    else:
        current_provider = "claude-code"

    return {
        "current_provider": current_provider,
        "current_model": current_model,
        "providers": PROVIDERS,
        "config": config,
    }


class UpdateProviderRequest(BaseModel):
    provider: str  # "claude-code", "ollama", "anthropic", "openai"
    model: str | None = None  # specific model within provider
    api_key: str | None = None  # optional API key to set


@router.post("/provider")
async def update_provider(req: UpdateProviderRequest) -> dict:
    """Switch the LLM provider for all agents."""
    config = _load_config()

    if req.provider == "claude-code":
        # Claude Code mode — use ollama for fallback but mark as claude-code
        model = "ollama/granite4:micro"
        config["_provider_mode"] = "claude-code"
    elif req.provider == "ollama":
        model_name = req.model or "granite4:micro"
        model = f"ollama/{model_name}"
        config.pop("_provider_mode", None)
    elif req.provider == "anthropic":
        model_name = req.model or "claude-haiku-4-5-20251001"
        model = f"anthropic/{model_name}"
        config.pop("_provider_mode", None)
    elif req.provider == "openai":
        model_name = req.model or "gpt-4o-mini"
        model = f"openai/{model_name}"
        config.pop("_provider_mode", None)
    else:
        return {"error": f"Unknown provider: {req.provider}"}

    # Update all agents to use the new model
    config["default"]["model"] = model
    for agent_name in config.get("agents", {}):
        config["agents"][agent_name]["model"] = model
    config["fallback"]["model"] = model

    _save_config(config)

    return {"status": "updated", "provider": req.provider, "model": model}


def _load_config() -> dict:
    if MODELS_PATH.exists():
        with open(MODELS_PATH) as f:
            return yaml.safe_load(f) or {}
    return {}


def _save_config(config: dict) -> None:
    with open(MODELS_PATH, "w") as f:
        f.write("# Atlas LLM model configuration\n")
        f.write("# Updated via Settings UI\n\n")
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
