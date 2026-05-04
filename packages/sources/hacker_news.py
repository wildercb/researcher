"""Hacker News source plugin for Atlas.

Uses the Algolia HN Search API to find research-relevant posts.
Filters by domain whitelist to focus on academic/research links.

Rate limits:
  - 10 req/s (generous, Algolia is fast)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
from urllib.parse import urlparse

from packages.sources.base import NormalizedItem, SourceRawItem
from packages.sources.http import RateLimiter, create_client, resilient_get
from packages.sources.registry import register_source

HN_API = "https://hn.algolia.com/api/v1"


@register_source
class HackerNewsSource:
    name = "hacker_news"
    cadence = "0 */4 * * *"

    def __init__(self, config: dict) -> None:
        self.config = config
        self.domain_whitelist: list[str] = config.get("domain_whitelist", [])
        self.cadence = config.get("cadence", self.cadence)
        self._rate_limiter = RateLimiter(requests_per_second=5.0)

    async def fetch(self, since: datetime | None = None) -> AsyncIterator[SourceRawItem]:
        """Fetch stories from HN Algolia API, filtered by domain whitelist."""
        async with create_client() as client:
            page = 0
            while page < 5:
                params: dict = {
                    "tags": "story",
                    "hitsPerPage": 50,
                    "page": page,
                }
                if since:
                    params["numericFilters"] = f"created_at_i>{int(since.timestamp())}"

                resp = await resilient_get(
                    client,
                    f"{HN_API}/search_by_date",
                    rate_limiter=self._rate_limiter,
                    params=params,
                )
                data = resp.json()
                hits = data.get("hits", [])
                if not hits:
                    break

                for hit in hits:
                    url = hit.get("url", "")
                    if self.domain_whitelist and not _matches_whitelist(url, self.domain_whitelist):
                        continue

                    yield SourceRawItem(
                        source_id=f"hn:{hit.get('objectID', '')}",
                        fetched_at=datetime.now(),
                        payload=hit,
                    )

                page += 1
                if page >= data.get("nbPages", 0):
                    break

    def parse(self, item: SourceRawItem) -> NormalizedItem:
        """Parse an HN story into a NormalizedItem."""
        h = item.payload
        title = h.get("title", "Untitled")
        url = h.get("url", "")
        if not url:
            url = f"https://news.ycombinator.com/item?id={h.get('objectID', '')}"

        author = h.get("author", "")
        points = h.get("points", 0)
        comments = h.get("num_comments", 0)

        created_at = None
        ts = h.get("created_at_i")
        if ts:
            created_at = datetime.fromtimestamp(ts)

        return NormalizedItem(
            source=self.name,
            source_id=item.source_id,
            kind="post",
            title=title,
            abstract=f"{points} points, {comments} comments on Hacker News",
            authors=[author] if author else [],
            venue="Hacker News",
            published_at=created_at,
            url=url,
            tags=_extract_tags(title, url),
            raw=h,
        )


def _matches_whitelist(url: str, whitelist: list[str]) -> bool:
    """Check if URL domain matches any whitelist entry."""
    if not url:
        return False
    try:
        domain = urlparse(url).netloc.lower()
        return any(w.lower() in domain for w in whitelist)
    except Exception:
        return False


def _extract_tags(title: str, url: str) -> list[str]:
    """Extract basic tags from title and URL."""
    tags = []
    title_lower = title.lower()
    if "arxiv" in url.lower():
        tags.append("arxiv")
    if "github" in url.lower():
        tags.append("github")
    for keyword in ["llm", "gpt", "transformer", "privacy", "ethics", "neural", "ai", "ml"]:
        if keyword in title_lower:
            tags.append(keyword)
    return tags
