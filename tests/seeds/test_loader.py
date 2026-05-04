"""Tests for seed loader."""



from packages.core.types import SeedType
from packages.seeds.loader import SeedEntry, classify_identifier, load_seeds, save_seeds


def test_load_empty_file(tmp_path):
    path = tmp_path / "seeds.yaml"
    path.write_text("papers: []\nauthors: []\nvenues: []\nkeywords: []\n")
    seeds = load_seeds(path)
    assert seeds == []


def test_load_papers_doi(tmp_path):
    path = tmp_path / "seeds.yaml"
    path.write_text('papers:\n  - doi: "10.1145/3442188.3445922"\n')
    seeds = load_seeds(path)
    assert len(seeds) == 1
    assert seeds[0].seed_type == SeedType.PAPER
    assert seeds[0].identifier == "10.1145/3442188.3445922"
    assert seeds[0].label.startswith("DOI:")


def test_load_papers_arxiv(tmp_path):
    path = tmp_path / "seeds.yaml"
    path.write_text('papers:\n  - arxiv: "2310.06825"\n')
    seeds = load_seeds(path)
    assert len(seeds) == 1
    assert seeds[0].identifier == "2310.06825"
    assert seeds[0].label.startswith("arXiv:")


def test_load_papers_title(tmp_path):
    path = tmp_path / "seeds.yaml"
    path.write_text('papers:\n  - title: "Attention is All You Need"\n')
    seeds = load_seeds(path)
    assert len(seeds) == 1
    assert seeds[0].identifier == "Attention is All You Need"


def test_load_authors(tmp_path):
    path = tmp_path / "seeds.yaml"
    path.write_text('authors:\n  - name: "Yann LeCun"\n    orcid: "0000-0001"\n')
    seeds = load_seeds(path)
    assert len(seeds) == 1
    assert seeds[0].seed_type == SeedType.AUTHOR
    assert seeds[0].identifier == "Yann LeCun"
    assert seeds[0].metadata.get("orcid") == "0000-0001"


def test_load_venues(tmp_path):
    path = tmp_path / "seeds.yaml"
    path.write_text('venues:\n  - name: "NeurIPS"\n')
    seeds = load_seeds(path)
    assert len(seeds) == 1
    assert seeds[0].seed_type == SeedType.VENUE
    assert seeds[0].identifier == "NeurIPS"


def test_load_keywords(tmp_path):
    path = tmp_path / "seeds.yaml"
    path.write_text('keywords:\n  - term: "mechanistic interpretability"\n    weight: 1.5\n')
    seeds = load_seeds(path)
    assert len(seeds) == 1
    assert seeds[0].seed_type == SeedType.KEYWORD
    assert seeds[0].weight == 1.5


def test_load_negative_seeds(tmp_path):
    path = tmp_path / "seeds.yaml"
    path.write_text('negative:\n  authors:\n    - "Bad Author"\n  topics:\n    - "Crypto"\n')
    seeds = load_seeds(path)
    assert len(seeds) == 2
    assert all(s.is_negative for s in seeds)


def test_save_and_reload(tmp_path):
    path = tmp_path / "seeds.yaml"
    original = [
        SeedEntry(SeedType.PAPER, "10.1234/test", "DOI:10.1234/test"),
        SeedEntry(SeedType.AUTHOR, "Alice", "Alice", metadata={"orcid": "0000"}),
        SeedEntry(SeedType.VENUE, "ICML", "ICML"),
        SeedEntry(SeedType.KEYWORD, "transformers", "transformers", weight=1.5),
        SeedEntry(SeedType.NEGATIVE, "Bad Topic", "NOT: Bad Topic", is_negative=True, metadata={"original_type": "topic"}),
    ]
    save_seeds(path, original)
    reloaded = load_seeds(path)
    assert len(reloaded) == 5
    types = {s.seed_type for s in reloaded}
    assert SeedType.PAPER in types
    assert SeedType.AUTHOR in types
    assert SeedType.VENUE in types
    assert SeedType.KEYWORD in types
    assert SeedType.NEGATIVE in types


def test_classify_identifier():
    assert classify_identifier("10.1145/3442188.3445922") == "doi"
    assert classify_identifier("2310.06825") == "arxiv"
    assert classify_identifier("arxiv:2310.06825") == "arxiv"
    assert classify_identifier("Attention is All You Need") == "title"


def test_load_nonexistent_file():
    seeds = load_seeds("/nonexistent/path/seeds.yaml")
    assert seeds == []
