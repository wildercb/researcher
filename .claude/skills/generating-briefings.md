# Generating Research Briefings

## Overview
Atlas generates research briefings in 3 modes, each producing the same comprehensive output format.

## Briefing Format (all modes produce this)

Every briefing includes:
1. **Paper Listings** — Must-Read (>=70% relevance) and On the Radar (40-70%) with authors, venue, date, score, summary
2. **Emerging Topics** — tag frequency analysis
3. **Active Authors** — who's publishing most in your feed
4. **Key Trends** — what's accelerating (3-5 with evidence)
5. **Gaps & Opportunities** — unsolved problems (3-5)
6. **Research Paper Ideas** — concrete ideas with target venues and deadlines
7. **Submission Timeline** — when to submit where
8. **What to Watch** — authors/labs/threads to follow

## Modes

### Basic (no LLM)
- Generates paper listings, topics, authors, venues from data
- Always works, no API key needed
- Missing: trends analysis, gaps, research ideas

### Deep (LLM via Ollama or API)
- Basic listing + LLM analysis of trends, gaps, ideas
- Requires Ollama running or ANTHROPIC_API_KEY/OPENAI_API_KEY
- Uses `packages/agents/prompts/briefing_writer/v1.md` prompt

### Claude Code (you are the LLM)
- Ask Claude Code: "generate a deep briefing"
- Claude Code reads papers via API, writes full analysis, saves via POST /api/briefings/save
- Best quality — uses Claude's full reasoning
- Command: `/generate-briefing`

## Key Files
- `apps/api/routes/briefings.py` — API endpoints
- `packages/agents/prompts/briefing_writer/v1.md` — LLM prompt
- `.claude/commands/generate-briefing.md` — Claude Code command

## API
```
POST /api/briefings/generate {period, mode: "basic"|"deep"|"claude-code"}
POST /api/briefings/save {content, period}
GET  /api/briefings/
```
