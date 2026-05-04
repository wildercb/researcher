"""Atlas CLI — entry point for all commands."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import click
import yaml


def _load_sources_config() -> dict:
    path = Path("config/sources.yaml")
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return {}


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """Atlas — Research Intelligence Platform."""
    pass


@cli.command()
@click.option("--host", default="0.0.0.0", help="Bind host")
@click.option("--port", default=8765, type=int, help="Bind port")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def run(host: str, port: int, reload: bool) -> None:
    """Start the Atlas server."""
    import uvicorn

    uvicorn.run(
        "apps.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


# --- Seed commands ---


@cli.group()
def seed() -> None:
    """Manage seeds (papers, authors, venues, keywords)."""
    pass


@seed.command("import")
@click.argument("path", type=click.Path(exists=True))
def seed_import(path: str) -> None:
    """Import seeds from a YAML file."""
    from packages.seeds.loader import load_seeds

    seeds = load_seeds(path)
    click.echo(f"Loaded {len(seeds)} seeds from {path}")
    for s in seeds:
        neg = " [negative]" if s.is_negative else ""
        click.echo(f"  [{s.seed_type.value}] {s.identifier}{neg}")


@seed.command("export")
def seed_export() -> None:
    """Export current seeds to stdout as YAML."""
    config_path = Path("config/seeds.yaml")
    if config_path.exists():
        click.echo(config_path.read_text())
    else:
        click.echo("No seeds file found at config/seeds.yaml")


@seed.command("paper")
@click.argument("identifier")
def seed_paper(identifier: str) -> None:
    """Add a paper seed (DOI, arXiv ID, or title)."""
    from packages.core.types import SeedType
    from packages.seeds.loader import SeedEntry, classify_identifier, load_seeds, save_seeds

    seeds_path = Path("config/seeds.yaml")
    seeds = load_seeds(seeds_path)
    kind = classify_identifier(identifier)
    label = f"{kind.upper()}:{identifier}" if kind != "title" else identifier
    seeds.append(SeedEntry(
        seed_type=SeedType.PAPER,
        identifier=identifier,
        label=label,
    ))
    save_seeds(seeds_path, seeds)
    click.echo(f"Added paper seed: {identifier} ({kind})")


@seed.command("author")
@click.argument("name")
@click.option("--orcid", help="ORCID identifier")
def seed_author(name: str, orcid: str | None) -> None:
    """Add an author seed."""
    from packages.core.types import SeedType
    from packages.seeds.loader import SeedEntry, load_seeds, save_seeds

    seeds_path = Path("config/seeds.yaml")
    seeds = load_seeds(seeds_path)
    meta = {"orcid": orcid} if orcid else {}
    seeds.append(SeedEntry(
        seed_type=SeedType.AUTHOR,
        identifier=name,
        label=name,
        metadata=meta,
    ))
    save_seeds(seeds_path, seeds)
    click.echo(f"Added author seed: {name}" + (f" (ORCID: {orcid})" if orcid else ""))


@seed.command("venue")
@click.argument("name")
@click.option("--rss", help="RSS feed URL")
def seed_venue(name: str, rss: str | None) -> None:
    """Add a venue seed."""
    from packages.core.types import SeedType
    from packages.seeds.loader import SeedEntry, load_seeds, save_seeds

    seeds_path = Path("config/seeds.yaml")
    seeds = load_seeds(seeds_path)
    meta = {"rss": rss} if rss else {}
    seeds.append(SeedEntry(
        seed_type=SeedType.VENUE,
        identifier=name,
        label=name,
        metadata=meta,
    ))
    save_seeds(seeds_path, seeds)
    click.echo(f"Added venue seed: {name}")


@seed.command("keyword")
@click.argument("term")
@click.option("--weight", default=1.0, type=float, help="Keyword weight")
def seed_keyword(term: str, weight: float) -> None:
    """Add a keyword seed."""
    from packages.core.types import SeedType
    from packages.seeds.loader import SeedEntry, load_seeds, save_seeds

    seeds_path = Path("config/seeds.yaml")
    seeds = load_seeds(seeds_path)
    seeds.append(SeedEntry(
        seed_type=SeedType.KEYWORD,
        identifier=term,
        label=term,
        weight=weight,
    ))
    save_seeds(seeds_path, seeds)
    click.echo(f"Added keyword seed: {term} (weight={weight})")


# --- Calibrate ---


@cli.command()
@click.option("--depth", default=2, type=int, help="Citation graph depth")
@click.option("--max-items", default=5000, type=int, help="Max items to fetch")
@click.option("--status", "show_status", is_flag=True, help="Show calibration status")
@click.option("--dry-run", is_flag=True, help="Show what would be fetched")
def calibrate(depth: int, max_items: int, show_status: bool, dry_run: bool) -> None:
    """Run the calibration crawl from seeds."""
    import asyncio
    import os

    from packages.seeds.crawl import run_calibration

    seeds_path = Path("config/seeds.yaml")
    s2_key = os.environ.get("S2_API_KEY") or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")

    if show_status:
        click.echo("Calibration status: check config/interest.yaml for last run results.")
        return

    if dry_run:
        from packages.seeds.loader import load_seeds

        seeds = load_seeds(seeds_path)
        click.echo(f"Seeds: {len(seeds)}")
        for s in seeds:
            click.echo(f"  [{s.seed_type.value}] {s.identifier}")
        click.echo(f"\nWould crawl with depth={depth}, max_items={max_items}")
        return

    def on_progress(p):
        click.echo(
            f"\r  Seeds: {p.seeds_processed}/{p.seeds_total} | "
            f"Items: {p.items_discovered} | "
            f"Errors: {p.errors} | "
            f"Elapsed: {p.elapsed_seconds:.0f}s",
            nl=False,
        )

    click.echo(f"Starting calibration crawl (depth={depth}, max_items={max_items})...")
    progress = asyncio.run(run_calibration(
        seeds_path=seeds_path,
        depth=depth,
        max_items=max_items,
        s2_api_key=s2_key,
        on_progress=on_progress,
        dry_run=False,
    ))
    click.echo("\n\nCalibration complete:")
    click.echo(f"  Seeds processed: {progress.seeds_processed}/{progress.seeds_total}")
    click.echo(f"  Items discovered: {progress.items_discovered}")
    click.echo(f"  Errors: {progress.errors}")
    click.echo(f"  Duration: {progress.elapsed_seconds:.1f}s")


# --- Sources ---


@cli.group()
def sources() -> None:
    """Manage source plugins."""
    pass


@sources.command("list")
def sources_list() -> None:
    """List registered source plugins."""
    import packages.sources  # noqa: F401 — triggers auto-registration
    from packages.sources.registry import list_sources

    registered = list_sources()
    if not registered:
        click.echo("No sources registered.")
    else:
        config = _load_sources_config()
        for name in sorted(registered):
            src_cfg = config.get(name, {})
            enabled = src_cfg.get("enabled", False)
            status = "enabled" if enabled else "disabled"
            click.echo(f"  {name:20s} [{status}]")


@sources.command("test")
@click.argument("name")
@click.option("--limit", default=5, type=int, help="Max items to fetch")
def sources_test(name: str, limit: int) -> None:
    """Test a source plugin by fetching and parsing a few items."""
    import asyncio

    import packages.sources  # noqa: F401
    from packages.sources.registry import get_source

    config = _load_sources_config()
    src_cls = get_source(name)
    src = src_cls(config.get(name, {}))
    click.echo(f"Testing source: {name}")

    async def _test():
        count = 0
        async for raw in src.fetch():
            item = src.parse(raw)
            click.echo(f"  [{item.kind}] {item.title[:80]}")
            if item.authors:
                click.echo(f"         Authors: {', '.join(item.authors[:3])}")
            count += 1
            if count >= limit:
                break
        click.echo(f"\nFetched and parsed {count} items from {name}.")

    asyncio.run(_test())


@sources.command("fetch")
@click.argument("name")
@click.option("--since", help="Fetch items since date (YYYY-MM-DD)")
@click.option("--limit", default=100, type=int, help="Max items to fetch")
@click.option("--dry-run", is_flag=True, help="Show what would be fetched")
def sources_fetch(name: str, since: str | None, limit: int, dry_run: bool) -> None:
    """Fetch items from a source."""
    import asyncio

    import packages.sources  # noqa: F401
    from packages.sources.registry import get_source

    config = _load_sources_config()
    src_cls = get_source(name)
    src = src_cls(config.get(name, {}))

    since_dt = None
    if since:
        since_dt = datetime.strptime(since, "%Y-%m-%d")

    click.echo(f"Fetching from {name}" + (f" since {since}" if since else ""))

    async def _fetch():
        count = 0
        async for raw in src.fetch(since=since_dt):
            item = src.parse(raw)
            if dry_run:
                click.echo(f"  [{item.kind}] {item.title[:80]}")
            count += 1
            if count >= limit:
                break
        click.echo(f"\n{'Would fetch' if dry_run else 'Fetched'} {count} items from {name}.")

    asyncio.run(_fetch())


# --- Pipeline ---


@cli.group()
def pipeline() -> None:
    """Pipeline management."""
    pass


@pipeline.command("run")
@click.option("--source", "source_name", help="Run pipeline for a specific source")
@click.option("--since", help="Process items since date (YYYY-MM-DD)")
@click.option("--no-enrich", is_flag=True, help="Skip LLM enrichment")
def pipeline_run(source_name: str | None, since: str | None, no_enrich: bool) -> None:
    """Run the ingestion pipeline."""
    import asyncio

    from packages.core.config import get_settings
    from packages.core.storage import create_storage
    from packages.pipeline.runner import run_pipeline

    settings = get_settings()
    storage = create_storage(settings)

    since_dt = None
    if since:
        since_dt = datetime.strptime(since, "%Y-%m-%d")

    sources_to_run = []
    if source_name:
        sources_to_run = [source_name]
    else:
        config = _load_sources_config()
        sources_to_run = [name for name, cfg in config.items() if cfg.get("enabled")]

    async def _run():
        await storage.init()
        try:
            for src in sources_to_run:
                click.echo(f"Running pipeline for {src}...")
                result = await run_pipeline(
                    source_name=src,
                    storage=storage,
                    since=since_dt,
                    enrich=not no_enrich,
                )
                click.echo(
                    f"  Fetched: {result.fetched} | New: {result.new_items} | "
                    f"Dupes: {result.duplicates} | Enriched: {result.enriched} | "
                    f"Failed: {result.failed} | {result.elapsed_seconds:.1f}s"
                )
        finally:
            await storage.close()

    asyncio.run(_run())


@pipeline.command("retry-failed")
@click.option("--limit", default=100, type=int, help="Max items to retry")
def pipeline_retry(limit: int) -> None:
    """Retry failed pipeline items."""
    import asyncio

    from packages.core.config import get_settings
    from packages.core.storage import create_storage
    from packages.pipeline.backfill import backfill_enrichment

    settings = get_settings()
    storage = create_storage(settings)

    async def _retry():
        await storage.init()
        try:
            async with storage.session() as session:
                count = await backfill_enrichment(session, limit=limit)
                click.echo(f"Re-enriched {count} items.")
        finally:
            await storage.close()

    asyncio.run(_retry())


# --- Export / Import ---


@cli.command("export")
@click.argument("path", default="atlas-export.json")
def export_data(path: str) -> None:
    """Export all Atlas data."""
    click.echo(f"Exporting data to {path}...")
    click.echo("Export will be fully wired in Phase 2")


@cli.command("import")
@click.argument("path", type=click.Path(exists=True))
def import_data(path: str) -> None:
    """Import Atlas data from export."""
    click.echo(f"Importing data from {path}...")
    click.echo("Import will be fully wired in Phase 2")


if __name__ == "__main__":
    cli()
