"""Web tools — external search and URL fetching."""

from __future__ import annotations

import re

from pydantic import BaseModel

from packages.sources.http import create_client


class WebSearchResult(BaseModel):
    title: str
    url: str
    snippet: str


class FetchedContent(BaseModel):
    url: str
    title: str
    text: str
    word_count: int


async def web_search(query: str, k: int = 5) -> list[WebSearchResult]:
    """Search the web. Uses DuckDuckGo HTML as a free fallback."""
    async with create_client() as client:
        try:
            resp = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
            )
            results = _parse_ddg_html(resp.text, k)
            return results
        except Exception:
            return []


async def fetch_url(url: str) -> FetchedContent | None:
    """Fetch a URL and extract main text content."""
    async with create_client(timeout=15.0) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            text = _extract_text(resp.text)
            title = _extract_title(resp.text)
            return FetchedContent(
                url=url,
                title=title,
                text=text[:10000],  # cap at 10k chars
                word_count=len(text.split()),
            )
        except Exception:
            return None


def _parse_ddg_html(html: str, k: int) -> list[WebSearchResult]:
    """Parse DuckDuckGo HTML results (basic extraction)."""
    results = []
    # Extract result links and snippets
    links = re.findall(r'class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL)
    snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</[a-z]', html, re.DOTALL)

    for i, (url, title) in enumerate(links[:k]):
        snippet = snippets[i] if i < len(snippets) else ""
        results.append(WebSearchResult(
            title=re.sub(r"<[^>]+>", "", title).strip(),
            url=url,
            snippet=re.sub(r"<[^>]+>", "", snippet).strip(),
        ))
    return results


def _extract_text(html: str) -> str:
    """Basic HTML text extraction."""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_title(html: str) -> str:
    """Extract title from HTML."""
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""
