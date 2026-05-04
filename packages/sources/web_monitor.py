"""Web monitor source plugin for Atlas.

Watches custom URLs (researcher pages, lab websites, social profiles)
for new content. Extracts text and looks for new papers/posts.

Add URLs in config/sources.yaml under web_monitor.urls.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import AsyncIterator
from datetime import datetime

from packages.sources.base import NormalizedItem, SourceRawItem
from packages.sources.http import RateLimiter, create_client
from packages.sources.registry import register_source


@register_source
class WebMonitorSource:
    name = "web_monitor"
    cadence = "0 */12 * * *"

    def __init__(self, config: dict) -> None:
        self.config = config
        self.urls: list[dict] = config.get("urls", [])
        self.cadence = config.get("cadence", self.cadence)
        self._rate_limiter = RateLimiter(requests_per_second=1.0)

    async def fetch(self, since: datetime | None = None) -> AsyncIterator[SourceRawItem]:
        """Fetch content from monitored URLs."""
        async with create_client(timeout=15.0) as client:
            for entry in self.urls:
                name = entry.get("name", "unknown")
                url = entry.get("url", "")
                if not url:
                    continue

                try:
                    await self._rate_limiter.acquire()
                    resp = await client.get(url)
                    resp.raise_for_status()
                    html = resp.text

                    # Extract links that look like papers/posts
                    links = _extract_content_links(html, url)

                    for link in links:
                        content_hash = hashlib.sha256(link["url"].encode()).hexdigest()[:16]
                        yield SourceRawItem(
                            source_id=f"webmon:{name}:{content_hash}",
                            fetched_at=datetime.now(),
                            payload={
                                "monitor_name": name,
                                "monitor_url": url,
                                "title": link["title"],
                                "url": link["url"],
                            },
                        )
                except Exception:
                    continue

    def parse(self, item: SourceRawItem) -> NormalizedItem:
        p = item.payload
        return NormalizedItem(
            source=self.name,
            source_id=item.source_id,
            kind="post",
            title=p.get("title", "Untitled"),
            url=p.get("url", ""),
            venue=p.get("monitor_name", ""),
            tags=["web-monitor"],
            raw=p,
        )


def _extract_content_links(html: str, base_url: str) -> list[dict]:
    """Extract links that look like papers or blog posts from HTML."""
    links = []
    seen = set()

    # Find <a> tags with href
    for match in re.finditer(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL):
        href = match.group(1)
        text = re.sub(r"<[^>]+>", "", match.group(2)).strip()

        if not text or len(text) < 10 or len(text) > 300:
            continue

        # Resolve relative URLs
        if href.startswith("/"):
            from urllib.parse import urlparse

            parsed = urlparse(base_url)
            href = f"{parsed.scheme}://{parsed.netloc}{href}"
        elif not href.startswith("http"):
            continue

        # Filter: skip nav/footer links, keep content links
        text_lower = text.lower()
        if any(skip in text_lower for skip in ["login", "sign up", "cookie", "menu", "nav", "footer"]):
            continue

        if href not in seen:
            seen.add(href)
            links.append({"url": href, "title": text})

    return links[:50]  # cap at 50 per page
