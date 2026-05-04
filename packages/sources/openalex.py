"""OpenAlex source plugin for Atlas.

Uses the OpenAlex REST API to fetch academic works.

Rate limits:
  - 10 req/s with polite pool (User-Agent with mailto:)
  - No auth required
  - API: REST at https://api.openalex.org/works
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime

from packages.sources.base import NormalizedItem, SourceRawItem
from packages.sources.http import RateLimiter, create_client, resilient_get
from packages.sources.registry import register_source

OPENALEX_API = "https://api.openalex.org/works"
MAX_ITEMS = 5000
PER_PAGE = 200


def reconstruct_abstract(inverted_index: dict | None) -> str | None:
    """Reconstruct abstract from OpenAlex inverted index format.

    Format: {"word": [position1, position2, ...], ...}
    We invert this to [(position, word), ...], sort by position, and join.
    """
    if not inverted_index:
        return None
    word_positions: list[tuple[int, str]] = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort(key=lambda x: x[0])
    return " ".join(word for _, word in word_positions) if word_positions else None


@register_source
class OpenAlexSource:
    name = "openalex"
    cadence = "0 */6 * * *"

    def __init__(self, config: dict) -> None:
        self.config = config
        self.mailto: str = config.get("mailto", "atlas@localhost")
        self.cadence = config.get("cadence", self.cadence)
        self._rate_limiter = RateLimiter(requests_per_second=10.0)

    async def fetch(self, since: datetime | None = None) -> AsyncIterator[SourceRawItem]:
        """Fetch works from OpenAlex with cursor-based pagination."""
        user_agent = f"Atlas/0.1.0 (mailto:{self.mailto})"
        async with create_client(headers={"User-Agent": user_agent}) as client:
            cursor = "*"
            total_fetched = 0

            while cursor and total_fetched < MAX_ITEMS:
                params: dict = {
                    "per_page": PER_PAGE,
                    "cursor": cursor,
                }
                if since:
                    params["filter"] = f"from_created_date:{since.strftime('%Y-%m-%d')}"

                resp = await resilient_get(
                    client,
                    OPENALEX_API,
                    rate_limiter=self._rate_limiter,
                    params=params,
                )
                data = resp.json()
                results = data.get("results", [])
                if not results:
                    break

                for work in results:
                    yield SourceRawItem(
                        source_id=work.get("id", ""),
                        fetched_at=datetime.now(),
                        payload=work,
                    )
                    total_fetched += 1
                    if total_fetched >= MAX_ITEMS:
                        break

                next_cursor = data.get("meta", {}).get("next_cursor")
                if not next_cursor:
                    break
                cursor = next_cursor

    def parse(self, item: SourceRawItem) -> NormalizedItem:
        """Parse an OpenAlex work into a NormalizedItem."""
        w = item.payload

        # Title
        title = w.get("display_name") or "Untitled"

        # Abstract from inverted index
        abstract = reconstruct_abstract(w.get("abstract_inverted_index"))

        # Authors and affiliations
        authors: list[str] = []
        affiliations: list[str] = []
        seen_affiliations: set[str] = set()
        for authorship in w.get("authorships", []):
            author = authorship.get("author", {})
            name = author.get("display_name", "")
            if name:
                authors.append(name)
            for inst in authorship.get("institutions", []):
                aff = inst.get("display_name", "")
                if aff and aff not in seen_affiliations:
                    affiliations.append(aff)
                    seen_affiliations.add(aff)

        # DOI — strip prefix
        doi_raw = w.get("doi", "")
        doi: str | None = None
        if doi_raw:
            doi = doi_raw.replace("https://doi.org/", "").strip() or None

        # Venue
        primary_loc = w.get("primary_location") or {}
        source_info = primary_loc.get("source") or {}
        venue = source_info.get("display_name")

        # Published date
        published_at: datetime | None = None
        pub_date = w.get("publication_date", "")
        if pub_date:
            try:
                published_at = datetime.fromisoformat(pub_date)
            except (ValueError, TypeError):
                pass

        # URL: prefer DOI, fall back to OpenAlex ID
        url = doi_raw or w.get("id", "")

        # PDF URL
        pdf_url = primary_loc.get("pdf_url")
        if not pdf_url:
            oa = w.get("open_access") or {}
            pdf_url = oa.get("oa_url")

        # Citations (referenced works — list of OpenAlex IDs)
        citations: list[str] = w.get("referenced_works", [])

        # Tags from concepts, top 5 by score
        concepts = w.get("concepts", [])
        concepts_sorted = sorted(concepts, key=lambda c: c.get("score", 0), reverse=True)
        tags = [c.get("display_name", "") for c in concepts_sorted[:5] if c.get("display_name")]

        return NormalizedItem(
            source=self.name,
            source_id=item.source_id,
            kind="paper",
            title=title,
            abstract=abstract,
            authors=authors,
            affiliations=affiliations,
            venue=venue,
            published_at=published_at,
            url=url,
            pdf_url=pdf_url,
            doi=doi,
            citations=citations,
            tags=tags,
            raw=w,
        )
