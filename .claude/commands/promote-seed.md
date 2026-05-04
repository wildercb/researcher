# /promote-seed $ARGUMENTS

Promote a high-relevance non-seed to a seed.

## Instructions

1. Parse $ARGUMENTS as an author name or venue name.
2. Search the database for matching entities with high relevance scores.
3. If found, add to `config/seeds.yaml` under the appropriate section (authors or venues).
4. Run `uv run atlas seed <type> "<name>"` to register.
5. Optionally trigger incremental recalibration.
6. Report what was promoted and why (relevance score, hit count).
