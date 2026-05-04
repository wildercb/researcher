# Phase 0 Report: Repo Skeleton, Harness, and Dual-Mode Foundation

**Date:** 2026-05-03
**Status:** Complete

## What's Done

### Monorepo Structure
- Full directory layout: `apps/`, `packages/`, `infra/`, `migrations/`, `scripts/`, `tests/`, `docs/`, `config/`, `cli/`, `.claude/`
- Python 3.12 via uv with single `pyproject.toml`
- pnpm workspace for Next.js frontend

### Core Packages (`packages/core/`)
- `config.py` — pydantic-settings with ATLAS_MODE env var, dual-mode database URL resolution
- `types.py` — StrEnum types: AtlasMode, ItemKind, SeedType, FeedbackSignal, EnrichmentStatus
- `models.py` — 14 SQLAlchemy models: Item, RawItem, Mention, Author, Venue, Topic, ItemTopic, Citation, Seed, SeedProvenance, FeedbackEvent, AgentRun, PromptVersion
- `storage.py` — Storage protocol + SQLiteStorage + PostgresStorage implementations
- `scheduler.py` — Scheduler protocol + APSchedulerBackend + PrefectBackend (stub)

### Source Protocol (`packages/sources/`)
- `base.py` — Source protocol, SourceRawItem, NormalizedItem Pydantic models
- `registry.py` — `@register_source` decorator with `get_source()`, `list_sources()`

### LLM Router (`packages/agents/llm.py`)
- LiteLLM-based completion and embedding with model resolution from config
- Cost tracking, latency logging, automatic fallback

### CLI (`cli/main.py`)
- Click-based with `atlas` entry point
- Commands: run, seed (paper/author/venue/keyword/import/export), calibrate, sources (list/test/fetch), pipeline (run/retry-failed), export, import
- All Phase 1+ commands are stubs with clear messages

### FastAPI API (`apps/api/`)
- App factory with lifespan (storage init, scheduler start/stop)
- Routes: /api/health, /api/items, /api/chat, /api/seeds, /api/sources
- CORS configured for dev
- Static file mount for frontend

### Frontend (`apps/web/`)
- Next.js 14, App Router, TypeScript, Tailwind
- Sidebar with icons (lucide-react): Chat, Briefings, Trends, Seeds, Reading List, Eval
- Chat page with message UI, input, loading animation
- Placeholder pages for all routes
- Static export builds to `out/` for FastAPI serving
- Mobile responsive sidebar with toggle

### Infrastructure
- `Makefile` with targets: laptop-setup, vps-deploy, dev, test, eval, migrate, seed-demo, lint, typecheck, fmt, clean
- `infra/Dockerfile` — multi-stage (python-deps, node-deps, build-web, runtime)
- `infra/docker-compose.yml` — caddy, postgres, api, web, worker, prefect services
- `infra/Caddyfile` — reverse proxy config
- `scripts/laptop-setup.sh` + `scripts/vps-deploy.sh`
- `.pre-commit-config.yaml` — ruff, pre-commit-hooks, mypy, detect-secrets

### Claude Harness
- **Skills (3):** adding-a-source, adding-an-agent, swapping-models
- **Commands (8):** add-source, add-agent, seed, eval, swap-model, diagnose-pipeline, recalibrate, promote-seed
- **Subagent Personas (7):** source-plugin-writer, agent-builder, ui-builder, eval-writer, code-reviewer, doc-writer, integration-tester

### Migrations
- Alembic configured with `render_as_batch=True` for SQLite compatibility
- Initial migration creates all 14 tables

### Tests (17 passing)
- `test_config.py` (6) — mode selection, database URL resolution, config paths
- `test_storage.py` (6) — CRUD operations, rollback, storage factory
- `test_scheduler.py` (5) — backend selection, start/stop, job add/remove

### Documentation
- `README.md` — quick start, architecture, tech stack, CLI, extending
- `DECISIONS.md` — 9 ADRs
- `docs/testing.md` — test strategy
- `docs/runbook.md` — operational procedures

## Acceptance Verification

| Criterion | Status |
|-----------|--------|
| `atlas run` starts at :8765 | PASS |
| Health endpoint returns OK | PASS — `{"status":"ok","mode":"laptop","version":"0.1.0"}` |
| Frontend loads | PASS — full HTML with sidebar, chat UI |
| API routes respond | PASS — /api/health, /api/items, /api/seeds, /api/sources |
| 17 tests pass | PASS |
| ruff lint clean | PASS |
| .claude/ harness populated | PASS — 3 skills, 8 commands, 7 subagents |

## What Changed from Spec

- Used `sa.JSON` instead of `postgresql.JSONB` for dual-mode compatibility (ADR-009)
- Disabled ruff TC rules (type-checking block) — runtime imports needed for Pydantic/SQLAlchemy
- Disabled ruff B008 — `Depends()` in FastAPI defaults is idiomatic
- PrefectBackend is a stub (no-op) — full implementation in Phase 2

## What's Flaky

- Nothing. All tests deterministic. All endpoints respond.

## What's Next (Phase 1)

Source plugins: arXiv, OpenAlex, Semantic Scholar, OpenReview, Generic RSS. Each implemented by a source-plugin-writer subagent in parallel.
