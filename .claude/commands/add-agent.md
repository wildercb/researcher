# /add-agent $ARGUMENTS

Scaffold a new agent for Atlas.

## Instructions

1. Read `.claude/skills/adding-an-agent.md` for the full protocol.
2. Create `packages/agents/$ARGUMENTS.py` with agent implementation. All LLM calls through `packages/agents/llm.py`.
3. Create `packages/agents/prompts/$ARGUMENTS/v1.md` with the initial prompt.
4. Create `packages/eval/datasets/$ARGUMENTS.jsonl` with at least 10 eval examples.
5. Create `tests/agents/test_$ARGUMENTS.py` with unit tests.
6. Add model config for `$ARGUMENTS` in `config/models.yaml` under `agents`.
7. Run `uv run pytest tests/agents/test_$ARGUMENTS.py` to verify.
