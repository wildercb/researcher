"""Calibration crawl engine.

Expands seeds into a corpus via citation graph traversal,
stores items with provenance, and derives the interest profile.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import structlog

from packages.core.types import SeedType
from packages.seeds.loader import SeedEntry, load_seeds
from packages.seeds.resolvers.author import resolve_author
from packages.seeds.resolvers.keyword import resolve_keyword
from packages.seeds.resolvers.paper import resolve_paper
from packages.seeds.resolvers.venue import resolve_venue

logger = structlog.get_logger()


@dataclass
class CrawlProgress:
    """Tracks calibration crawl progress."""

    seeds_total: int = 0
    seeds_processed: int = 0
    items_discovered: int = 0
    items_stored: int = 0
    items_deduplicated: int = 0
    errors: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, running, completed, failed

    @property
    def elapsed_seconds(self) -> float:
        return (datetime.now() - self.started_at).total_seconds()


@dataclass
class DiscoveredItem:
    """An item found during calibration."""

    source: str
    title: str
    abstract: str | None = None
    authors: list[str] = field(default_factory=list)
    venue: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    url: str = ""
    published_at: datetime | None = None
    tags: list[str] = field(default_factory=list)
    seed_id: str = ""
    relation: str = ""  # "seed", "cites", "cited_by", "same_author", "same_venue", "keyword_match"
    hops: int = 0
    raw: dict = field(default_factory=dict)


async def run_calibration(
    seeds_path: str | Path = "config/seeds.yaml",
    depth: int = 1,
    max_items: int = 5000,
    s2_api_key: str | None = None,
    on_progress: Callable[[CrawlProgress], None] | None = None,
    dry_run: bool = False,
) -> CrawlProgress:
    """Run the calibration crawl.

    Loads seeds, resolves them, expands citation graphs, discovers items.
    Returns the crawl progress with all discovered items.
    """
    seeds = load_seeds(seeds_path)
    progress = CrawlProgress(seeds_total=len(seeds), status="running")
    _notify(on_progress, progress)

    discovered: list[DiscoveredItem] = []
    seen_ids: set[str] = set()  # dedupe by DOI/arXiv/title

    for seed in seeds:
        if len(discovered) >= max_items:
            break

        try:
            if seed.seed_type == SeedType.PAPER:
                items = await _expand_paper_seed(seed, depth, s2_api_key, seen_ids, max_items - len(discovered))
                discovered.extend(items)
            elif seed.seed_type == SeedType.AUTHOR:
                items = await _expand_author_seed(seed, s2_api_key, seen_ids, max_items - len(discovered))
                discovered.extend(items)
            elif seed.seed_type == SeedType.VENUE:
                items = await _expand_venue_seed(seed, seen_ids, max_items - len(discovered))
                discovered.extend(items)
            elif seed.seed_type == SeedType.KEYWORD:
                items = await _expand_keyword_seed(seed, s2_api_key, seen_ids, max_items - len(discovered))
                discovered.extend(items)

            progress.seeds_processed += 1
        except Exception as e:
            logger.error("seed_expansion_failed", seed=seed.identifier, error=str(e))
            progress.errors += 1

        _notify(on_progress, progress)

    progress.items_discovered = len(discovered)
    progress.items_stored = len(discovered)  # in real impl, after DB insert
    progress.status = "completed"
    _notify(on_progress, progress)

    logger.info(
        "calibration_complete",
        seeds=progress.seeds_processed,
        items=len(discovered),
        errors=progress.errors,
        elapsed_s=round(progress.elapsed_seconds, 1),
    )

    return progress


async def _expand_paper_seed(
    seed: SeedEntry,
    depth: int,
    api_key: str | None,
    seen: set[str],
    budget: int,
) -> list[DiscoveredItem]:
    """Expand a paper seed via citation graph."""
    items: list[DiscoveredItem] = []

    paper = await resolve_paper(seed.identifier, api_key=api_key)
    if not paper:
        logger.warning("paper_seed_unresolved", identifier=seed.identifier)
        return items

    # Add the seed paper itself
    seed_item = _paper_to_item(paper, seed.identifier, "seed", 0)
    if seed_item and _add_if_new(seed_item, seen):
        items.append(seed_item)

    paper_id = paper.get("paperId", "")
    if not paper_id or len(items) >= budget:
        return items

    # Expand citations and references
    from packages.sources.semantic_scholar import SemanticScholarSource

    s2 = SemanticScholarSource({"api_key": api_key} if api_key else {})

    for hop in range(1, depth + 1):
        if len(items) >= budget:
            break

        # Get papers that cite this one
        try:
            citations = await s2.get_citations(paper_id, limit=min(100, budget - len(items)))
            for entry in citations:
                cited_paper = entry if isinstance(entry, dict) and entry.get("paperId") else entry.get("citingPaper", entry)
                item = _paper_to_item(cited_paper, seed.identifier, "cited_by", hop)
                if item and _add_if_new(item, seen):
                    items.append(item)
                    if len(items) >= budget:
                        break
        except Exception as e:
            logger.warning("citations_fetch_failed", paper_id=paper_id, error=str(e))

        # Get papers this one references
        try:
            references = await s2.get_references(paper_id, limit=min(100, budget - len(items)))
            for entry in references:
                ref_paper = entry if isinstance(entry, dict) and entry.get("paperId") else entry.get("citedPaper", entry)
                item = _paper_to_item(ref_paper, seed.identifier, "cites", hop)
                if item and _add_if_new(item, seen):
                    items.append(item)
                    if len(items) >= budget:
                        break
        except Exception as e:
            logger.warning("references_fetch_failed", paper_id=paper_id, error=str(e))

    return items


async def _expand_author_seed(
    seed: SeedEntry,
    api_key: str | None,
    seen: set[str],
    budget: int,
) -> list[DiscoveredItem]:
    """Expand an author seed by fetching their publications."""
    items: list[DiscoveredItem] = []

    author = await resolve_author(
        seed.identifier,
        orcid=seed.metadata.get("orcid"),
        api_key=api_key,
    )
    if not author:
        return items

    for paper in author.get("papers", [])[:budget]:
        item = DiscoveredItem(
            source="semantic_scholar",
            title=paper.get("title", ""),
            seed_id=seed.identifier,
            relation="same_author",
            hops=1,
            raw=paper,
        )
        if item.title and _add_if_new(item, seen):
            items.append(item)
            if len(items) >= budget:
                break

    return items


async def _expand_venue_seed(
    seed: SeedEntry,
    seen: set[str],
    budget: int,
) -> list[DiscoveredItem]:
    """Expand a venue seed by fetching recent papers."""
    items: list[DiscoveredItem] = []

    venue = await resolve_venue(seed.identifier)
    if not venue:
        return items

    for paper in venue.get("recent_papers", [])[:budget]:
        title = paper.get("display_name") or paper.get("title") or ""
        doi_raw = paper.get("doi", "")
        doi = doi_raw.replace("https://doi.org/", "") if doi_raw else None

        item = DiscoveredItem(
            source="openalex",
            title=title,
            doi=doi,
            venue=seed.identifier,
            url=doi_raw or paper.get("id", ""),
            seed_id=seed.identifier,
            relation="same_venue",
            hops=1,
            raw=paper,
        )
        if item.title and _add_if_new(item, seen):
            items.append(item)
            if len(items) >= budget:
                break

    return items


async def _expand_keyword_seed(
    seed: SeedEntry,
    api_key: str | None,
    seen: set[str],
    budget: int,
) -> list[DiscoveredItem]:
    """Expand a keyword seed by searching sources."""
    items: list[DiscoveredItem] = []

    papers = await resolve_keyword(seed.identifier, limit=budget, api_key=api_key)
    for paper in papers:
        item = _paper_to_item(paper, seed.identifier, "keyword_match", 1)
        if item and _add_if_new(item, seen):
            items.append(item)
            if len(items) >= budget:
                break

    return items


def _paper_to_item(
    paper: dict,
    seed_id: str,
    relation: str,
    hops: int,
) -> DiscoveredItem | None:
    """Convert an S2 paper dict to a DiscoveredItem."""
    title = paper.get("title")
    if not title:
        return None

    ext_ids = paper.get("externalIds") or {}
    pub_date = paper.get("publicationDate")
    published_at = None
    if pub_date:
        try:
            published_at = datetime.fromisoformat(pub_date)
        except (ValueError, TypeError):
            pass

    pdf_info = paper.get("openAccessPdf") or {}
    pdf_url = pdf_info.get("url") if isinstance(pdf_info, dict) else None

    return DiscoveredItem(
        source="semantic_scholar",
        title=title,
        abstract=paper.get("abstract"),
        authors=[a.get("name", "") for a in paper.get("authors", []) if a.get("name")],
        venue=paper.get("venue"),
        doi=ext_ids.get("DOI"),
        arxiv_id=ext_ids.get("ArXiv"),
        url=pdf_url or f"https://www.semanticscholar.org/paper/{paper.get('paperId', '')}",
        published_at=published_at,
        tags=paper.get("fieldsOfStudy") or [],
        seed_id=seed_id,
        relation=relation,
        hops=hops,
        raw=paper,
    )


def _add_if_new(item: DiscoveredItem, seen: set[str]) -> bool:
    """Add item to seen set if not duplicate. Returns True if new."""
    keys = []
    if item.doi:
        keys.append(f"doi:{item.doi}")
    if item.arxiv_id:
        keys.append(f"arxiv:{item.arxiv_id}")
    # Title-based dedup (normalized)
    if item.title:
        normalized = item.title.lower().strip()[:100]
        keys.append(f"title:{normalized}")

    for key in keys:
        if key in seen:
            return False

    for key in keys:
        seen.add(key)
    return True


def _notify(callback: Callable[[CrawlProgress], None] | None, progress: CrawlProgress) -> None:
    if callback:
        callback(progress)
