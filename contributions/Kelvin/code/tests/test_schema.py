from __future__ import annotations

import pytest

from rugby_analysis.core.schema import CANONICAL_COLUMNS, CanonicalEvent


def test_canonical_event_round_trip_preserves_metadata_and_types() -> None:
    original = CanonicalEvent(
        source="public_source",
        match_id="match_001",
        event_id="match_001_0",
        sequence_index=3,
        event_type="try",
        period=2,
        timestamp_seconds=2451.5,
        team_name="Alpha RFC",
        player_name="Alice Flyhalf",
        outcome="scored",
        metadata={"score_value": 5, "nested": {"original": True}},
    )

    record = original.to_record()
    restored = CanonicalEvent.from_record(record)

    assert list(record) == CANONICAL_COLUMNS
    assert restored == original
    assert restored.metadata["nested"]["original"] is True


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"source": ""}, "source"),
        ({"match_id": ""}, "match_id"),
        ({"event_id": ""}, "event_id"),
        ({"sequence_index": -1}, "sequence_index"),
        ({"event_type": ""}, "event_type"),
        ({"timestamp_seconds": -0.1}, "timestamp_seconds"),
    ],
)
def test_canonical_event_rejects_invalid_required_values(kwargs: dict[str, object], message: str) -> None:
    values: dict[str, object] = {
        "source": "public_source",
        "match_id": "match_001",
        "event_id": "match_001_0",
        "sequence_index": 0,
        "event_type": "try",
    }
    values.update(kwargs)

    with pytest.raises(ValueError, match=message):
        CanonicalEvent(**values)  # type: ignore[arg-type]

