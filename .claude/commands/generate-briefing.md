# /generate-briefing

Generate a comprehensive deep research briefing using Claude Code's intelligence.

## Instructions

1. Fetch the paper data from the Atlas API:
   ```
   curl -s -X POST "http://localhost:8765/api/briefings/generate" -H "Content-Type: application/json" -d '{"mode":"claude-code"}'
   ```

2. Analyze the returned papers. You have access to titles, abstracts, authors, venues, relevance scores, and summaries.

3. Write a comprehensive briefing with ALL of these sections:
   - **Executive Summary** — 2-3 sentences on the state of the field
   - **Must-Read Papers** — top papers with authors, venue, date, score, and summary (already in basic mode, but add your analytical commentary)
   - **Key Trends** — 3-5 trends with specific paper evidence
   - **Gaps & Research Opportunities** — 3-5 unsolved problems pointed to by the papers
   - **Research Paper Ideas** — 5 concrete ideas with:
     - Proposed title
     - Key contribution
     - Target venue (RE, ICSE, NeurIPS, COLM, FSE, TOSEM, etc.)
     - Estimated deadline
     - Which papers ground this idea
   - **Submission Timeline** — table of venues, deadlines, and matching ideas
   - **What to Watch** — specific authors, labs, threads to follow

4. Save the briefing:
   ```
   curl -s -X POST "http://localhost:8765/api/briefings/save" -H "Content-Type: application/json" -d '{"content": "<your markdown>", "period": "deep-analysis"}'
   ```

5. Confirm it's saved and visible at http://localhost:3000/briefings

The user's research interests: privacy requirements engineering, LLM-based policy compliance, knowledge graphs for regulatory reasoning, AI ethics in software development, privacy by design.
