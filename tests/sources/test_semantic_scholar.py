from datetime import datetime

import pytest

from packages.sources.base import SourceRawItem
from packages.sources.semantic_scholar import SemanticScholarSource

SAMPLE_PAPER = {
    "paperId": "a1b2c3d4e5f6",
    "title": "Attention Is All You Need",
    "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
    "authors": [
        {"authorId": "1", "name": "Ashish Vaswani"},
        {"authorId": "2", "name": "Noam Shazeer"},
        {"authorId": "3", "name": "Niki Parmar"},
    ],
    "venue": "NeurIPS",
    "year": 2017,
    "externalIds": {
        "DOI": "10.48550/arXiv.1706.03762",
        "ArXiv": "1706.03762",
        "CorpusId": 215827658,
    },
    "citationCount": 90000,
    "referenceCount": 38,
    "openAccessPdf": {"url": "https://arxiv.org/pdf/1706.03762.pdf", "status": "GREEN"},
    "publicationDate": "2017-06-12",
    "fieldsOfStudy": ["Computer Science", "Mathematics"],
}


def test_semantic_scholar_registers():
    from packages.sources.registry import get_source

    cls = get_source("semantic_scholar")
    assert cls is SemanticScholarSource


def test_parse_basic():
    source = SemanticScholarSource(config={"queries": ["transformers"]})
    raw = SourceRawItem(
        source_id="a1b2c3d4e5f6",
        fetched_at=datetime(2024, 1, 15),
        payload=SAMPLE_PAPER,
    )
    item = source.parse(raw)

    assert item.title == "Attention Is All You Need"
    assert item.abstract is not None
    assert "dominant sequence transduction" in item.abstract
    assert item.kind == "paper"
    assert item.source == "semantic_scholar"
    assert item.source_id == "a1b2c3d4e5f6"
    assert item.venue == "NeurIPS"
    assert item.url == "https://www.semanticscholar.org/paper/a1b2c3d4e5f6"
    assert item.pdf_url == "https://arxiv.org/pdf/1706.03762.pdf"
    assert item.published_at == datetime(2017, 6, 12)


def test_parse_authors():
    source = SemanticScholarSource(config={"queries": []})
    raw = SourceRawItem(
        source_id="a1b2c3d4e5f6",
        fetched_at=datetime(2024, 1, 15),
        payload=SAMPLE_PAPER,
    )
    item = source.parse(raw)

    assert len(item.authors) == 3
    assert "Ashish Vaswani" in item.authors
    assert "Noam Shazeer" in item.authors
    assert "Niki Parmar" in item.authors


def test_parse_external_ids():
    source = SemanticScholarSource(config={"queries": []})
    raw = SourceRawItem(
        source_id="a1b2c3d4e5f6",
        fetched_at=datetime(2024, 1, 15),
        payload=SAMPLE_PAPER,
    )
    item = source.parse(raw)

    assert item.doi == "10.48550/arXiv.1706.03762"
    assert item.arxiv_id == "1706.03762"


def test_parse_tags():
    source = SemanticScholarSource(config={"queries": []})
    raw = SourceRawItem(
        source_id="a1b2c3d4e5f6",
        fetched_at=datetime(2024, 1, 15),
        payload=SAMPLE_PAPER,
    )
    item = source.parse(raw)

    assert "Computer Science" in item.tags
    assert "Mathematics" in item.tags


def test_parse_missing_fields():
    """Test graceful handling of missing/null fields."""
    minimal_paper = {
        "paperId": "minimal123",
        "title": "Minimal Paper",
        "abstract": None,
        "authors": [],
        "venue": "",
        "year": 2024,
        "externalIds": {},
        "citationCount": 0,
        "referenceCount": 0,
        "openAccessPdf": None,
        "publicationDate": None,
        "fieldsOfStudy": None,
    }
    source = SemanticScholarSource(config={"queries": []})
    raw = SourceRawItem(
        source_id="minimal123",
        fetched_at=datetime(2024, 6, 1),
        payload=minimal_paper,
    )
    item = source.parse(raw)

    assert item.title == "Minimal Paper"
    assert item.abstract is None
    assert item.authors == []
    assert item.venue is None
    assert item.published_at is None
    assert item.pdf_url is None
    assert item.doi is None
    assert item.arxiv_id is None
    assert item.tags == []
    assert item.url == "https://www.semanticscholar.org/paper/minimal123"


def test_parse_no_external_ids_key():
    """Test when externalIds key is missing entirely."""
    paper = {
        "paperId": "noext456",
        "title": "No External IDs",
    }
    source = SemanticScholarSource(config={"queries": []})
    raw = SourceRawItem(
        source_id="noext456",
        fetched_at=datetime(2024, 6, 1),
        payload=paper,
    )
    item = source.parse(raw)

    assert item.doi is None
    assert item.arxiv_id is None


def test_rate_limiter_with_api_key():
    """With an API key, rate limiter should allow 10 req/s."""
    source = SemanticScholarSource(config={"api_key": "test-key", "queries": []})
    assert source._rate_limiter._min_interval == pytest.approx(0.1)


def test_rate_limiter_without_api_key():
    """Without an API key, rate limiter should allow 1 req/s."""
    source = SemanticScholarSource(config={"queries": []})
    assert source._rate_limiter._min_interval == pytest.approx(1.0)
