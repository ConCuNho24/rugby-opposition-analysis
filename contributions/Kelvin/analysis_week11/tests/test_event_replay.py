from __future__ import annotations

import pandas as pd
import pytest

from week11_analysis.analysis.event_replay import (
    build_replay_sequence,
    current_event_metadata,
    event_path,
    filter_replay_events,
    has_recorded_location,
    order_replay_events,
    recent_event_trail,
    replay_actions,
)


@pytest.fixture
def replay_events() -> pd.DataFrame:
    """Recorded-event rows from two uploaded fixture sources."""

    return pd.DataFrame(
        [
            {
                "event_id": 101,
                "fixture_id": 1001,
                "team_name": "Team A",
                "player_name": "Player One",
                "start_seconds": 10.0,
                "source_order": 2,
                "match_clock": "00:10",
                "action_name": "Kick",
                "action_type_name": "Box",
                "action_result_name": "In Play",
                "x": 12.5,
                "y": 7.25,
                "x_end": 80.0,
                "y_end": 32.0,
                "qualifier_3_name": "Kick Receipt Contested",
                "source_file_name": "fixture-1001.xlsx",
            },
            {
                "event_id": 102,
                "fixture_id": 1001,
                "team_name": "Team A",
                "player_name": "Player Two",
                "start_seconds": 10.0,
                "source_order": 1,
                "match_clock": "00:10",
                "action_name": "Tackle",
                "action_type_name": "Line",
                "action_result_name": "Complete",
                "x": 34.0,
                "y": 40.0,
                "x_end": pd.NA,
                "y_end": pd.NA,
                "qualifier_4_name": "Dominant Tackle",
                "source_file_name": "fixture-1001.xlsx",
            },
            {
                "event_id": 103,
                "fixture_id": 1001,
                "team_name": "Team A",
                "player_name": "Player Three",
                "start_seconds": pd.NA,
                "source_order": 0,
                "match_clock": "00:11",
                "action_name": "Attacking Qualities",
                "action_type_name": "Initial Break",
                "action_result_name": "Line Break",
                "x": pd.NA,
                "y": pd.NA,
                "x_end": pd.NA,
                "y_end": pd.NA,
                "source_file_name": "fixture-1001.xlsx",
            },
            {
                "event_id": 104,
                "fixture_id": 1001,
                "team_name": "Team B",
                "player_name": "Opponent",
                "start_seconds": 4.0,
                "source_order": 0,
                "match_clock": "00:04",
                "action_name": "Kick",
                "x": 50.0,
                "y": 30.0,
                "source_file_name": "fixture-1001.xlsx",
            },
            {
                "event_id": 201,
                "fixture_id": 2002,
                "team_name": "Team A",
                "player_name": "Other Fixture Player",
                "start_seconds": 1.0,
                "source_order": 0,
                "match_clock": "00:01",
                "action_name": "Kick",
                "x": 101.0,
                "y": 20.0,
                "x_end": 103.0,
                "y_end": 25.0,
                "source_file_name": "fixture-2002.csv",
            },
        ]
    )


def test_replay_orders_timestamps_then_uses_stable_source_order(replay_events: pd.DataFrame) -> None:
    sequence = build_replay_sequence(replay_events, fixture_id=1001, team_name="Team A")

    # 101 and 102 share a timestamp: lower original source_order comes first.
    # The event without ps_timestamp/start_seconds remains a timeline row last.
    assert sequence["event_id"].tolist() == [102, 101, 103]
    assert sequence["match_clock"].tolist() == ["00:10", "00:10", "00:11"]
    assert sequence["replay_event_index"].tolist() == [0, 1, 2]


def test_order_accepts_ps_timestamp_when_called_before_transformation() -> None:
    raw_named_events = pd.DataFrame(
        {
            "event_id": [1, 2, 3],
            "ps_timestamp": [8.0, 4.0, 8.0],
            "source_order": [1, 0, 0],
        }
    )

    ordered = order_replay_events(raw_named_events)

    assert ordered["event_id"].tolist() == [2, 3, 1]


def test_fixture_team_and_action_filters_use_recorded_source_labels(replay_events: pd.DataFrame) -> None:
    team_events = filter_replay_events(replay_events, fixture_id=1001, team_name="Team A")
    kick_events = build_replay_sequence(
        replay_events, fixture_id=1001, team_name="Team A", action_filter="Kick"
    )
    initial_break_events = build_replay_sequence(
        replay_events, fixture_id=1001, team_name="Team A", action_filter="Initial Break"
    )

    assert team_events["event_id"].tolist() == [101, 102, 103]
    assert kick_events["event_id"].tolist() == [101]
    assert initial_break_events["event_id"].tolist() == [103]
    assert replay_actions(replay_events, fixture_id=1001, team_name="Team A") == [
        "Attacking Qualities",
        "Box",
        "Initial Break",
        "Kick",
        "Line",
        "Tackle",
    ]


