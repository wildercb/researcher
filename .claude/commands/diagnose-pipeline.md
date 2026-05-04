# /diagnose-pipeline

Report pipeline health for Atlas.

## Instructions

1. Query the database for pipeline status:
   - Last successful fetch per source
   - Items ingested in the last 24h per source
   - Dead letter count (enrichment_status = 'failed')
   - Dedupe hit rate (mentions vs items created)
2. Format as a table showing: Source | Last Run | Items (24h) | Dead Letters | Status
3. Flag any source with no activity in >24h as "stale".
4. Report overall pipeline health.

Use `uv run atlas pipeline status` when available, or query the database directly.
