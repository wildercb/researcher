"""Scoring functions for eval harness."""

from __future__ import annotations


def exact_match(output: str, expected: str) -> float:
    """1.0 if exact match, 0.0 otherwise."""
    return 1.0 if output.strip() == expected.strip() else 0.0


def contains_all(output: str, terms: list[str]) -> float:
    """1.0 if all terms present (case-insensitive), 0.0 otherwise."""
    output_lower = output.lower()
    return 1.0 if all(t.lower() in output_lower for t in terms) else 0.0


def contains_any(output: str, terms: list[str]) -> float:
    """Fraction of terms present."""
    if not terms:
        return 1.0
    output_lower = output.lower()
    matches = sum(1 for t in terms if t.lower() in output_lower)
    return matches / len(terms)


def in_range(value: float, min_val: float, max_val: float = 1.0) -> float:
    """1.0 if value in [min_val, max_val], 0.0 otherwise."""
    return 1.0 if min_val <= value <= max_val else 0.0


def word_count_check(output: str, min_words: int = 10, max_words: int = 200) -> float:
    """1.0 if word count in range."""
    count = len(output.split())
    return 1.0 if min_words <= count <= max_words else 0.0
