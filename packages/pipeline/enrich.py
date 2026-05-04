"""Enrich stage — LLM-powered enrichment of items.

Enrichment is opportunistic: if LLM unavailable, items stay "pending"
and can be backfilled later. Caches on content hash.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import structlog
import yaml

from packages.core.models import Item
from packages.seeds.interest import compute_relevance_score

logger = structlog.get_logger()

SUMMARIZE_SYSTEM = """You are a research paper summarizer. Given a paper's title and abstract, write exactly 2 sentences that summarize the key contribution and findings. Be precise, factual, and use plain language accessible to researchers in adjacent fields. Do not use phrases like "this paper" — start with the contribution."""


async def enrich_item(
    item: Item,
    interest_profile: dict | None = None,
) -> Item:
    """Enrich an item with summary and relevance score.

    If LLM is unavailable, scores relevance from interest profile only.
    """
    if item.enrichment_status == "enriched":
        return item

    try:
        # Relevance scoring (no LLM needed)
        if interest_profile:
            tags = item.tags if isinstance(item.tags, list) else []
            authors = item.authors if isinstance(item.authors, list) else []
            item.relevance_score = compute_relevance_score(
                item_tags=tags,
                item_authors=authors,
                item_venue=item.venue,
                profile=interest_profile,
            )

        # LLM summarization (optional — graceful if unavailable)
        if item.abstract and not item.summary:
            try:
                summary = await _summarize(item.title, item.abstract)
                if summary:
                    item.summary = summary
            except Exception as e:
                logger.debug("summarize_skipped", item_id=item.id, error=str(e))

        item.enrichment_status = "enriched"
    except Exception as e:
        logger.warning("enrichment_failed", item_id=item.id, error=str(e))
        item.enrichment_status = "failed"

    return item


async def _summarize(title: str, abstract: str) -> str | None:
    """Summarize a paper in 2 sentences via LLM."""
    try:
        from packages.agents.llm import completion

        prompt = f"Title: {title}\n\nAbstract: {abstract}"
        result = await completion(
            prompt=prompt,
            system=SUMMARIZE_SYSTEM,
            agent_name="summarizer",
            max_tokens=200,
        )
        return result.get("content", "").strip() or None
    except Exception:
        return None


def load_interest_profile(path: str | Path = "config/interest.yaml") -> dict | None:
    """Load the interest profile from YAML."""
    path = Path(path)
    if not path.exists():
        return None
    with open(path) as f:
        return yaml.safe_load(f)


def content_hash(title: str, abstract: str | None) -> str:
    """SHA256 hash of title + abstract for caching."""
    text = f"{title}|{abstract or ''}"
    return hashlib.sha256(text.encode()).hexdigest()[:32]
