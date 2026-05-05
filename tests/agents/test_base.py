"""Tests for agent base — prompt loading."""

import pytest

from packages.agents.base import get_prompt_version, load_prompt


def test_load_prompt_summarizer():
    prompt = load_prompt("summarizer", "v1")
    assert "2 sentences" in prompt


def test_load_prompt_relevance_scorer():
    prompt = load_prompt("relevance_scorer", "v1")
    assert "0.0 to 1.0" in prompt


def test_load_prompt_briefing_writer():
    prompt = load_prompt("briefing_writer", "v1")
    assert "Key Trends" in prompt


def test_load_prompt_ideation_agent():
    prompt = load_prompt("ideation_agent", "v1")
    assert "research directions" in prompt


def test_load_prompt_fit_agent():
    prompt = load_prompt("fit_agent", "v1")
    assert "Novelty" in prompt


def test_load_prompt_trend_detector():
    prompt = load_prompt("trend_detector", "v1")
    assert "velocity" in prompt


def test_load_prompt_not_found():
    with pytest.raises(FileNotFoundError):
        load_prompt("nonexistent_agent", "v1")


def test_get_prompt_version():
    version = get_prompt_version("summarizer")
    assert version == "v1"
