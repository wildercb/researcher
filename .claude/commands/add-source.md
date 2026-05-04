# /add-source $ARGUMENTS

Scaffold a new source plugin for Atlas.

## Instructions

1. Read `.claude/skills/adding-a-source.md` for the full protocol.
2. Create `packages/sources/$ARGUMENTS.py` implementing the `Source` protocol with `@register_source`.
3. Create `tests/sources/test_$ARGUMENTS.py` with test skeleton and VCR fixture setup.
4. Add a config block for `$ARGUMENTS` in `config/sources.yaml`.
5. Run `uv run pytest tests/sources/test_$ARGUMENTS.py` to verify.
