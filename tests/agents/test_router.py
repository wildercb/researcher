"""Tests for chat router intent detection."""

from packages.agents.router import detect_intent


def test_detect_briefing():
    assert detect_intent("Give me a briefing on recent papers") == "briefing"
    assert detect_intent("What's new in my field?") == "briefing"
    assert detect_intent("Daily digest please") == "briefing"


def test_detect_ideation():
    assert detect_intent("What research directions should I explore?") == "ideation"
    assert detect_intent("Help me brainstorm ideas") == "ideation"
    assert detect_intent("Generate some research ideas") == "ideation"


def test_detect_fit():
    assert detect_intent("Where does my idea about X fit?") == "fit"
    assert detect_intent("How novel is this approach?") == "fit"
    assert detect_intent("What's the related work for this?") == "fit"


def test_detect_trends():
    assert detect_intent("What topics are trending?") == "trends"
    assert detect_intent("Show me emerging research areas") == "trends"


def test_detect_general():
    assert detect_intent("Tell me about transformer architectures") == "general"
    assert detect_intent("What is BERT?") == "general"
    assert detect_intent("Hello") == "general"
