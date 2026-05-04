"""Seed loader — reads and writes config/seeds.yaml."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from packages.core.types import SeedType

DOI_RE = re.compile(r"^10\.\d{4,}/")
ARXIV_RE = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")


@dataclass
class SeedEntry:
    seed_type: SeedType
    identifier: str
    label: str
    weight: float = 1.0
    is_negative: bool = False
    metadata: dict = field(default_factory=dict)


def load_seeds(path: str | Path) -> list[SeedEntry]:
    """Load seeds from a YAML file."""
    path = Path(path)
    if not path.exists():
        return []
    with open(path) as f:
        data = yaml.safe_load(f) or {}

    seeds: list[SeedEntry] = []

    # Papers
    for entry in data.get("papers", []) or []:
        if isinstance(entry, str):
            identifier = entry
            meta = {}
        elif isinstance(entry, dict):
            identifier = entry.get("doi") or entry.get("arxiv") or entry.get("title") or ""
            meta = {k: v for k, v in entry.items() if k not in ("doi", "arxiv", "title", "weight")}
        else:
            continue
        seeds.append(SeedEntry(
            seed_type=SeedType.PAPER,
            identifier=identifier,
            label=_paper_label(identifier),
            weight=entry.get("weight", 1.0) if isinstance(entry, dict) else 1.0,
            metadata=meta,
        ))

    # Authors
    for entry in data.get("authors", []) or []:
        if isinstance(entry, str):
            name = entry
            meta = {}
        elif isinstance(entry, dict):
            name = entry.get("name", "")
            meta = {k: v for k, v in entry.items() if k not in ("name", "weight")}
        else:
            continue
        seeds.append(SeedEntry(
            seed_type=SeedType.AUTHOR,
            identifier=name,
            label=name,
            weight=entry.get("weight", 1.0) if isinstance(entry, dict) else 1.0,
            metadata=meta,
        ))

    # Venues
    for entry in data.get("venues", []) or []:
        if isinstance(entry, str):
            name = entry
            meta = {}
        elif isinstance(entry, dict):
            name = entry.get("name", "")
            meta = {k: v for k, v in entry.items() if k not in ("name", "weight")}
        else:
            continue
        seeds.append(SeedEntry(
            seed_type=SeedType.VENUE,
            identifier=name,
            label=name,
            weight=entry.get("weight", 1.0) if isinstance(entry, dict) else 1.0,
            metadata=meta,
        ))

    # Keywords
    for entry in data.get("keywords", []) or []:
        if isinstance(entry, str):
            term = entry
            weight = 1.0
        elif isinstance(entry, dict):
            term = entry.get("term", "")
            weight = entry.get("weight", 1.0)
        else:
            continue
        seeds.append(SeedEntry(
            seed_type=SeedType.KEYWORD,
            identifier=term,
            label=term,
            weight=weight,
        ))

    # Negative seeds
    neg = data.get("negative", {}) or {}
    for author in neg.get("authors", []) or []:
        name = author if isinstance(author, str) else author.get("name", "")
        seeds.append(SeedEntry(
            seed_type=SeedType.NEGATIVE,
            identifier=name,
            label=f"NOT: {name}",
            is_negative=True,
            metadata={"original_type": "author"},
        ))
    for topic in neg.get("topics", []) or []:
        term = topic if isinstance(topic, str) else topic.get("term", "")
        seeds.append(SeedEntry(
            seed_type=SeedType.NEGATIVE,
            identifier=term,
            label=f"NOT: {term}",
            is_negative=True,
            metadata={"original_type": "topic"},
        ))
    for venue in neg.get("venues", []) or []:
        name = venue if isinstance(venue, str) else venue.get("name", "")
        seeds.append(SeedEntry(
            seed_type=SeedType.NEGATIVE,
            identifier=name,
            label=f"NOT: {name}",
            is_negative=True,
            metadata={"original_type": "venue"},
        ))

    return seeds


def save_seeds(path: str | Path, seeds: list[SeedEntry]) -> None:
    """Save seeds to a YAML file."""
    data: dict = {
        "papers": [],
        "authors": [],
        "venues": [],
        "keywords": [],
        "negative": {"authors": [], "topics": [], "venues": []},
    }

    for s in seeds:
        if s.is_negative:
            orig_type = s.metadata.get("original_type", "topic")
            if orig_type == "author":
                data["negative"]["authors"].append(s.identifier)
            elif orig_type == "venue":
                data["negative"]["venues"].append(s.identifier)
            else:
                data["negative"]["topics"].append(s.identifier)
        elif s.seed_type == SeedType.PAPER:
            entry: dict = {}
            if DOI_RE.match(s.identifier):
                entry["doi"] = s.identifier
            elif ARXIV_RE.match(s.identifier):
                entry["arxiv"] = s.identifier
            else:
                entry["title"] = s.identifier
            if s.weight != 1.0:
                entry["weight"] = s.weight
            data["papers"].append(entry)
        elif s.seed_type == SeedType.AUTHOR:
            entry = {"name": s.identifier}
            if s.metadata.get("orcid"):
                entry["orcid"] = s.metadata["orcid"]
            if s.weight != 1.0:
                entry["weight"] = s.weight
            data["authors"].append(entry)
        elif s.seed_type == SeedType.VENUE:
            entry = {"name": s.identifier}
            if s.weight != 1.0:
                entry["weight"] = s.weight
            data["venues"].append(entry)
        elif s.seed_type == SeedType.KEYWORD:
            entry = {"term": s.identifier}
            if s.weight != 1.5:
                entry["weight"] = s.weight
            data["keywords"].append(entry)

    path = Path(path)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def classify_identifier(identifier: str) -> str:
    """Classify a paper identifier as 'doi', 'arxiv', or 'title'."""
    if DOI_RE.match(identifier):
        return "doi"
    if ARXIV_RE.match(identifier):
        return "arxiv"
    if identifier.startswith("arxiv:"):
        return "arxiv"
    return "title"


def _paper_label(identifier: str) -> str:
    kind = classify_identifier(identifier)
    if kind == "doi":
        return f"DOI:{identifier}"
    if kind == "arxiv":
        return f"arXiv:{identifier}"
    return identifier
