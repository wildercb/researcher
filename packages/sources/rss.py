"""Generic RSS/Atom source plugin for Atlas.

One source class, many feeds via config. Each feed is a {name, url} entry.

Rate limits:
  - 1 req/s per feed (polite default)
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser

from packages.sources.base import NormalizedItem, SourceRawItem
from packages.sources.http import create_client
from packages.sources.registry import register_source


@register_source
class RSSSource:
    name = "rss"
    cadence = "0 */6 * * *"

    def __init__(self, config: dict) -> None:
        self.config = config
        self.feeds: list[dict] = config.get("feeds", [])
        self.cadence = config.get("cadence", self.cadence)

    async def fetch(self, since: datetime | None = None) -> AsyncIterator[SourceRawItem]:
        """Fetch entries from all configured RSS/Atom feeds."""
        async with create_client() as client:
            for feed_config in self.feeds:
                feed_name = feed_config.get("name", "unknown")
                feed_url = feed_config.get("url", "")
                if not feed_url:
                    continue

                try:
                    resp = await client.get(feed_url)
                    resp.raise_for_status()
                except Exception:
                    continue

                parsed = feedparser.parse(resp.text)

                for entry in parsed.entries:
                    published = _parse_date(entry)

                    if since and published and published < since:
                        continue

                    entry_id = entry.get("id") or entry.get("link") or entry.get("title", "")
                    yield SourceRawItem(
                        source_id=f"rss:{feed_name}:{entry_id}",
                        fetched_at=datetime.now(),
                        payload={
                            "feed_name": feed_name,
                            "feed_url": feed_url,
                            **{k: v for k, v in entry.items() if isinstance(v, (str, list, dict))},
                        },
                    )

                # Polite delay between feeds
                await asyncio.sleep(1.0)

    def parse(self, item: SourceRawItem) -> NormalizedItem:
        """Parse an RSS/Atom entry into a NormalizedItem."""
        p = item.payload
        feed_name = p.get("feed_name", "")

        title = p.get("title", "Untitled")
        link = p.get("link", "")
        summary = p.get("summary", p.get("description", ""))

        # Authors
        author = p.get("author", "")
        authors = [author] if author else []

        # Published date
        published_at = None
        for date_field in ("published_parsed", "updated_parsed"):
            parsed_time = p.get(date_field)
            if parsed_time and isinstance(parsed_time, (list, tuple)) and len(parsed_time) >= 6:
                try:
                    published_at = datetime(*parsed_time[:6])
                except (ValueError, TypeError):
                    pass
                break
        if not published_at:
            for str_field in ("published", "updated"):
                date_str = p.get(str_field, "")
                if date_str:
                    try:
                        published_at = parsedate_to_datetime(date_str)
                    except (ValueError, TypeError):
                        pass
                    break

        # Tags
        tags_data = p.get("tags", [])
        tags = []
        if isinstance(tags_data, list):
            for t in tags_data:
                if isinstance(t, dict):
                    tags.append(t.get("term", ""))
                elif isinstance(t, str):
                    tags.append(t)

        # Determine kind
        kind = "blog" if "blog" in feed_name.lower() else "post"

        return NormalizedItem(
            source=self.name,
            source_id=item.source_id,
            kind=kind,
            title=title,
            abstract=summary if summary else None,
            authors=authors,
            venue=feed_name,
            published_at=published_at,
            url=link,
            tags=[t for t in tags if t],
            raw=p,
        )


def _parse_date(entry: dict) -> datetime | None:
    """Try to parse a date from a feedparser entry."""
    for field in ("published_parsed", "updated_parsed"):
        parsed = entry.get(field)
        if parsed and hasattr(parsed, "__len__") and len(parsed) >= 6:
            try:
                return datetime(*parsed[:6])
            except (ValueError, TypeError):
                pass
    for field in ("published", "updated"):
        s = entry.get(field, "")
        if s:
            try:
                return parsedate_to_datetime(s)
            except (ValueError, TypeError):
                pass
    return None
