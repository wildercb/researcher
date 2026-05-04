# Phase 2 Report: Ingestion Pipeline

**Date:** 2026-05-03
**Status:** Complete

## What's Done

### Pipeline Stages (`packages/pipeline/`)

| Stage | File | Purpose |
|-------|------|---------|
| Fetch | `fetch.py` | Pulls raw items from source, persists to raw_items (idempotent) |
| Parse | `parse.py` | Converts raw items to NormalizedItem via source.parse() |
| Dedupe | `dedupe.py` | DOI → arXiv → source_id match. Creates Mention on duplicate. |
| Store | `store.py` | Creates Item from NormalizedItem |
| Enrich | `enrich.py` | Relevance scoring (interest profile), LLM summarization (optional) |
| Backfill | `backfill.py` | Re-enriches pending/failed items |
| Runner | `runner.py` | Orchestrates full pipeline per source |

### Pipeline Flow
```
Source.fetch() → raw_items (persisted immediately)
     ↓ parse
NormalizedItem
     ↓ dedupe
  Match → Mention (cross-source dedup)
  New → Item (stored)
     ↓ enrich
  Relevance score (from interest profile)
  Summary (LLM, optional)
  enrichment_status = "enriched"
```

### Key Properties
- **Idempotent**: re-running fetch skips existing raw items
- **Resilient**: individual item errors don't stop the pipeline
- **Opportunistic enrichment**: works without LLM API key
- **Backfillable**: `atlas pipeline retry-failed` re-enriches later

### CLI (wired)
- `atlas pipeline run [--source NAME] [--since DATE] [--no-enrich]`
- `atlas pipeline retry-failed [--limit N]`

### Tests (13 new, 91 total)
- `test_dedupe.py` (7) — DOI match, arXiv match, source_id match, mention creation, title hash
- `test_store.py` (2) — item creation, minimal item
- `test_enrich.py` (4) — interest profile scoring, no profile, already enriched, content hash

## Acceptance Verification

| Criterion | Status |
|-----------|--------|
| Pipeline stages chain correctly | PASS |
| Dedupe by DOI/arXiv/source_id | PASS |
| Mentions created for cross-source matches | PASS |
| Enrichment scores relevance from profile | PASS |
| Enrichment graceful when LLM unavailable | PASS |
| Backfill re-enriches failed items | PASS |
| CLI wired | PASS |
| 91 tests pass | PASS |
| Lint clean | PASS |

## What's Next (Phase 3)

Agent runtime: LLM router logging, tool catalog, first agents (relevance_scorer, summarizer, briefing_writer, ideation_agent, fit_agent).
