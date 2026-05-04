"""Tests for feedback loop drift computation."""

import pytest

from packages.core.models import FeedbackEvent, Item
from packages.seeds.feedback_loop import apply_drift_to_profile, compute_drift


@pytest.mark.asyncio
async def test_compute_drift_positive(storage):
    async with storage.session() as session:
        item = Item(
            source="test", source_id="drift-1", kind="paper",
            title="Liked Paper", url="https://example.com", raw={},
            tags=["ML", "NLP"], authors=["Alice"], venue="NeurIPS",
        )
        session.add(item)
        await session.flush()

        session.add(FeedbackEvent(item_id=item.id, signal="liked"))

    async with storage.session() as session:
        drift = await compute_drift(session)
        assert drift["event_count"] == 1
        assert drift["tag_drift"].get("ML", 0) > 0
        assert drift["author_drift"].get("Alice", 0) > 0
        assert drift["venue_drift"].get("NeurIPS", 0) > 0


@pytest.mark.asyncio
async def test_compute_drift_negative(storage):
    async with storage.session() as session:
        item = Item(
            source="test", source_id="drift-2", kind="paper",
            title="Hidden Paper", url="https://example.com", raw={},
            tags=["Crypto"], authors=["Bad Author"],
        )
        session.add(item)
        await session.flush()

        session.add(FeedbackEvent(item_id=item.id, signal="hidden"))

    async with storage.session() as session:
        drift = await compute_drift(session)
        assert drift["tag_drift"].get("Crypto", 0) < 0


def test_apply_drift_bounded(tmp_path):
    profile = {
        "tag_affinities": {"ML": 1.0, "NLP": 0.5},
        "author_affinities": {"Alice": 1.0},
        "venue_affinities": {"NeurIPS": 1.0},
        "relevance_weights": {},
        "drift": {"feedback_events": 0, "last_updated": None},
    }
    drift = {
        "tag_drift": {"ML": 10.0, "NewTopic": 5.0},
        "author_drift": {},
        "venue_drift": {},
        "event_count": 5,
    }
    path = tmp_path / "interest.yaml"
    updated = apply_drift_to_profile(profile, drift, output_path=path)

    # ML should be bounded — not exceed 1.0
    assert updated["tag_affinities"]["ML"] <= 1.0
    # NewTopic should appear but bounded
    assert "NewTopic" in updated["tag_affinities"]
    assert updated["tag_affinities"]["NewTopic"] <= 0.3  # MAX_DRIFT_RATIO
    assert updated["drift"]["feedback_events"] == 5
