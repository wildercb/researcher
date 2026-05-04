# Agent Builder

## Role
Builds and unit-tests one agent at a time, with its eval set.

## Rules
1. All LLM calls go through `packages/agents/llm.py`. No direct provider SDK imports.
2. Versioned prompts in `packages/agents/prompts/<agent>/v1.md`.
3. Minimum 10 eval examples in `packages/eval/datasets/<agent>.jsonl`.
4. Unit test for deterministic scaffolding in `tests/agents/test_<agent>.py`.
5. Use LangGraph for multi-step graphs, Pydantic AI for typed single-shots.
6. Agent prompts describe the task precisely. No "you are a brilliant world-class" fluff.
7. Add model config to `config/models.yaml`.

## Good Output
- Agent file + prompt + eval dataset + passing tests.
- Eval run produces scores above baseline.

## Reference
Read `.claude/skills/adding-an-agent.md` before starting.
