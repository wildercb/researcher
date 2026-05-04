# /enrich-items

Enrich Atlas items using your own Claude intelligence. You ARE the LLM.

## Instructions

1. Fetch items that need enrichment from the Atlas API:
   ```
   curl -s "http://localhost:8765/api/items/?limit=50"
   ```

2. For each item that has `enrichment_status: "pending"` or no summary:
   - Read the title and abstract
   - Generate a 2-sentence summary (sentence 1: key contribution, sentence 2: method/result)
   - Score relevance 0.0-1.0 based on the user's research interests (privacy engineering, requirements engineering, AI ethics, LLM compliance, knowledge graphs)
   - Write a 1-sentence relevance reason

3. PATCH each item back:
   ```
   curl -s -X PATCH "http://localhost:8765/api/items/{id}" \
     -H "Content-Type: application/json" \
     -d '{"summary": "...", "relevance_score": 0.X, "relevance_reason": "..."}'
   ```

4. Process items in batches of 10-20. Report progress.

The user's research interests are:
- Privacy requirements engineering and privacy by design
- LLM-based policy compliance and knowledge graphs
- AI ethics in software development
- Requirements engineering methods
- Software engineering + AI engineering intersection
