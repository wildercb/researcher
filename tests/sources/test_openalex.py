from datetime import datetime

from packages.sources.base import SourceRawItem
from packages.sources.openalex import OpenAlexSource, reconstruct_abstract

SAMPLE_WORK = {
    "id": "https://openalex.org/W2741809807",
    "doi": "https://doi.org/10.1038/s41586-024-07386-0",
    "display_name": "Scaling Laws for Neural Language Models",
    "publication_date": "2024-03-15",
    "abstract_inverted_index": {
        "We": [0],
        "study": [1],
        "empirical": [2],
        "scaling": [3],
        "laws": [4],
        "for": [5, 11],
        "neural": [6],
        "language": [7],
        "model": [8],
        "performance": [9],
        "and": [10],
        "transfer.": [12],
    },
    "authorships": [
        {
            "author": {"id": "https://openalex.org/A001", "display_name": "Jared Kaplan"},
            "institutions": [
                {"id": "https://openalex.org/I001", "display_name": "Johns Hopkins University"}
            ],
        },
        {
            "author": {"id": "https://openalex.org/A002", "display_name": "Sam McCandlish"},
            "institutions": [
                {"id": "https://openalex.org/I002", "display_name": "OpenAI"}
            ],
        },
        {
            "author": {"id": "https://openalex.org/A003", "display_name": "Tom Henighan"},
            "institutions": [
                {"id": "https://openalex.org/I002", "display_name": "OpenAI"}
            ],
        },
    ],
    "primary_location": {
        "source": {"display_name": "Nature"},
        "pdf_url": "https://arxiv.org/pdf/2001.08361",
    },
    "open_access": {
        "oa_url": "https://arxiv.org/abs/2001.08361",
    },
    "referenced_works": [
        "https://openalex.org/W100",
        "https://openalex.org/W200",
        "https://openalex.org/W300",
    ],
    "concepts": [
        {"display_name": "Scaling", "score": 0.95},
        {"display_name": "Language model", "score": 0.91},
        {"display_name": "Neural network", "score": 0.88},
        {"display_name": "Deep learning", "score": 0.82},
        {"display_name": "Machine learning", "score": 0.78},
        {"display_name": "Artificial intelligence", "score": 0.65},
        {"display_name": "Computer science", "score": 0.55},
    ],
}


def test_openalex_registers():
    from packages.sources.registry import get_source

    cls = get_source("openalex")
    assert cls is OpenAlexSource


def test_parse_basic():
    source = OpenAlexSource(config={"mailto": "test@example.com"})
    raw = SourceRawItem(
        source_id="https://openalex.org/W2741809807",
        fetched_at=datetime(2024, 6, 15),
        payload=SAMPLE_WORK,
    )
    item = source.parse(raw)

    assert item.source == "openalex"
    assert item.source_id == "https://openalex.org/W2741809807"
    assert item.kind == "paper"
    assert item.title == "Scaling Laws for Neural Language Models"
    assert item.doi == "10.1038/s41586-024-07386-0"
    assert item.venue == "Nature"
    assert item.published_at == datetime(2024, 3, 15)
    assert item.url == "https://doi.org/10.1038/s41586-024-07386-0"
    assert item.pdf_url == "https://arxiv.org/pdf/2001.08361"


def test_parse_authors():
    source = OpenAlexSource(config={})
    raw = SourceRawItem(
        source_id="https://openalex.org/W2741809807",
        fetched_at=datetime(2024, 6, 15),
        payload=SAMPLE_WORK,
    )
    item = source.parse(raw)

    assert item.authors == ["Jared Kaplan", "Sam McCandlish", "Tom Henighan"]


def test_parse_affiliations_deduplicated():
    source = OpenAlexSource(config={})
    raw = SourceRawItem(
        source_id="https://openalex.org/W2741809807",
        fetched_at=datetime(2024, 6, 15),
        payload=SAMPLE_WORK,
    )
    item = source.parse(raw)

    # OpenAI appears twice in authorships but should be deduplicated
    assert item.affiliations == ["Johns Hopkins University", "OpenAI"]


def test_parse_citations():
    source = OpenAlexSource(config={})
    raw = SourceRawItem(
        source_id="https://openalex.org/W2741809807",
        fetched_at=datetime(2024, 6, 15),
        payload=SAMPLE_WORK,
    )
    item = source.parse(raw)

    assert item.citations == [
        "https://openalex.org/W100",
        "https://openalex.org/W200",
        "https://openalex.org/W300",
    ]


def test_parse_tags_top_5():
    source = OpenAlexSource(config={})
    raw = SourceRawItem(
        source_id="https://openalex.org/W2741809807",
        fetched_at=datetime(2024, 6, 15),
        payload=SAMPLE_WORK,
    )
    item = source.parse(raw)

    # Top 5 by score, should not include "Artificial intelligence" or "Computer science"
    assert len(item.tags) == 5
    assert item.tags == ["Scaling", "Language model", "Neural network", "Deep learning", "Machine learning"]


def test_reconstruct_abstract():
    inverted_index = {
        "We": [0],
        "study": [1],
        "empirical": [2],
        "scaling": [3],
        "laws": [4],
        "for": [5, 11],
        "neural": [6],
        "language": [7],
        "model": [8],
        "performance": [9],
        "and": [10],
        "transfer.": [12],
    }
    result = reconstruct_abstract(inverted_index)
    assert result == "We study empirical scaling laws for neural language model performance and for transfer."


def test_reconstruct_abstract_none():
    assert reconstruct_abstract(None) is None
    assert reconstruct_abstract({}) is None


def test_parse_missing_abstract():
    work = {
        "id": "https://openalex.org/W999",
        "display_name": "No Abstract Paper",
        "authorships": [],
        "concepts": [],
    }
    source = OpenAlexSource(config={})
    raw = SourceRawItem(
        source_id="https://openalex.org/W999",
        fetched_at=datetime(2024, 6, 15),
        payload=work,
    )
    item = source.parse(raw)

    assert item.title == "No Abstract Paper"
    assert item.abstract is None
    assert item.authors == []
    assert item.affiliations == []
    assert item.doi is None
    assert item.venue is None
    assert item.pdf_url is None
    assert item.tags == []


def test_parse_url_fallback_to_openalex_id():
    """When DOI is absent, URL should fall back to the OpenAlex ID."""
    work = {
        "id": "https://openalex.org/W12345",
        "display_name": "No DOI Paper",
        "authorships": [],
        "concepts": [],
    }
    source = OpenAlexSource(config={})
    raw = SourceRawItem(
        source_id="https://openalex.org/W12345",
        fetched_at=datetime(2024, 6, 15),
        payload=work,
    )
    item = source.parse(raw)

    assert item.url == "https://openalex.org/W12345"
    assert item.doi is None


def test_parse_pdf_url_fallback_to_oa_url():
    """When primary_location has no pdf_url, fall back to open_access.oa_url."""
    work = {
        "id": "https://openalex.org/W555",
        "display_name": "OA Paper",
        "primary_location": {
            "source": {"display_name": "ArXiv"},
        },
        "open_access": {
            "oa_url": "https://arxiv.org/abs/2401.99999",
        },
        "authorships": [],
        "concepts": [],
    }
    source = OpenAlexSource(config={})
    raw = SourceRawItem(
        source_id="https://openalex.org/W555",
        fetched_at=datetime(2024, 6, 15),
        payload=work,
    )
    item = source.parse(raw)

    assert item.pdf_url == "https://arxiv.org/abs/2401.99999"
    assert item.venue == "ArXiv"
