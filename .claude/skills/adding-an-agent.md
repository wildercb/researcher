# Adding an Agent

## Key Files
- LLM router: `packages/agents/llm.py` (all LLM calls go through here)
- Prompts: `packages/agents/prompts/<agent>/v1.md`
- Evals: `packages/eval/datasets/<agent>.jsonl`
- Model config: `config/models.yaml`

## Steps

### 1. Create agent file
`packages/agents/<name>.py`:
```python
from packages.agents.llm import completion

PROMPT_VERSION = "v1"

async def run(input_text: str, **kwargs) -> dict:
    prompt_path = f"packages/agents/prompts/{AGENT_NAME}/{PROMPT_VERSION}.md"
    with open(prompt_path) as f:
        system_prompt = f.read()

    result = await completion(
        prompt=input_text,
        system=system_prompt,
        agent_name=AGENT_NAME,
    )
    return result
```

Use LangGraph for multi-step graphs, Pydantic AI for typed single-shots.

### 2. Create prompt version file
`packages/agents/prompts/<name>/v1.md` — task-specific instructions. Be precise about the task, not the persona.

### 3. Add model config
In `config/models.yaml`:
```yaml
agents:
  my_agent:
    model: "openai/gpt-4o-mini"
    temperature: 0.3
```

### 4. Create eval dataset
`packages/eval/datasets/<name>.jsonl` — minimum 10 examples:
```jsonl
{"input": "...", "expected": "...", "tags": ["category"]}
```

### 5. Write unit test
`tests/agents/test_<name>.py` — test deterministic scaffolding (prompt loading, tool calls) without LLM.

### 6. Run
```bash
uv run pytest tests/agents/test_<name>.py
uv run pytest packages/eval/ -k <name>
```

## Every agent logs
model, prompt version, input/output tokens, cost_usd, latency_ms via `packages/agents/llm.py`.

## Checklist
- [ ] Agent in `packages/agents/<name>.py`
- [ ] Prompt in `packages/agents/prompts/<name>/v1.md`
- [ ] Eval dataset (>=10 examples) in `packages/eval/datasets/<name>.jsonl`
- [ ] Model config in `config/models.yaml`
- [ ] Unit test in `tests/agents/test_<name>.py`
- [ ] All LLM calls through `packages/agents/llm.py`
