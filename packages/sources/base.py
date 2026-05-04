from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Literal, Protocol

from pydantic import BaseModel


class SourceRawItem(BaseModel):
    """Raw item as fetched from a source, before normalization."""

    source_id: str
    fetched_at: datetime
    payload: dict


class NormalizedItem(BaseModel):
    """Normalized item ready for deduplication and storage."""

    source: str
    source_id: str
    kind: Literal["paper", "preprint", "post", "talk", "blog", "issue", "review"]
    title: str
    abstract: str | None = None
    authors: list[str] = []
    affiliations: list[str] = []
    venue: str | None = None
    published_at: datetime | None = None
    url: str
    pdf_url: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    citations: list[str] = []
    tags: list[str] = []
    raw: dict = {}


class Source(Protocol):
    """Protocol that every source plugin must implement.

    Sources self-register via @register_source decorator.
    Each source lives in packages/sources/<name>.py.
    """

    name: str
    cadence: str  # cron expression

    async def fetch(self, since: datetime | None = None) -> AsyncIterator[SourceRawItem]: ...

    def parse(self, item: SourceRawItem) -> NormalizedItem: ...
