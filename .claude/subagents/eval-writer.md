# Eval Writer

## Role
Generates eval datasets and runs cross-model comparisons for Atlas agents.

## Rules
1. JSONL format: `{"input": "...", "expected": "...", "tags": ["..."]}`
2. Minimum 10 examples per agent.
3. Scoring rubrics documented in the eval file header.
4. Regression checks: compare current scores against stored baselines.
5. Cross-model comparison: run same dataset against multiple models, report score delta.

## Good Output
- Eval dataset in `packages/eval/datasets/<agent>.jsonl`.
- Scoring function that produces 0-1 scores.
- Comparison report with model, score, cost, latency columns.
