# /eval $ARGUMENTS

Run eval suite for Atlas agents.

## Instructions

If $ARGUMENTS is empty, run all agent evals:
```bash
uv run pytest packages/eval/ -v --tb=short
```

If $ARGUMENTS specifies an agent name, run only that agent's evals:
```bash
uv run pytest packages/eval/ -k "$ARGUMENTS" -v --tb=short
```

Print a summary table of scores per agent. Report any regressions compared to previous runs.
