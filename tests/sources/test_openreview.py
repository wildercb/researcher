from datetime import datetime

from packages.sources.base import SourceRawItem
from packages.sources.openreview import OpenReviewSource

SAMPLE_NOTE = {
    "id": "abc123",
    "tcdate": 1704067200000,  # 2024-01-01 00:00:00
    "content": {
        "title": {"value": "A Novel Approach to Transformers"},
        "abstract": {"value": "We propose a new method for training transformers."},
        "authors": {"value": ["Alice Smith", "Bob Jones"]},
        "venue": {"value": "NeurIPS 2024"},
        "pdf": {"value": "/pdf/abc123.pdf"},
        "keywords": {"value": ["transformers", "deep learning", "attention"]},
    },
}


def test_openreview_registers():
    from packages.sources.registry import get_source

    cls = get_source("openreview")
    assert cls is OpenReviewSource


def test_parse_basic():
    source = OpenReviewSource(config={"venues": ["NeurIPS 2024"]})
    raw = SourceRawItem(
        source_id="abc123",
        fetched_at=datetime(2024, 1, 15),
        payload=SAMPLE_NOTE,
    )
    item = source.parse(raw)
    assert item.title == "A Novel Approach to Transformers"
    assert item.abstract == "We propose a new method for training transformers."
    assert item.authors == ["Alice Smith", "Bob Jones"]
    assert item.venue == "NeurIPS 2024"
    assert item.kind == "paper"
    assert item.source == "openreview"
    assert item.url == "https://openreview.net/forum?id=abc123"
    assert item.pdf_url == "https://openreview.net/pdf/abc123.pdf"
    assert "transformers" in item.tags


def test_parse_legacy_format():
    """Test parsing when content values are strings instead of dicts."""
    note = {
        "id": "def456",
        "cdate": 1704067200000,
        "content": {
            "title": "Legacy Paper",
            "abstract": "Old format abstract.",
            "authors": ["Author One"],
            "venue": "ICML 2023",
        },
    }
    source = OpenReviewSource(config={"venues": []})
    raw = SourceRawItem(
        source_id="def456",
        fetched_at=datetime(2024, 1, 15),
        payload=note,
    )
    item = source.parse(raw)
    assert item.title == "Legacy Paper"
    assert item.abstract == "Old format abstract."
    assert item.authors == ["Author One"]


def test_parse_missing_fields():
    """Test graceful handling of missing fields."""
    note = {
        "id": "minimal",
        "content": {},
    }
    source = OpenReviewSource(config={"venues": []})
    raw = SourceRawItem(
        source_id="minimal",
        fetched_at=datetime(2024, 1, 15),
        payload=note,
    )
    item = source.parse(raw)
    assert item.title == "Untitled"
    assert item.abstract is None
    assert item.authors == []
