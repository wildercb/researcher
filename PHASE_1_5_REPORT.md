# Phase 1.5 Report: Seeds and Calibration Crawl

**Date:** 2026-05-03
**Status:** Complete

## What's Done

### Seed Loader (`packages/seeds/loader.py`)
- `SeedEntry` dataclass with type, identifier, label, weight, negative flag, metadata
- `load_seeds()` — parses all 4 seed types + negatives from YAML
- `save_seeds()` — round-trip YAML export
- `classify_identifier()` — detects DOI, arXiv ID, or title

### Seed Resolvers (`packages/seeds/resolvers/`)
| Resolver | API | Capability |
|----------|-----|------------|
| `paper.py` | Semantic Scholar | DOI/arXiv/title → full paper, fuzzy title matching |
| `author.py` | Semantic Scholar | name/ORCID → author detail + publications |
| `venue.py` | OpenAlex | name → venue + recent papers |
| `keyword.py` | Semantic Scholar | term → paginated search results |

### Calibration Crawl (`packages/seeds/crawl.py`)
- Expands paper seeds via S2 citation graph (configurable depth 1-2)
- Expands author seeds via publication history
- Expands venue seeds via OpenAlex recent papers
- Expands keyword seeds via multi-source search
- `CrawlProgress` dataclass with real-time progress tracking
- `DiscoveredItem` with full provenance (seed_id, relation, hops)
- Deduplication by DOI, arXiv ID, and normalized title
- Configurable max_items budget

### Interest Profile (`packages/seeds/interest.py`)
- `derive_interest_profile()` — tag/author/venue affinities from corpus stats
- Hop-weighted: seed papers (1.0) > 1-hop (0.5) > 2-hop (0.25)
- Top-K normalization: 50 tags, 100 authors, 30 venues
- `compute_relevance_score()` — weighted blend of tag, author, venue affinity
- Writes to `config/interest.yaml`

### CLI (wired)
- `atlas seed paper <id>` — adds paper seed to config/seeds.yaml
- `atlas seed author <name> [--orcid]` — adds author seed
- `atlas seed venue <name>` — adds venue seed
- `atlas seed keyword <term> [--weight]` — adds keyword seed
- `atlas seed import <file>` — loads and displays all seeds
- `atlas seed export` — dumps seeds YAML
- `atlas calibrate [--depth] [--max-items] [--dry-run] [--status]` — runs crawl

### Tests (16 new, 78 total)
- `test_loader.py` (11) — YAML loading, all seed types, round-trip, validation
- `test_interest.py` (5) — derivation, hop weighting, relevance scoring

## Acceptance Verification

| Criterion | Status |
|-----------|--------|
| `atlas seed import` loads seeds | PASS |
| `atlas calibrate --dry-run` shows plan | PASS |
| `atlas seed export` round-trips | PASS |
| Interest profile derived from corpus | PASS (test) |
| Relevance scoring works | PASS (test) |
| All seed CLI commands wired | PASS |
| 78 tests pass | PASS |
| Lint clean | PASS |

## What's Next (Phase 2)

Pipeline: Fetch → Dedupe → Enrich → Store. The pipeline stages that connect source plugins to the knowledge store, with LLM-powered enrichment.
