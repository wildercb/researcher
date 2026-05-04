"""Semantic Scholar source plugin for Atlas.

Uses the Semantic Scholar Graph API to search for papers.

Rate limits:
  - 1 req/s without API key
  - 10 req/s with API key
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime

from packages.sources.base import NormalizedItem, SourceRawItem
from packages.sources.http import RateLimiter, create_client, resilient_get
from packages.sources.registry import register_source

BASE_URL = "https://api.semanticscholar.org/graph/v1"

PAPER_FIELDS = (
    "paperId,title,abstract,authors,venue,year,externalIds,"
    "citationCount,referenceCount,openAccessPdf,publicationDate,fieldsOfStudy"
)

MAX_ITEMS = 1000


@register_source
class SemanticScholarSource:
    name = "semantic_scholar"
    cadence = "0 */6 * * *"

    def __init__(self, config: dict) -> None:
        self.config = config
        self.api_key: str | None = config.get("api_key")
        self.queries: list[str] = config.get("queries", [])
        self.cadence = config.get("cadence", self.cadence)

        rps = 10.0 if self.api_key else 1.0
        self._rate_limiter = RateLimiter(requests_per_second=rps)

    def _headers(self) -> dict[str, str]:
        """Return auth headers if an API key is configured."""
        if self.api_key:
            return {"x-api-key": self.api_key}
        return {}

    async def fetch(self, since: datetime | None = None) -> AsyncIterator[SourceRawItem]:
        """Fetch papers from Semantic Scholar for each configured query."""
        async with create_client() as client:
            for query in self.queries:
                total_fetched = 0
                offset = 0
                limit = 100

                while total_fetched < MAX_ITEMS:
                    params: dict = {
                        "query": query,
                        "offset": offset,
                        "limit": limit,
                        "fields": PAPER_FIELDS,
                    }

                    resp = await resilient_get(
                        client,
                        f"{BASE_URL}/paper/search",
                        rate_limiter=self._rate_limiter,
                        params=params,
                        headers=self._headers(),
                    )
                    data = resp.json()
                    total = data.get("total", 0)
                    papers = data.get("data", [])

                    if not papers:
                        break

                    for paper in papers:
                        pub_date_str = paper.get("publicationDate")
                        if since and pub_date_str:
                            try:
                                pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
                                if pub_date < since:
                                    continue
                            except ValueError:
                                pass

                        yield SourceRawItem(
                            source_id=paper.get("paperId", ""),
                            fetched_at=datetime.now(),
                            payload=paper,
                        )
                        total_fetched += 1

                    offset += limit
                    if offset >= total:
                        break

    def parse(self, item: SourceRawItem) -> NormalizedItem:
        """Parse a Semantic Scholar paper into a NormalizedItem."""
        paper = item.payload

        # Authors
        authors_raw = paper.get("authors") or []
        authors = [a.get("name", "") for a in authors_raw if a.get("name")]

        # External IDs
        external_ids = paper.get("externalIds") or {}
        doi = external_ids.get("DOI")
        arxiv_id = external_ids.get("ArXiv")

        # Published date
        published_at = None
        pub_date_str = paper.get("publicationDate")
        if pub_date_str:
            try:
                published_at = datetime.strptime(pub_date_str, "%Y-%m-%d")
            except ValueError:
                pass

        # PDF URL
        open_access = paper.get("openAccessPdf") or {}
        pdf_url = open_access.get("url")

        # Tags from fields of study
        tags = paper.get("fieldsOfStudy") or []

        paper_id = paper.get("paperId", "")

        return NormalizedItem(
            source=self.name,
            source_id=item.source_id,
            kind="paper",
            title=paper.get("title") or "Untitled",
            abstract=paper.get("abstract"),
            authors=authors,
            venue=paper.get("venue") or None,
            published_at=published_at,
            url=f"https://www.semanticscholar.org/paper/{paper_id}",
            pdf_url=pdf_url,
            doi=doi,
            arxiv_id=arxiv_id,
            tags=tags,
            raw=paper,
        )

    # ------------------------------------------------------------------
    # Phase 1.5 helper methods (not part of the Source protocol)
    # ------------------------------------------------------------------

    async def get_paper(self, paper_id: str) -> dict:
        """Fetch full details for a single paper by ID."""
        async with create_client() as client:
            resp = await resilient_get(
                client,
                f"{BASE_URL}/paper/{paper_id}",
                rate_limiter=self._rate_limiter,
                params={"fields": PAPER_FIELDS},
                headers=self._headers(),
            )
            return resp.json()

    async def get_citations(self, paper_id: str, limit: int = 100) -> list[dict]:
        """Fetch papers that cite the given paper."""
        async with create_client() as client:
            resp = await resilient_get(
                client,
                f"{BASE_URL}/paper/{paper_id}/citations",
                rate_limiter=self._rate_limiter,
                params={"fields": PAPER_FIELDS, "limit": limit},
                headers=self._headers(),
            )
            data = resp.json()
            return data.get("data", [])

    async def get_references(self, paper_id: str, limit: int = 100) -> list[dict]:
        """Fetch papers referenced by the given paper."""
        async with create_client() as client:
            resp = await resilient_get(
                client,
                f"{BASE_URL}/paper/{paper_id}/references",
                rate_limiter=self._rate_limiter,
                params={"fields": PAPER_FIELDS, "limit": limit},
                headers=self._headers(),
            )
            data = resp.json()
            return data.get("data", [])
