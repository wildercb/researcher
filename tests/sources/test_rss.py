from datetime import datetime

from packages.sources.base import SourceRawItem
from packages.sources.rss import RSSSource


def test_rss_registers():
    from packages.sources.registry import get_source

    cls = get_source("rss")
    assert cls is RSSSource


def test_parse_blog_entry():
    source = RSSSource(config={"feeds": [{"name": "ML Blog", "url": "https://example.com/rss"}]})
    raw = SourceRawItem(
        source_id="rss:ML Blog:https://example.com/post-1",
        fetched_at=datetime(2024, 6, 15),
        payload={
            "feed_name": "ML Blog",
            "feed_url": "https://example.com/rss",
            "title": "Understanding Attention Mechanisms",
            "link": "https://example.com/post-1",
            "summary": "A deep dive into attention mechanisms in transformers.",
            "author": "Jane Doe",
            "published": "Mon, 10 Jun 2024 10:00:00 GMT",
            "tags": [{"term": "machine-learning"}, {"term": "attention"}],
        },
    )
    item = source.parse(raw)
    assert item.title == "Understanding Attention Mechanisms"
    assert item.abstract == "A deep dive into attention mechanisms in transformers."
    assert item.authors == ["Jane Doe"]
    assert item.venue == "ML Blog"
    assert item.kind == "blog"
    assert item.url == "https://example.com/post-1"
    assert "machine-learning" in item.tags
    assert item.source == "rss"


def test_parse_non_blog():
    source = RSSSource(config={"feeds": [{"name": "ArXiv Feed", "url": "https://example.com"}]})
    raw = SourceRawItem(
        source_id="rss:ArXiv Feed:123",
        fetched_at=datetime(2024, 6, 15),
        payload={
            "feed_name": "ArXiv Feed",
            "title": "New Paper",
            "link": "https://arxiv.org/abs/2401.00001",
            "summary": "Abstract text.",
        },
    )
    item = source.parse(raw)
    assert item.kind == "post"  # not "blog" since feed_name doesn't contain "blog"


def test_parse_missing_author():
    source = RSSSource(config={"feeds": []})
    raw = SourceRawItem(
        source_id="rss:test:1",
        fetched_at=datetime(2024, 6, 15),
        payload={
            "feed_name": "test",
            "title": "No Author Post",
            "link": "https://example.com",
        },
    )
    item = source.parse(raw)
    assert item.authors == []


def test_parse_date_from_parsed_tuple():
    source = RSSSource(config={"feeds": []})
    raw = SourceRawItem(
        source_id="rss:test:2",
        fetched_at=datetime(2024, 6, 15),
        payload={
            "feed_name": "test",
            "title": "Tuple Date",
            "link": "https://example.com",
            "published_parsed": [2024, 6, 10, 12, 0, 0, 0, 162, 0],
        },
    )
    item = source.parse(raw)
    assert item.published_at == datetime(2024, 6, 10, 12, 0, 0)
