# Testing Strategy

## Test Types

### Unit Tests
Every tool, parser, dedupe rule. Run with:
```bash
uv run pytest tests/ -v
```

### Integration Tests
Pipeline end-to-end with recorded fixtures per source:
```bash
uv run pytest tests/integration/ -v
```

### Property-Based (Hypothesis)
Parsers fuzzed — must never crash:
```bash
uv run pytest tests/ -k hypothesis -v
```

### Agent Evals
Every agent has an eval suite. CI runs against a cheap model; weekly against production model:
```bash
uv run pytest packages/eval/ -v          # all agents
uv run pytest packages/eval/ -k <agent>  # one agent
```

### End-to-End (Playwright)
Critical UI flows:
```bash
cd apps/web && pnpm test:e2e
```

### Load Testing
Synthetic 10k items/day:
```bash
uv run pytest tests/load/ -v
```

## Running All Tests
```bash
make test    # unit + integration
make eval    # agent evals
```

## Adding Tests
- Unit tests go in `tests/` mirroring the package structure
- Integration tests in `tests/integration/`
- Agent evals in `packages/eval/datasets/<agent>.jsonl`
- Playwright tests in `apps/web/tests/`
