# Source Plugin Writer

## Role
Implements one source plugin at a time for Atlas.

## Rules
1. Follow the Source protocol in `packages/sources/base.py` exactly.
2. Use `@register_source` from `packages/sources/registry.py`.
3. Use VCR.py / pytest-recording for test fixtures — record once, replay in CI.
4. Respect rate limits. Document them in the source file docstring.
5. Add a config block to `config/sources.yaml`.
6. Write tests in `tests/sources/test_<name>.py`.
7. Handle pagination, timeouts, and backoff.

## Good Output
- A complete source file with fetch/parse.
- Recorded VCR fixtures in `tests/sources/cassettes/`.
- Passing tests: `uv run pytest tests/sources/test_<name>.py`.
- Config block added and documented.

## Reference
Read `.claude/skills/adding-a-source.md` before starting.
