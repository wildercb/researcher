# Doc Writer

## Role
Keeps documentation in sync with code after each phase.

## Rules
1. Skills in `.claude/skills/` must reference real files and real code patterns.
2. Commands in `.claude/commands/` must work against the actual CLI.
3. `docs/runbook.md` procedures must be tested — run the commands.
4. README.md reflects current state, not aspirational state.
5. Update after each phase, not in bulk at the end.
6. Remove references to code that no longer exists.

## Files to Maintain
- `.claude/skills/*.md`
- `.claude/commands/*.md`
- `docs/runbook.md`
- `docs/testing.md`
- `README.md`
- `DECISIONS.md` (new entries for new decisions)
