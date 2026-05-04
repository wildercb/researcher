"""Tests for interest profile derivation."""

from packages.seeds.crawl import DiscoveredItem
from packages.seeds.interest import compute_relevance_score, derive_interest_profile


def _make_item(title="Paper", tags=None, authors=None, venue=None, hops=0):
    return DiscoveredItem(
        source="test",
        title=title,
        tags=tags or [],
        authors=authors or [],
        venue=venue,
        hops=hops,
        seed_id="test-seed",
        relation="seed",
    )


def test_derive_empty():
    profile = derive_interest_profile([], output_path="/tmp/test_interest.yaml")
    assert profile["tag_affinities"] == {}
    assert profile["author_affinities"] == {}
    assert profile["venue_affinities"] == {}


def test_derive_basic(tmp_path):
    items = [
        _make_item(tags=["ML", "NLP"], authors=["Alice"], venue="NeurIPS", hops=0),
        _make_item(tags=["ML", "CV"], authors=["Bob"], venue="ICML", hops=1),
        _make_item(tags=["ML"], authors=["Alice"], venue="NeurIPS", hops=0),
    ]
    path = tmp_path / "interest.yaml"
    profile = derive_interest_profile(items, output_path=path)

    assert "ML" in profile["tag_affinities"]
    assert profile["tag_affinities"]["ML"] == 1.0  # highest frequency
    assert "Alice" in profile["author_affinities"]
    assert "NeurIPS" in profile["venue_affinities"]
    assert profile["calibration"]["items_count"] == 3


def test_hop_weighting(tmp_path):
    items = [
        _make_item(tags=["Deep"], hops=0),  # weight 1.0
        _make_item(tags=["Shallow"], hops=2),  # weight 0.25
    ]
    path = tmp_path / "interest.yaml"
    profile = derive_interest_profile(items, output_path=path)

    assert profile["tag_affinities"]["Deep"] > profile["tag_affinities"]["Shallow"]


def test_relevance_scoring():
    profile = {
        "tag_affinities": {"ML": 1.0, "NLP": 0.8, "CV": 0.5},
        "author_affinities": {"Alice": 1.0, "Bob": 0.5},
        "venue_affinities": {"NeurIPS": 1.0, "ICML": 0.7},
        "relevance_weights": {
            "tag_overlap": 0.2,
            "author_affinity": 0.2,
            "venue_affinity": 0.1,
        },
    }

    # High relevance: matching tags, author, venue
    score = compute_relevance_score(["ML", "NLP"], ["Alice"], "NeurIPS", profile)
    assert score > 0.5

    # Low relevance: no matches
    score = compute_relevance_score(["Crypto"], ["Unknown"], "ArXiv", profile)
    assert score == 0.0

    # Medium relevance: partial match
    score = compute_relevance_score(["ML"], ["Bob"], None, profile)
    assert 0 < score < 1


def test_relevance_empty_profile():
    profile = {
        "tag_affinities": {},
        "author_affinities": {},
        "venue_affinities": {},
        "relevance_weights": {"tag_overlap": 0.2, "author_affinity": 0.2, "venue_affinity": 0.1},
    }
    score = compute_relevance_score(["ML"], ["Alice"], "NeurIPS", profile)
    assert score == 0.0
