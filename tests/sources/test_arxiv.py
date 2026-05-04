from datetime import datetime

from packages.sources.arxiv import ArxivSource, _clean_whitespace, _extract_arxiv_id
from packages.sources.base import SourceRawItem

# ---------------------------------------------------------------------------
# Sample payload mimicking what _entry_to_dict produces from an Atom entry
# ---------------------------------------------------------------------------

SAMPLE_ENTRY_PAYLOAD = {
    "id": "http://arxiv.org/abs/2401.12345v1",
    "title": "Scaling Laws for  Neural\n  Language Models",
    "summary": "We study empirical scaling laws  for\n  language model performance.",
    "published": "2024-01-15T18:00:00Z",
    "link": "http://arxiv.org/abs/2401.12345v1",
    "authors": [
        {"name": "Jared Kaplan"},
        {"name": "Sam McCandlish"},
        {"name": "Tom Henighan"},
    ],
    "links": [
        {"href": "http://arxiv.org/abs/2401.12345v1", "rel": "alternate", "type": "text/html"},
        {"href": "http://arxiv.org/pdf/2401.12345v1", "rel": "related", "type": "application/pdf"},
    ],
    "tags": [
        {"term": "cs.LG", "scheme": "http://arxiv.org/schemas/atom"},
        {"term": "cs.CL", "scheme": "http://arxiv.org/schemas/atom"},
    ],
    "arxiv_doi_url": "https://doi.org/10.1234/example.2024",
}

MINIMAL_ENTRY_PAYLOAD = {
    "id": "http://arxiv.org/abs/2401.99999v1",
    "title": "Minimal Paper",
    "link": "http://arxiv.org/abs/2401.99999v1",
}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_arxiv_registers():
    from packages.sources.registry import get_source

    cls = get_source("arxiv")
    assert cls is ArxivSource


def test_arxiv_name():
    source = ArxivSource(config={"categories": ["cs.AI"]})
    assert source.name == "arxiv"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def test_parse_basic():
    source = ArxivSource(config={"categories": ["cs.LG", "cs.CL"]})
    raw = SourceRawItem(
        source_id="arxiv:2401.12345v1",
        fetched_at=datetime(2024, 1, 20),
        payload=SAMPLE_ENTRY_PAYLOAD,
    )
    item = source.parse(raw)

    assert item.source == "arxiv"
    assert item.source_id == "arxiv:2401.12345v1"
    assert item.kind == "preprint"
    assert item.title == "Scaling Laws for Neural Language Models"
    assert item.abstract == "We study empirical scaling laws for language model performance."
    assert item.authors == ["Jared Kaplan", "Sam McCandlish", "Tom Henighan"]
    assert item.published_at is not None
    assert item.published_at.year == 2024
    assert item.published_at.month == 1
    assert item.published_at.day == 15
    assert item.url == "http://arxiv.org/abs/2401.12345v1"
    assert item.pdf_url == "http://arxiv.org/pdf/2401.12345v1"
    assert item.arxiv_id == "2401.12345v1"
    assert "cs.LG" in item.tags
    assert "cs.CL" in item.tags


def test_parse_doi_from_url():
    source = ArxivSource(config={"categories": []})
    raw = SourceRawItem(
        source_id="arxiv:2401.12345v1",
        fetched_at=datetime(2024, 1, 20),
        payload=SAMPLE_ENTRY_PAYLOAD,
    )
    item = source.parse(raw)
    assert item.doi == "10.1234/example.2024"


def test_parse_doi_direct():
    """When arxiv_doi is set directly, use it."""
    payload = {**MINIMAL_ENTRY_PAYLOAD, "arxiv_doi": "10.5555/direct.doi"}
    source = ArxivSource(config={"categories": []})
    raw = SourceRawItem(
        source_id="arxiv:2401.99999v1",
        fetched_at=datetime(2024, 1, 20),
        payload=payload,
    )
    item = source.parse(raw)
    assert item.doi == "10.5555/direct.doi"


def test_parse_minimal_entry():
    """Test graceful handling of minimal fields."""
    source = ArxivSource(config={"categories": []})
    raw = SourceRawItem(
        source_id="arxiv:2401.99999v1",
        fetched_at=datetime(2024, 1, 20),
        payload=MINIMAL_ENTRY_PAYLOAD,
    )
    item = source.parse(raw)
    assert item.title == "Minimal Paper"
    assert item.abstract is None
    assert item.authors == []
    assert item.tags == []
    assert item.doi is None
    assert item.kind == "preprint"
    assert item.arxiv_id == "2401.99999v1"
    # Fallback PDF URL constructed from arxiv_id
    assert item.pdf_url == "https://arxiv.org/pdf/2401.99999v1"


def test_parse_pdf_url_from_links():
    """PDF URL should come from links if a PDF link is present."""
    source = ArxivSource(config={"categories": []})
    raw = SourceRawItem(
        source_id="arxiv:2401.12345v1",
        fetched_at=datetime(2024, 1, 20),
        payload=SAMPLE_ENTRY_PAYLOAD,
    )
    item = source.parse(raw)
    assert item.pdf_url == "http://arxiv.org/pdf/2401.12345v1"


def test_parse_authors_as_strings():
    """Authors provided as plain strings should still work."""
    payload = {
        **MINIMAL_ENTRY_PAYLOAD,
        "authors": ["Alice", "Bob"],
    }
    source = ArxivSource(config={"categories": []})
    raw = SourceRawItem(
        source_id="arxiv:2401.99999v1",
        fetched_at=datetime(2024, 1, 20),
        payload=payload,
    )
    item = source.parse(raw)
    assert item.authors == ["Alice", "Bob"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def test_clean_whitespace():
    assert _clean_whitespace("hello  world") == "hello world"
    assert _clean_whitespace("multi\n  line\n text") == "multi line text"
    assert _clean_whitespace(None) is None
    assert _clean_whitespace("  ") is None


def test_extract_arxiv_id():
    assert _extract_arxiv_id("http://arxiv.org/abs/2401.12345v1") == "2401.12345v1"
    assert _extract_arxiv_id("https://arxiv.org/abs/2401.12345v1") == "2401.12345v1"
    assert _extract_arxiv_id("2401.12345v1") == "2401.12345v1"


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def test_cadence_default():
    source = ArxivSource(config={"categories": ["cs.AI"]})
    assert source.cadence == "0 */6 * * *"


def test_cadence_override():
    source = ArxivSource(config={"categories": ["cs.AI"], "cadence": "0 0 * * *"})
    assert source.cadence == "0 0 * * *"


def test_categories_from_config():
    source = ArxivSource(config={"categories": ["cs.AI", "cs.LG", "stat.ML"]})
    assert source.categories == ["cs.AI", "cs.LG", "stat.ML"]