def test_period_prevents_halves_from_interleaving_after_a_timestamp_jump() -> None:
    events = pd.DataFrame(
        {
            "event_id": [1, 2],
            "period": [2, 1],
            "start_seconds": [1.0, 99.0],
            "source_order": [0, 1],
        }
    )

    ordered = order_replay_events(events)

    assert ordered["event_id"].tolist() == [2, 1]


def test_missing_coordinates_stay_in_timeline_without_creating_a_path(replay_events: pd.DataFrame) -> None:
    sequence = build_replay_sequence(replay_events, fixture_id=1001, team_name="Team A")
    missing_location = sequence.loc[sequence["event_id"].eq(103)].iloc[0]

    assert not has_recorded_location(missing_location)
    assert event_path(missing_location) is None
    metadata = current_event_metadata(sequence, event_index=2)
    assert metadata is not None
    assert metadata["has_recorded_location"] is False
    assert metadata["start_coordinates"] is None
    assert metadata["end_coordinates"] is None


def test_path_contains_only_one_event_start_and_end_with_source_coordinates(
    replay_events: pd.DataFrame,
) -> None:
    sequence = build_replay_sequence(replay_events, fixture_id=1001, team_name="Team A")
    kick = sequence.loc[sequence["event_id"].eq(101)].iloc[0]

    path = event_path(kick)

    assert path is not None
    assert path.to_dict("records") == [
        {"x": 12.5, "y": 7.25, "point": "Start"},
        {"x": 80.0, "y": 32.0, "point": "End"},
    ]
    # A source event with no recorded end location cannot imply movement.
    assert event_path(sequence.loc[sequence["event_id"].eq(102)].iloc[0]) is None


def test_replay_never_creates_positions_between_separate_source_events(
    replay_events: pd.DataFrame,
) -> None:
    sequence = build_replay_sequence(replay_events, fixture_id=1001, team_name="Team A")

    # The sequence has one row per source event; it does not create frames
    # between events 102 and 101 despite both having recorded locations.
    assert sequence["event_id"].tolist() == [102, 101, 103]
    assert len(sequence) == 3
    assert event_path(sequence.iloc[1])["point"].tolist() == ["Start", "End"]


def test_current_metadata_is_compact_and_marks_out_of_range_source_locations(
    replay_events: pd.DataFrame,
) -> None:
    sequence = build_replay_sequence(replay_events, fixture_id=2002, team_name="Team A")

    metadata = current_event_metadata(sequence, event_index=0)

    assert metadata == {
        "event_number": 1,
        "event_count": 1,
        "event_id": 201,
        "fixture_id": 2002,
        "match_time": "00:01",
        "team_name": "Team A",
        "player_name": "Other Fixture Player",
        "action_name": "Kick",
        "action_type_name": None,
        "action_result_name": None,
        "start_coordinates": (101.0, 20.0),
        "end_coordinates": (103.0, 25.0),
        "has_recorded_location": True,
        "location_within_nominal_field": False,
        "recorded_qualifiers": [],
        "source_file_name": "fixture-2002.csv",
    }


def test_current_metadata_keeps_recorded_qualifiers_and_coordinates(replay_events: pd.DataFrame) -> None:
    sequence = build_replay_sequence(replay_events, fixture_id=1001, team_name="Team A")

    metadata = current_event_metadata(sequence, event_index=1)

    assert metadata is not None
    assert metadata["player_name"] == "Player One"
    assert metadata["action_name"] == "Kick"
    assert metadata["start_coordinates"] == (12.5, 7.25)
    assert metadata["end_coordinates"] == (80.0, 32.0)
    assert metadata["recorded_qualifiers"] == ["Kick Receipt Contested"]


def test_recent_trail_uses_only_prior_recorded_rows_and_fixture_isolation(
    replay_events: pd.DataFrame,
) -> None:
    sequence = build_replay_sequence(replay_events, fixture_id=1001, team_name="Team A")

    trail = recent_event_trail(sequence, event_index=2, limit=5)

    assert trail["event_id"].tolist() == [102, 101]
    assert set(sequence["source_file_name"]) == {"fixture-1001.xlsx"}
    assert 201 not in sequence["event_id"].tolist()
    assert recent_event_trail(sequence, event_index=0, limit=5).empty
