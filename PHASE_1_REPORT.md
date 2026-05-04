# Phase 1 Report: Source Plugins

**Date:** 2026-05-03
**Status:** Complete

## What's Done

### Source Plugins (5 implemented)

| Source | File | Tests | Kind | Rate Limit |
|--------|------|-------|------|------------|
| arXiv | `packages/sources/arxiv.py` | 13 | preprint | 1 req/3s |
| OpenAlex | `packages/sources/openalex.py` | 11 | paper | 10 req/s |
| Semantic Scholar | `packages/sources/semantic_scholar.py` | 9 | paper | 1-10 req/s |
| OpenReview | `packages/sources/openreview.py` | 4 | paper | 2 req/s |
| RSS | `packages/sources/rss.py` | 5 | blog/post | 1 req/s/feed |

### Shared Utilities
- `packages/sources/http.py` — RateLimiter, CircuitBreaker, resilient_get with exponential backoff, shared httpx client factory

### Auto-Registration
- `packages/sources/__init__.py` imports all sources → `@register_source` fires on import
- `atlas sources list` shows all 5 sources with enabled/disabled status

### CLI Commands (wired)
- `atlas sources list` — shows registered sources with config status
- `atlas sources test <name>` — fetches and parses items, prints summary
- `atlas sources fetch <name> --since <date> --dry-run` — full fetch with filtering

### Semantic Scholar Extra Methods (for Phase 1.5)
- `get_paper(paper_id)` — fetch single paper
- `get_citations(paper_id)` — fetch citing papers
- `get_references(paper_id)` — fetch referenced papers

### Test Summary
- 62 total tests passing (17 core + 42 source + 3 registry integration)
- All tests use mock data — no real API calls
- Lint clean

## Acceptance Verification

| Criterion | Status |
|-----------|--------|
| `atlas sources list` shows 5 sources | PASS |
| arXiv, OpenAlex, S2, OpenReview, RSS implemented | PASS |
| Each source: fetch + parse + tests | PASS |
| Rate limits documented and enforced | PASS |
| Adding new RSS feed = one config entry | PASS |
| Adding new source type = one new file | PASS |
| 62 tests pass | PASS |
| Lint clean | PASS |

## What Changed from Spec

- OpenAlex function name `reconstruct_abstract` (not prefixed with underscore) — subagent preference, works fine
- Semantic Scholar uses `datetime.strptime` instead of `fromisoformat` for date parsing
- OpenReview handles both new format (content values as `{value: ...}`) and legacy format (content values as strings)

## What's Next (Phase 1.5)

Seeds and calibration crawl: seed importers (paper, author, venue, keyword), citation graph expansion via Semantic Scholar, interest profile derivation.
