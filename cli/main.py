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
    with open(path) as f:
        data = yaml.safe_load(f)
    count = sum(len(v) for v in data.values() if isinstance(v, list))
    click.echo(f"Loaded {count} seeds from {path}")
    click.echo("Seed import will be fully wired in Phase 1.5")


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
    click.echo(f"Adding paper seed: {identifier}")
    click.echo("Paper seed addition will be fully wired in Phase 1.5")


@seed.command("author")
@click.argument("name")
@click.option("--orcid", help="ORCID identifier")
def seed_author(name: str, orcid: str | None) -> None:
    """Add an author seed."""
    click.echo(f"Adding author seed: {name}" + (f" (ORCID: {orcid})" if orcid else ""))
    click.echo("Author seed addition will be fully wired in Phase 1.5")


@seed.command("venue")
@click.argument("name")
@click.option("--rss", help="RSS feed URL")
def seed_venue(name: str, rss: str | None) -> None:
    """Add a venue seed."""
    click.echo(f"Adding venue seed: {name}")
    click.echo("Venue seed addition will be fully wired in Phase 1.5")


@seed.command("keyword")
@click.argument("term")
@click.option("--weight", default=1.0, type=float, help="Keyword weight")
def seed_keyword(term: str, weight: float) -> None:
    """Add a keyword seed."""
    click.echo(f"Adding keyword seed: {term} (weight={weight})")
    click.echo("Keyword seed addition will be fully wired in Phase 1.5")


# --- Calibrate ---


@cli.command()
@click.option("--depth", default=2, type=int, help="Citation graph depth")
@click.option("--max-items", default=5000, type=int, help="Max items to fetch")
@click.option("--status", "show_status", is_flag=True, help="Show calibration status")
@click.option("--dry-run", is_flag=True, help="Show what would be fetched")
def calibrate(depth: int, max_items: int, show_status: bool, dry_run: bool) -> None:
    """Run the calibration crawl from seeds."""
    if show_status:
        click.echo("Calibration status: not yet started")
        click.echo("Calibration will be fully wired in Phase 1.5")
        return
    if dry_run:
        click.echo(f"Would crawl with depth={depth}, max_items={max_items}")
        click.echo("Calibration will be fully wired in Phase 1.5")
        return
    click.echo(f"Starting calibration crawl (depth={depth}, max_items={max_items})...")
    click.echo("Calibration will be fully wired in Phase 1.5")


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
@click.option("--source", help="Run pipeline for a specific source")
@click.option("--since", help="Process items since date")
def pipeline_run(source: str | None, since: str | None) -> None:
    """Run the ingestion pipeline."""
    click.echo("Pipeline will be fully wired in Phase 2")


@pipeline.command("retry-failed")
def pipeline_retry() -> None:
    """Retry failed pipeline items."""
    click.echo("Pipeline retry will be fully wired in Phase 2")


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
