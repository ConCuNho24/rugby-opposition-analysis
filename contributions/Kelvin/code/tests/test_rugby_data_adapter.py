from __future__ import annotations

from pathlib import Path

from rugby_analysis.adapters.rugby_data import RugbyDataJsonAdapter


def test_rugby_data_adapter_maps_score_lineup_and_discipline_events(rugby_raw_root: Path) -> None:
    adapter = RugbyDataJsonAdapter(rugby_raw_root)
    files = adapter.discover_files(rugby_raw_root)

    assert [path.name for path in files] == ["fixture.json"]
    # The acquisition step uses the stable source-derived ID as the filename.
    # A hand-written test fixture is deliberately named ``fixture.json``.
    assert adapter.match_id_for_file(files[0]) == "fixture"

    events = adapter.normalize_file(files[0])

    # Five scoring records, two substitutions, and one yellow card.
    assert len(events) == 8
    assert [event.sequence_index for event in events] == list(range(8))
    assert {event.team_name for event in events} == {"Alpha RFC", "Beta RFC"}

    opening_try = next(event for event in events if event.event_type == "try" and event.team_name == "Alpha RFC")
    assert opening_try.timestamp_seconds == 300
    assert opening_try.player_name == "Alice Flyhalf"
    assert opening_try.outcome == "scored"
    assert opening_try.metadata["score_value"] == 5
    assert opening_try.metadata["home_final_score"] == 12
    assert opening_try.metadata["away_final_score"] == 5

    missed_penalty = next(event for event in events if event.event_type == "missed_penalty")
    assert missed_penalty.outcome == "missed"
    assert missed_penalty.metadata["event_category"] == "scoring"

    cards = [event for event in events if event.event_type == "yellow_card"]
    assert len(cards) == 1
    assert cards[0].timestamp_seconds == 42 * 60
    assert cards[0].metadata["event_category"] == "discipline"

    assert adapter.validate(events) == [
        "Home source score-event values total 10, but published final score is 12; "
        "final-score and event-value metrics remain separate."
    ]
