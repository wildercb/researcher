"""OpenReview source plugin for Atlas.

Rate limits:
  - ~2 req/s (undocumented, conservative estimate)
  - No auth required for public notes
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime

from packages.sources.base import NormalizedItem, SourceRawItem
from packages.sources.http import RateLimiter, create_client, resilient_get
from packages.sources.registry import register_source


@register_source
class OpenReviewSource:
    name = "openreview"
    cadence = "0 0 * * *"

    def __init__(self, config: dict) -> None:
        self.config = config
        self.venues: list[str] = config.get("venues", [])
        self.cadence = config.get("cadence", self.cadence)
        self._rate_limiter = RateLimiter(requests_per_second=2.0)

    async def fetch(self, since: datetime | None = None) -> AsyncIterator[SourceRawItem]:
        """Fetch notes from OpenReview for configured venues."""
        async with create_client() as client:
            for venue in self.venues:
                offset = 0
                limit = 100
                while True:
                    params = {
                        "content.venue": venue,
                        "offset": offset,
                        "limit": limit,
                    }
                    resp = await resilient_get(
                        client,
                        "https://api2.openreview.net/notes",
                        rate_limiter=self._rate_limiter,
                        params=params,
                    )
                    data = resp.json()
                    notes = data.get("notes", [])
                    if not notes:
                        break

                    for note in notes:
                        created = note.get("tcdate", note.get("cdate", 0))
                        created_dt = datetime.fromtimestamp(created / 1000) if created else None

                        if since and created_dt and created_dt < since:
                            continue

                        yield SourceRawItem(
                            source_id=note.get("id", ""),
                            fetched_at=datetime.now(),
                            payload=note,
                        )

                    if len(notes) < limit:
                        break
                    offset += limit
                    if offset >= 5000:
                        break

    def parse(self, item: SourceRawItem) -> NormalizedItem:
        """Parse an OpenReview note into a NormalizedItem."""
        note = item.payload
        content = note.get("content", {})

        # Extract values — OpenReview stores content as {field: {value: ...}}
        def get_val(field: str) -> str | None:
            v = content.get(field)
            if isinstance(v, dict):
                return v.get("value")
            if isinstance(v, str):
                return v
            return None

        title = get_val("title") or "Untitled"
        abstract = get_val("abstract")
        venue = get_val("venue") or get_val("venueid")

        # Authors — may be strings or dicts like {"fullname": "...", "username": "..."}
        authors_val = content.get("authors")
        if isinstance(authors_val, dict):
            authors_raw = authors_val.get("value", [])
        elif isinstance(authors_val, list):
            authors_raw = authors_val
        else:
            authors_raw = []

        authors = []
        for a in authors_raw if isinstance(authors_raw, list) else []:
            if isinstance(a, str):
                authors.append(a)
            elif isinstance(a, dict):
                authors.append(a.get("fullname") or a.get("name") or a.get("username", ""))
            # skip anything else

        # Published date
        cdate = note.get("tcdate", note.get("cdate", 0))
        published_at = datetime.fromtimestamp(cdate / 1000) if cdate else None

        # PDF URL
        pdf_url = None
        pdf_val = content.get("pdf")
        if isinstance(pdf_val, dict):
            pdf_path = pdf_val.get("value", "")
        elif isinstance(pdf_val, str):
            pdf_path = pdf_val
        else:
            pdf_path = ""
        if pdf_path:
            pdf_url = f"https://openreview.net{pdf_path}" if pdf_path.startswith("/") else pdf_path

        # Keywords as tags
        keywords_val = content.get("keywords")
        tags = []
        if isinstance(keywords_val, dict):
            tags = keywords_val.get("value", [])
        elif isinstance(keywords_val, list):
            tags = keywords_val

        return NormalizedItem(
            source=self.name,
            source_id=item.source_id,
            kind="paper",
            title=title,
            abstract=abstract,
            authors=authors if isinstance(authors, list) else [],
            venue=venue,
            published_at=published_at,
            url=f"https://openreview.net/forum?id={note.get('id', '')}",
            pdf_url=pdf_url,
            tags=tags if isinstance(tags, list) else [],
            raw=note,
        )
