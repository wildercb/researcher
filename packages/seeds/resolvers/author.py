"""Author seed resolver — resolves name/ORCID to author data."""

from __future__ import annotations

import structlog

from packages.sources.http import RateLimiter, create_client, resilient_get

logger = structlog.get_logger()

S2_API = "https://api.semanticscholar.org/graph/v1"


async def resolve_author(
    name: str,
    orcid: str | None = None,
    api_key: str | None = None,
) -> dict | None:
    """Resolve an author by name (and optional ORCID) via Semantic Scholar.

    Returns dict with authorId, name, papers, or None.
    """
    rate_limiter = RateLimiter(requests_per_second=1.0 if not api_key else 10.0)
    headers = {"x-api-key": api_key} if api_key else {}

    async with create_client() as client:
        try:
            resp = await resilient_get(
                client,
                f"{S2_API}/author/search",
                rate_limiter=rate_limiter,
                params={"query": name, "limit": 10},
                headers=headers,
            )
            data = resp.json()
            authors = data.get("data", [])
            if not authors:
                return None

            # If ORCID provided, try to match
            if orcid:
                for a in authors:
                    author_detail = await _get_author_detail(
                        client, a["authorId"], rate_limiter, headers
                    )
                    if author_detail and author_detail.get("externalIds", {}).get("ORCID") == orcid:
                        return author_detail

            # Return the first match with papers
            for a in authors:
                detail = await _get_author_detail(client, a["authorId"], rate_limiter, headers)
                if detail and detail.get("paperCount", 0) > 0:
                    logger.info("author_resolved", name=name, author_id=a["authorId"])
                    return detail

            return None
        except Exception as e:
            logger.warning("author_resolve_failed", name=name, error=str(e))
            return None


async def _get_author_detail(client, author_id: str, rate_limiter, headers) -> dict | None:
    try:
        resp = await resilient_get(
            client,
            f"{S2_API}/author/{author_id}",
            rate_limiter=rate_limiter,
            params={"fields": "authorId,name,paperCount,citationCount,hIndex,papers.paperId,papers.title,papers.year,externalIds"},
            headers=headers,
        )
        return resp.json()
    except Exception:
        return None
