from __future__ import annotations

import pandas as pd

from week11_analysis.analysis.game_intervals import (
    interval_label_from_minutes,
    recorded_event_intervals,
    try_action_intervals,
)
from week11_analysis.analysis.insights import generate_key_insights
from week11_analysis.analysis.linebreaks import (
    initial_break_events,
    initial_break_results,
    offload_passes_by_player,
)
from week11_analysis.data.transformation import transform_partner_events


def test_initial_break_and_offload_filters_are_explicit() -> None:
    rows = pd.DataFrame(
        [
            {
                "ID": 1, "FXID": 1, "teamName": "Team A", "playerName": "Breaker",
                "playerpositionName": "Wing", "MatchTime": 101, "period": 1,
                "x_coord": 62, "y_coord": 30, "actionName": "Attacking Qualities",
                "ActionTypeName": "Initial Break", "ActionResultName": "Line Break",
            },
            {
                "ID": 2, "FXID": 1, "teamName": "Team A", "playerName": "Helper",
                "MatchTime": 102, "period": 1, "x_coord": 63, "y_coord": 31,
                "actionName": "Attacking Qualities", "ActionTypeName": "Break Assist",
                "ActionResultName": "Line Break",
            },
            {
                "ID": 3, "FXID": 1, "teamName": "Team A", "playerName": "Offloader",
                "MatchTime": 103, "period": 1, "x_coord": 64, "y_coord": 32,
                "actionName": "Pass", "ActionTypeName": "Offload", "ActionResultName": "Own Player",
            },
        ]
    )
    events = transform_partner_events(rows)

    assert len(initial_break_events(events, "Team A")) == 1
    assert initial_break_results(events, "Team A").iloc[0]["source_result"] == "Line Break"
    assert offload_passes_by_player(events, "Team A").iloc[0]["player_name"] == "Offloader"


def test_intervals_handle_boundaries_and_malformed_mmss(partner_rows) -> None:
    events = transform_partner_events(partner_rows)
    events.loc[events.index[0], "match_time_raw"] = 5960  # Invalid mmss; must not enter a band.
    intervals = recorded_event_intervals(events, "NSW Waratahs")
    tries = try_action_intervals(events, "NSW Waratahs")

    assert intervals.to_dict("records") == [{"interval": "40-50", "count": 6}]
    assert tries.empty
    labels = interval_label_from_minutes(pd.Series([0, 9, 10, 79, 80, None]))
    assert labels.tolist() == ["00-10", "00-10", "10-20", "70-80", "80+", pd.NA]


def test_insights_are_empty_safe_and_source_bound(partner_rows) -> None:
    events = transform_partner_events(partner_rows)
    insights = generate_key_insights(events, "NSW Waratahs")

    assert any(item.module == "Kicking" for item in insights)
    assert any("Playmaker Option records" in item.text for item in insights)
    assert generate_key_insights(events.iloc[:0], "No team") == []
