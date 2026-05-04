"""Paper seed resolver — resolves DOI, arXiv ID, or title to full paper data."""

from __future__ import annotations

import structlog

from packages.seeds.loader import classify_identifier
from packages.sources.http import RateLimiter, create_client, resilient_get

logger = structlog.get_logger()

S2_API = "https://api.semanticscholar.org/graph/v1"
S2_FIELDS = "paperId,title,abstract,authors,venue,year,externalIds,citationCount,referenceCount,openAccessPdf,publicationDate,fieldsOfStudy"


async def resolve_paper(
    identifier: str,
    api_key: str | None = None,
) -> dict | None:
    """Resolve a paper identifier to full metadata via Semantic Scholar.

    Accepts DOI, arXiv ID, or title string.
    Returns a dict with S2 paper fields, or None if not found.
    """
    kind = classify_identifier(identifier)
    rate_limiter = RateLimiter(requests_per_second=1.0 if not api_key else 10.0)
    headers = {"x-api-key": api_key} if api_key else {}

    async with create_client() as client:
        if kind == "doi":
            return await _resolve_by_id(client, f"DOI:{identifier}", rate_limiter, headers)
        if kind == "arxiv":
            clean_id = identifier.removeprefix("arxiv:")
            return await _resolve_by_id(client, f"ARXIV:{clean_id}", rate_limiter, headers)
        # Title — search
        return await _resolve_by_title(client, identifier, rate_limiter, headers)


async def _resolve_by_id(client, paper_id: str, rate_limiter, headers) -> dict | None:
    try:
        resp = await resilient_get(
            client,
            f"{S2_API}/paper/{paper_id}",
            rate_limiter=rate_limiter,
            params={"fields": S2_FIELDS},
            headers=headers,
        )
        data = resp.json()
        if data.get("paperId"):
            logger.info("paper_resolved", identifier=paper_id, title=data.get("title"))
            return data
    except Exception as e:
        logger.warning("paper_resolve_failed", identifier=paper_id, error=str(e))
    return None


async def _resolve_by_title(client, title: str, rate_limiter, headers) -> dict | None:
    try:
        resp = await resilient_get(
            client,
            f"{S2_API}/paper/search",
            rate_limiter=rate_limiter,
            params={"query": title, "limit": 5, "fields": S2_FIELDS},
            headers=headers,
        )
        data = resp.json()
        papers = data.get("data", [])
        if not papers:
            return None

        # Find best title match
        title_lower = title.lower().strip()
        for paper in papers:
            paper_title = (paper.get("title") or "").lower().strip()
            if _title_similarity(title_lower, paper_title) > 0.8:
                logger.info("paper_resolved_by_title", query=title, title=paper.get("title"))
                return paper

        # Fall back to first result if close enough
        first = papers[0]
        first_title = (first.get("title") or "").lower().strip()
        if _title_similarity(title_lower, first_title) > 0.5:
            logger.info("paper_resolved_by_title_fuzzy", query=title, title=first.get("title"))
            return first

    except Exception as e:
        logger.warning("paper_title_search_failed", title=title, error=str(e))
    return None


def _title_similarity(a: str, b: str) -> float:
    """Simple word-overlap similarity between two titles."""
    words_a = set(a.split())
    words_b = set(b.split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)
