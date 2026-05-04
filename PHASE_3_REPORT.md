# Phase 3 Report: Agent Runtime, Tools, First Agents

**Date:** 2026-05-03
**Status:** Complete

## What's Done

### Agent Base (`packages/agents/base.py`)
- `load_prompt(agent, version)` — loads versioned prompt from `prompts/<agent>/v<N>.md`
- `get_prompt_version(agent)` — finds latest version
- `run_agent(agent, input)` — loads prompt, calls LLM router, returns result with metadata

### Tool Catalog (`packages/agents/tools/`)

| Tool | File | Purpose |
|------|------|---------|
| keyword_search | `search.py` | ILIKE search on title/abstract |
| recent_items | `search.py` | Most recent items |
| top_relevant_items | `search.py` | Highest relevance scores |
| read_item | `lookup.py` | Full item details by ID |
| author_profile | `lookup.py` | Author's papers and venues from corpus |
| topic_trends | `trends.py` | Tag frequency and velocity analysis |
| citation_graph | `graph.py` | Walk citation links |
| record_feedback | `feedback.py` | Store liked/hidden/read signals |
| web_search | `web.py` | DuckDuckGo fallback search |
| fetch_url | `web.py` | Fetch + extract text from URL |

### Agents (6)

| Agent | Prompt | Eval Dataset | Purpose |
|-------|--------|-------------|---------|
| relevance_scorer | v1 | 10 examples | Item → 0-1 score + reason |
| summarizer | v1 | 10 examples | 2-sentence summaries |
| briefing_writer | v1 | 10 examples | Daily/weekly briefings |
| ideation_agent | v1 | — | Research direction generation |
| fit_agent | v1 | — | "Where does my idea fit?" |
| trend_detector | v1 | — | Emerging topic detection |

### Chat Router (`packages/agents/router.py`)
- Intent detection: keyword heuristics → briefing/ideation/fit/trends/general
- Routes to appropriate agent or generic RAG completion
- API wired at `/api/chat`

### Eval Harness (`packages/eval/`)
- `harness.py` — load datasets, run offline validation, score outputs
- `scoring.py` — exact_match, contains_all, contains_any, in_range, word_count_check
- 3 eval datasets (30 total examples)

### Tests (27 new, 118 total)
- `test_base.py` (8) — prompt loading for all 6 agents
- `test_tools.py` (5) — keyword search, read item, feedback
- `test_router.py` (5) — intent detection for all categories
- `test_eval_harness.py` (9) — dataset loading, scoring functions

## Acceptance Verification

| Criterion | Status |
|-----------|--------|
| Prompt loading for all agents | PASS |
| Tool catalog typed and tested | PASS |
| Chat router detects intents correctly | PASS |
| Chat API wired to agent runtime | PASS |
| Eval harness runs offline checks | PASS |
| 3 eval datasets with ≥10 examples each | PASS |
| Model swap = config change only | PASS |
| 118 tests pass | PASS |
| Lint clean | PASS |
