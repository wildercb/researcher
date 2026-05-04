"""Keyword seed resolver — searches sources for matching items."""

from __future__ import annotations

import structlog

from packages.sources.http import RateLimiter, create_client, resilient_get

logger = structlog.get_logger()

S2_API = "https://api.semanticscholar.org/graph/v1"
S2_FIELDS = "paperId,title,abstract,authors,venue,year,externalIds,publicationDate,fieldsOfStudy"


async def resolve_keyword(
    term: str,
    limit: int = 100,
    api_key: str | None = None,
) -> list[dict]:
    """Search Semantic Scholar for papers matching a keyword.

    Returns list of paper dicts.
    """
    rate_limiter = RateLimiter(requests_per_second=1.0 if not api_key else 10.0)
    headers = {"x-api-key": api_key} if api_key else {}

    results: list[dict] = []
    async with create_client() as client:
        try:
            offset = 0
            per_page = min(limit, 100)
            while len(results) < limit:
                resp = await resilient_get(
                    client,
                    f"{S2_API}/paper/search",
                    rate_limiter=rate_limiter,
                    params={
                        "query": term,
                        "offset": offset,
                        "limit": per_page,
                        "fields": S2_FIELDS,
                    },
                    headers=headers,
                )
                data = resp.json()
                papers = data.get("data", [])
                if not papers:
                    break
                results.extend(papers)
                offset += per_page
                if offset >= data.get("total", 0):
                    break

            logger.info("keyword_resolved", term=term, count=len(results))
        except Exception as e:
            logger.warning("keyword_resolve_failed", term=term, error=str(e))

    return results[:limit]
