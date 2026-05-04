"""arXiv source plugin for Atlas.

Uses the arXiv Atom API to fetch preprints by category.

Rate limits:
  - 1 request per 3 seconds (arXiv policy)
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from datetime import datetime

import feedparser

from packages.sources.base import NormalizedItem, SourceRawItem
from packages.sources.http import RateLimiter, create_client, resilient_get
from packages.sources.registry import register_source

ARXIV_API_URL = "http://export.arxiv.org/api/query"
ARXIV_ID_PREFIX = re.compile(r"^https?://arxiv\.org/abs/")
PAGE_SIZE = 100
MAX_RESULTS_CAP = 10000


def _clean_whitespace(text: str | None) -> str | None:
    """Collapse runs of whitespace into single spaces and strip."""
    if text is None:
        return None
    return re.sub(r"\s+", " ", text).strip() or None


def _extract_arxiv_id(entry_id: str) -> str:
    """Strip the URL prefix from an arXiv entry id.

    e.g. "http://arxiv.org/abs/2401.12345v1" -> "2401.12345v1"
    """
    return ARXIV_ID_PREFIX.sub("", entry_id)


@register_source
class ArxivSource:
    name = "arxiv"
    cadence = "0 */6 * * *"

    def __init__(self, config: dict) -> None:
        self.config = config
        self.categories: list[str] = config.get("categories", [])
        self.cadence = config.get("cadence", self.cadence)
        self._rate_limiter = RateLimiter(requests_per_second=1.0 / 3.0)

    async def fetch(self, since: datetime | None = None) -> AsyncIterator[SourceRawItem]:
        """Fetch preprints from arXiv for configured categories."""
        if not self.categories:
            return

        search_query = "+OR+".join(f"cat:{cat}" for cat in self.categories)

        async with create_client() as client:
            start = 0
            while start < MAX_RESULTS_CAP:
                params = {
                    "search_query": search_query,
                    "sortBy": "submittedDate",
                    "sortOrder": "descending",
                    "start": start,
                    "max_results": PAGE_SIZE,
                }
                resp = await resilient_get(
                    client,
                    ARXIV_API_URL,
                    rate_limiter=self._rate_limiter,
                    params=params,
                )
                feed = feedparser.parse(resp.text)
                entries = feed.entries

                if not entries:
                    break

                for entry in entries:
                    # Parse published date
                    published_at = _parse_entry_date(entry)

                    if since and published_at and published_at < since:
                        continue

                    entry_id = entry.get("id", "")
                    arxiv_id = _extract_arxiv_id(entry_id)

                    yield SourceRawItem(
                        source_id=f"arxiv:{arxiv_id}",
                        fetched_at=datetime.now(),
                        payload=_entry_to_dict(entry),
                    )

                if len(entries) < PAGE_SIZE:
                    break
                start += PAGE_SIZE

    def parse(self, item: SourceRawItem) -> NormalizedItem:
        """Parse an arXiv Atom entry into a NormalizedItem."""
        p = item.payload

        title = _clean_whitespace(p.get("title")) or "Untitled"
        abstract = _clean_whitespace(p.get("summary"))

        # Authors
        authors_data = p.get("authors", [])
        authors = []
        for a in authors_data:
            if isinstance(a, dict):
                name = a.get("name", "")
                if name:
                    authors.append(name)
            elif isinstance(a, str):
                authors.append(a)

        # Published date
        published_at = None
        published_str = p.get("published")
        if published_str:
            try:
                published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        # arxiv_id from entry id
        entry_id = p.get("id", "")
        arxiv_id = _extract_arxiv_id(entry_id)

        # URL — use the entry link
        url = p.get("link", entry_id)

        # PDF URL
        pdf_url = None
        links = p.get("links", [])
        for link in links:
            if isinstance(link, dict) and link.get("type") == "application/pdf":
                pdf_url = link.get("href")
                break
        # Fallback: construct from arxiv_id
        if not pdf_url and arxiv_id:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"

        # DOI
        doi = None
        doi_url = p.get("arxiv_doi")
        if doi_url:
            doi = doi_url
        elif p.get("arxiv_doi_url"):
            # Extract DOI from URL like https://doi.org/10.xxxx/yyyy
            doi_match = re.search(r"doi\.org/(.+)", p["arxiv_doi_url"])
            if doi_match:
                doi = doi_match.group(1)

        # Tags from categories
        tags = []
        tags_data = p.get("tags", [])
        for t in tags_data:
            if isinstance(t, dict):
                term = t.get("term", "")
                if term:
                    tags.append(term)
            elif isinstance(t, str):
                tags.append(t)

        return NormalizedItem(
            source=self.name,
            source_id=item.source_id,
            kind="preprint",
            title=title,
            abstract=abstract,
            authors=authors,
            published_at=published_at,
            url=url,
            pdf_url=pdf_url,
            doi=doi,
            arxiv_id=arxiv_id or None,
            tags=tags,
            raw=p,
        )


def _parse_entry_date(entry: dict) -> datetime | None:
    """Parse the published date from a feedparser entry."""
    published_parsed = entry.get("published_parsed")
    if published_parsed and hasattr(published_parsed, "__len__") and len(published_parsed) >= 6:
        try:
            return datetime(*published_parsed[:6])
        except (ValueError, TypeError):
            pass
    published_str = entry.get("published", "")
    if published_str:
        try:
            return datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass
    return None


def _entry_to_dict(entry) -> dict:
    """Convert a feedparser entry to a plain dict for storage."""
    result: dict = {}
    for key in ("id", "title", "summary", "published", "link"):
        if key in entry:
            result[key] = entry[key]
    # Authors
    if "authors" in entry:
        result["authors"] = [
            {"name": a.get("name", "")} if isinstance(a, dict) else {"name": str(a)}
            for a in entry.authors
        ]
    # Links
    if "links" in entry:
        result["links"] = [
            {k: v for k, v in link.items() if isinstance(v, str)}
            for link in entry.links
        ]
    # Tags / categories
    if "tags" in entry:
        result["tags"] = [
            {k: v for k, v in t.items() if isinstance(v, str)}
            for t in entry.tags
        ]
    # DOI fields
    for doi_field in ("arxiv_doi", "arxiv_doi_url"):
        if doi_field in entry:
            result[doi_field] = entry[doi_field]
    return result
