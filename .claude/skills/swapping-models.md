# Swapping Models

## Key Files
- Model config: `config/models.yaml`
- LLM router: `packages/agents/llm.py`
- Eval harness: `packages/eval/`

## How models are configured

`config/models.yaml`:
```yaml
default:
  model: "openai/gpt-4o-mini"
  temperature: 0.3
  max_tokens: 4096

agents:
  summarizer:
    model: "openai/gpt-4o-mini"
    temperature: 0.3
  ideation_agent:
    model: "openai/gpt-4o"
    temperature: 0.7

embedding:
  model: "openai/text-embedding-3-small"

fallback:
  enabled: true
  model: "openai/gpt-4o-mini"
```

Resolution order: explicit param > agent config > global default.

## LiteLLM model format
`"provider/model-name"` — examples:
- `openai/gpt-4o`, `openai/gpt-4o-mini`
- `anthropic/claude-sonnet-4-20250514`
- `ollama/llama3` (local)

## To swap a model

1. Edit `config/models.yaml` — change the model string
2. Run evals: `make eval`
3. Compare scores before/after
4. If no regressions, commit the change

## Cost tracking
Every call logged in `agent_runs` table with cost_usd. Daily cap in `config/models.yaml` under `daily_cost_cap_usd`.

## Fallback
If primary model fails, LLM router falls back to `fallback.model` automatically (if `fallback.enabled: true`).
