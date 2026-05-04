"""Tests for eval harness."""

from packages.eval.harness import list_datasets, load_dataset, run_eval_offline, score_contains
from packages.eval.scoring import contains_all, contains_any, exact_match, in_range


def test_load_dataset():
    dataset = load_dataset("relevance_scorer")
    assert len(dataset) >= 10
    assert "input" in dataset[0]


def test_load_nonexistent_dataset():
    dataset = load_dataset("nonexistent_agent")
    assert dataset == []


def test_list_datasets():
    datasets = list_datasets()
    assert "relevance_scorer" in datasets
    assert "summarizer" in datasets
    assert "briefing_writer" in datasets


def test_run_eval_offline():
    result = run_eval_offline("relevance_scorer")
    assert result.total >= 10
    assert result.pass_rate > 0


def test_score_contains():
    assert score_contains("The Transformer model uses attention", ["transformer", "attention"])
    assert not score_contains("Simple model", ["transformer"])


def test_exact_match():
    assert exact_match("hello", "hello") == 1.0
    assert exact_match("hello", "world") == 0.0


def test_contains_all():
    assert contains_all("hello world foo", ["hello", "world"]) == 1.0
    assert contains_all("hello", ["hello", "world"]) == 0.0


def test_contains_any():
    assert contains_any("hello world", ["hello", "missing"]) == 0.5


def test_in_range():
    assert in_range(0.7, 0.5, 1.0) == 1.0
    assert in_range(0.3, 0.5, 1.0) == 0.0
