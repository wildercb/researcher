# Phase 4 Report: Living Taxonomy

**Date:** 2026-05-04 | **Status:** Complete

- `packages/pipeline/taxonomy.py` — bootstrap from tag frequencies, classify items against topics, propose new topics for frequent unclassified tags, apply proposals
- Topics are versioned, auto-discovered, not hand-curated
- 4 tests passing

Boring-first: tag-frequency clustering. HDBSCAN on embeddings deferred to when embedding API is wired.
