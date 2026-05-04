# Phase 6 Report: Feedback Flywheel

**Date:** 2026-05-04 | **Status:** Complete

### Feedback Loop (`packages/seeds/feedback_loop.py`)
- Computes drift from feedback events (liked/hidden/read/deep_read/more_like_this)
- Signal weights: liked=1.0, more_like_this=1.5, read=0.3, deep_read=0.5, hidden=-1.0
- Drift is bounded (MAX_DRIFT_RATIO=0.3) — feedback shifts but cannot erase seed anchors
- Writes updated profile to config/interest.yaml

### Seed Scout (`packages/agents/seed_scout.py`)
- Finds authors/venues that consistently produce high-relevance items but aren't seeds
- Ignores existing seeds
- Returns ranked proposals with scores

### Tests
- 3 feedback loop tests (positive drift, negative drift, bounded application)
- 3 seed scout tests (frequent author, ignores existing, empty corpus)

Total: 128 tests passing.
