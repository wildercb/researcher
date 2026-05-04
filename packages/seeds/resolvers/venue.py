"""Venue seed resolver — resolves venue name to metadata via OpenAlex."""

from __future__ import annotations

import structlog

from packages.sources.http import RateLimiter, create_client, resilient_get

logger = structlog.get_logger()

OPENALEX_API = "https://api.openalex.org"


async def resolve_venue(
    name: str,
    mailto: str | None = None,
) -> dict | None:
    """Resolve a venue name to OpenAlex source metadata.

    Returns dict with id, display_name, works_count, recent papers, or None.
    """
    rate_limiter = RateLimiter(requests_per_second=10.0)

    async with create_client() as client:
        try:
            params: dict = {"search": name, "per_page": 5}
            if mailto:
                params["mailto"] = mailto

            resp = await resilient_get(
                client,
                f"{OPENALEX_API}/sources",
                rate_limiter=rate_limiter,
                params=params,
            )
            data = resp.json()
            results = data.get("results", [])
            if not results:
                return None

            # Take the best match
            venue = results[0]
            logger.info("venue_resolved", name=name, openalex_id=venue.get("id"))

            # Fetch recent papers from this venue
            venue_id = venue.get("id", "")
            papers_resp = await resilient_get(
                client,
                f"{OPENALEX_API}/works",
                rate_limiter=rate_limiter,
                params={
                    "filter": f"primary_location.source.id:{venue_id}",
                    "sort": "publication_date:desc",
                    "per_page": 100,
                    **({"mailto": mailto} if mailto else {}),
                },
            )
            papers_data = papers_resp.json()

            return {
                "id": venue.get("id"),
                "display_name": venue.get("display_name"),
                "works_count": venue.get("works_count"),
                "type": venue.get("type"),
                "recent_papers": papers_data.get("results", []),
            }
        except Exception as e:
            logger.warning("venue_resolve_failed", name=name, error=str(e))
            return None
