"""Integration test: all sources register correctly."""

import packages.sources  # noqa: F401 — triggers auto-registration
from packages.sources.registry import get_source, list_sources


def test_all_sources_registered():
    sources = list_sources()
    assert "arxiv" in sources
    assert "openalex" in sources
    assert "semantic_scholar" in sources
    assert "openreview" in sources
    assert "rss" in sources
    assert len(sources) >= 5


def test_each_source_has_name_and_cadence():
    for name in list_sources():
        cls = get_source(name)
        assert hasattr(cls, "name")
        assert hasattr(cls, "cadence")
        assert cls.name == name


def test_each_source_instantiable():
    for name in list_sources():
        cls = get_source(name)
        instance = cls(config={})
        assert hasattr(instance, "fetch")
        assert hasattr(instance, "parse")
