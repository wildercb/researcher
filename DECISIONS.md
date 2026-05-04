# Architecture Decision Log

## ADR-001: Python 3.12 via uv
**Date:** 2026-05-03 | **Status:** Accepted

**Context:** System has Python 3.11, spec requires 3.12 for modern type syntax (StrEnum, X | Y unions, etc.).

**Decision:** Use `uv` to download and pin Python 3.12.13. The `.python-version` file pins it project-wide.

**Consequences:** All developers need `uv` installed. CI uses `uv python install 3.12`.

---

## ADR-002: Single pyproject.toml monorepo
**Date:** 2026-05-03 | **Status:** Accepted

**Context:** The project has multiple packages (core, sources, agents, etc.). Could use separate pyproject.toml per package or one for the whole repo.

**Decision:** Single pyproject.toml with `packages/` as namespace packages. All deps in one place.

**Consequences:** Simpler dependency management. All packages share the same virtualenv. Trade-off: can't version packages independently (not needed for a single-deployment project).

---

## ADR-003: sqlite-vec for laptop mode vector search
**Date:** 2026-05-03 | **Status:** Accepted

**Context:** Need vector similarity search in laptop mode without Postgres/pgvector.

**Decision:** Use `sqlite-vec`, the actively maintained SQLite extension for vector operations.

**Consequences:** pip-installable, no system deps. Performance sufficient for <100k vectors. pgvector used in VPS mode for scale.

---

## ADR-004: Click for CLI
**Date:** 2026-05-03 | **Status:** Accepted

**Context:** Need a CLI framework for the `atlas` command.

**Decision:** Click with entry point registration in pyproject.toml (`atlas = "cli.main:cli"`).

**Consequences:** `uv run atlas <command>` works after `uv sync`. Subcommand groups for seed, sources, pipeline.

---

## ADR-005: Single-process laptop mode
**Date:** 2026-05-03 | **Status:** Accepted

**Context:** Laptop mode should be zero-friction. No Docker, no separate processes.

**Decision:** FastAPI + APScheduler + background worker all run in one uvicorn process via `atlas run`.

**Consequences:** Simple startup. Scheduler runs in the event loop. Trade-off: no process isolation, but acceptable for single-user laptop use.

---

## ADR-006: FastAPI serves Next.js static export
**Date:** 2026-05-03 | **Status:** Accepted

**Context:** In production (both laptop and VPS), we need to serve the frontend.

**Decision:** `next build` with `output: "export"` produces static HTML/JS/CSS. FastAPI mounts it as `StaticFiles`. In dev mode, Next.js dev server runs separately.

**Consequences:** No Node.js server needed at runtime. Trade-off: no SSR, but the app is a SPA with API calls — SSR not needed.

---

## ADR-007: Alembic with render_as_batch for SQLite compatibility
**Date:** 2026-05-03 | **Status:** Accepted

**Context:** Same migration chain must work on SQLite (laptop) and Postgres (VPS).

**Decision:** Alembic with `render_as_batch=True` in env.py. This wraps ALTER TABLE operations in batch mode for SQLite compatibility.

**Consequences:** Migrations work on both backends. Some Postgres-specific features (e.g. partial indexes with WHERE) need conditional logic.

---

## ADR-008: LiteLLM as sole LLM abstraction
**Date:** 2026-05-03 | **Status:** Accepted

**Context:** Must be provider-agnostic. Swapping models should be a config change, not a code change.

**Decision:** All LLM calls go through `packages/agents/llm.py` which uses LiteLLM. No provider SDK (openai, anthropic) imported in agent code.

**Consequences:** Model swapping is a one-line config change. LiteLLM handles auth, retries, format translation. Cost tracking via LiteLLM's built-in cost calculation.

---

## ADR-009: JSON columns instead of JSONB
**Date:** 2026-05-03 | **Status:** Accepted

**Context:** SQLAlchemy models need a JSON column type that works on both SQLite and Postgres.

**Decision:** Use `sa.JSON` instead of `postgresql.JSONB`. JSON works on both backends.

**Consequences:** Postgres will still store as JSONB internally. SQLite stores as TEXT. Lose Postgres-specific JSON operators in queries, but can use SQLAlchemy's JSON path accessors.
