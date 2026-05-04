from pathlib import Path

import yaml
from fastapi import APIRouter
from pydantic import BaseModel

from packages.sources.registry import list_sources

router = APIRouter(prefix="/api/sources", tags=["sources"])

SOURCES_PATH = Path("config/sources.yaml")


@router.get("/")
async def get_sources() -> dict:
    """List all registered sources with their config status."""
    registered = list_sources()
    config = _load_config()
    sources = []
    for name in sorted(registered):
        src_cfg = config.get(name, {})
        sources.append({
            "name": name,
            "enabled": src_cfg.get("enabled", False),
            "cadence": src_cfg.get("cadence", ""),
        })
    return {"sources": sources}


@router.get("/config")
async def get_sources_config() -> dict:
    """Get full sources config including feeds and queries."""
    config = _load_config()
    return {"config": config}


class AddFeedRequest(BaseModel):
    name: str
    url: str


@router.post("/rss/add")
async def add_rss_feed(req: AddFeedRequest) -> dict:
    """Add a new RSS/Atom feed."""
    config = _load_config()
    if "rss" not in config:
        config["rss"] = {"enabled": True, "feeds": [], "cadence": "0 */6 * * *"}
    feeds = config["rss"].get("feeds", [])
    if any(f.get("url") == req.url for f in feeds):
        return {"status": "already exists"}
    feeds.append({"name": req.name, "url": req.url})
    config["rss"]["feeds"] = feeds
    _save_config(config)
    return {"status": "added", "name": req.name}


@router.post("/web-monitor/add")
async def add_web_monitor(req: AddFeedRequest) -> dict:
    """Add a website to monitor."""
    config = _load_config()
    if "web_monitor" not in config:
        config["web_monitor"] = {"enabled": True, "urls": [], "cadence": "0 */12 * * *"}
    urls = config["web_monitor"].get("urls", [])
    if any(u.get("url") == req.url for u in urls):
        return {"status": "already exists"}
    urls.append({"name": req.name, "url": req.url})
    config["web_monitor"]["urls"] = urls
    _save_config(config)
    return {"status": "added", "name": req.name}


class AddQueryRequest(BaseModel):
    query: str


@router.post("/semantic-scholar/add-query")
async def add_s2_query(req: AddQueryRequest) -> dict:
    """Add a search query to Semantic Scholar."""
    config = _load_config()
    if "semantic_scholar" not in config:
        config["semantic_scholar"] = {"enabled": True, "queries": [], "cadence": "0 */12 * * *"}
    queries = config["semantic_scholar"].get("queries", [])
    if req.query in queries:
        return {"status": "already exists"}
    queries.append(req.query)
    config["semantic_scholar"]["queries"] = queries
    _save_config(config)
    return {"status": "added", "query": req.query}


def _load_config() -> dict:
    if SOURCES_PATH.exists():
        with open(SOURCES_PATH) as f:
            return yaml.safe_load(f) or {}
    return {}


def _save_config(config: dict) -> None:
    with open(SOURCES_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
