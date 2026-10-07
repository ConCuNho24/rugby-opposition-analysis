from __future__ import annotations

import pandas as pd

from week11_analysis.data.transformation import match_clock_from_mmss, transform_partner_events


def test_match_clock_uses_partner_mmss_representation() -> None:
    rendered = match_clock_from_mmss(pd.Series([17, 4328, None, 7860]))

    assert rendered.iloc[0] == "00:17"
    assert rendered.iloc[1] == "43:28"
    assert pd.isna(rendered.iloc[2])
    assert pd.isna(rendered.iloc[3])


def test_coordinate_handling_preserves_team_relative_source_values(partner_rows) -> None:
    events = transform_partner_events(partner_rows)

    # The transformation intentionally does not flip a team's x coordinate.
    assert events.loc[events["event_id"].eq(1), "x"].iloc[0] == 25
    assert not events.loc[events["event_id"].eq(6), "coordinate_in_playing_area"].iloc[0]


def test_transformation_retains_later_qualifier_names() -> None:
    raw = pd.DataFrame(
        {
            "ID": [1],
            "FXID": [10],
            "teamName": ["Team A"],
            "MatchTime": [12],
            "period": [1],
            "x_coord": [20],
            "y_coord": [30],
            "actionName": ["Kick"],
            "qualifier8Name": ["Qualifier eight"],
            "qualifier9Name": ["Qualifier nine"],
            "qualifier10Name": ["Qualifier ten"],
        }
    )

    event = transform_partner_events(raw).iloc[0]

    assert event["qualifier_8_name"] == "Qualifier eight"
    assert event["qualifier_9_name"] == "Qualifier nine"
    assert event["qualifier_10_name"] == "Qualifier ten"
