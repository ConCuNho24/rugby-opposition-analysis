from __future__ import annotations

import pandas as pd

from week11_analysis.analysis.insights import generate_key_insights
from week11_analysis.analysis.kicking import (
    kick_position_distribution,
    kick_receipt_contest_status,
)
from week11_analysis.analysis.linebreaks import (
    linebreak_achieved_conceded_summary,
    opponent_initial_break_events,
)
from week11_analysis.analysis.tackling import (
    dominant_tackle_outcome_matrix,
    evaded_tackles_by_associated_player,
    first_tackler_missed_by_player,
    player_tackle_outcome_matrix,
)
from week11_analysis.data.transformation import transform_partner_events


def test_associated_player_fields_transform_without_discarding_source_linkage() -> None:
    raw = pd.DataFrame(
        [
            {
                "ID": 1,
                "FXID": 1,
                "teamName": "Defenders",
                "playerName": "Tackler",
                "MatchTime": 100,
                "period": 1,
                "x_coord": 20,
                "y_coord": 30,
                "actionName": "Missed Tackle",
                "ActionTypeName": "Stepped",
                "ActionResultName": "Tackled",
                "assoc_player": 99,
                "assoc_playerName": "Evader",
                "assoc_playerTeam": 2,
                "assoc_playerTeamName": "Attackers",
                "assoc_event_id": 88,
            }
        ]
    )

    event = transform_partner_events(raw).iloc[0]

    assert event["associated_player_id"] == 99
    assert event["associated_player_name"] == "Evader"
    assert event["associated_player_team_id"] == 2
    assert event["associated_player_team_name"] == "Attackers"
    assert event["associated_event_id"] == 88


def test_kick_position_and_recorded_receipt_status_use_source_fields(partner_rows) -> None:
    rows = partner_rows.copy()
    kick_mask = rows["actionName"].eq("Kick")
    rows.loc[kick_mask, "playerpositionName"] = ["Scrum Half", "Fly Half"]
    rows.loc[kick_mask, "qualifier5Name"] = [
        "Kick Receipt Contested",
        "Kick Receipt Not Contested",
    ]
    events = transform_partner_events(rows)

    positions = kick_position_distribution(events, "NSW Waratahs")
    statuses = kick_receipt_contest_status(events, "NSW Waratahs")

    assert positions.to_dict("records") == [
        {"player_position_name": "Fly Half", "count": 1, "percentage": 50.0},
        {"player_position_name": "Scrum Half", "count": 1, "percentage": 50.0},
    ]
    assert statuses.to_dict("records") == [
        {"contest_status": "Contested", "count": 1, "percentage": 50.0},
        {"contest_status": "Not Contested", "count": 1, "percentage": 50.0},
    ]
    assert kick_position_distribution(events, "No source team").empty
    assert kick_receipt_contest_status(events, "No source team").empty


def test_missing_kick_receipt_qualifier_is_not_silently_classified_as_not_contested() -> None:
    raw = pd.DataFrame(
        [
            {
                "ID": 1, "FXID": 1, "teamName": "Team A", "playerName": "Kicker",
                "MatchTime": 101, "period": 1, "x_coord": 20, "y_coord": 30,
                "actionName": "Kick", "ActionTypeName": "Box", "ActionResultName": "Kick in Play",
            }
        ]
    )

    status = kick_receipt_contest_status(transform_partner_events(raw), "Team A")

    assert status.to_dict("records") == [
        {"contest_status": "Not recorded / other", "count": 1, "percentage": 100.0}
    ]


def test_evasion_summary_uses_linked_attacker_and_subtypes() -> None:
    raw = pd.DataFrame(
        [
            {
                "ID": 1, "FXID": 1, "teamName": "Defenders", "playerName": "Tackler A",
                "MatchTime": 101, "period": 1, "x_coord": 20, "y_coord": 30,
                "actionName": "Missed Tackle", "ActionTypeName": "Bumped Off",
                "ActionResultName": "Tackled", "assoc_playerName": "Evader One",
            },
            {
                "ID": 2, "FXID": 1, "teamName": "Defenders", "playerName": "Tackler B",
                "MatchTime": 102, "period": 1, "x_coord": 20, "y_coord": 30,
                "actionName": "Missed Tackle", "ActionTypeName": "Stepped",
                "ActionResultName": "Tackled", "assoc_playerName": "Evader One",
            },
            {
                "ID": 3, "FXID": 1, "teamName": "Defenders", "playerName": "Tackler C",
                "MatchTime": 103, "period": 1, "x_coord": 20, "y_coord": 30,
                "actionName": "Missed Tackle", "ActionTypeName": "Unusual source label",
                "ActionResultName": "Tackled", "assoc_playerName": "Evader Two",
            },
            {
                "ID": 4, "FXID": 1, "teamName": "Defenders", "playerName": "Tackler D",
                "MatchTime": 104, "period": 1, "x_coord": 20, "y_coord": 30,
                "actionName": "Missed Tackle", "ActionTypeName": "Outpaced",
                "ActionResultName": "Tackled", "assoc_playerName": None,
            },
        ]
    )
    summary = evaded_tackles_by_associated_player(transform_partner_events(raw), "Defenders")

    assert summary["associated_player_name"].tolist() == ["Evader One", "Evader Two"]
    assert summary["evaded_tackles"].tolist() == [2, 1]
    assert summary.loc[0, "Bumped Off"] == 1
    assert summary.loc[0, "Stepped"] == 1
    assert summary.loc[1, "Other"] == 1
    subtype_columns = [column for column in summary.columns if column not in {"associated_player_name", "evaded_tackles"}]
    assert (summary[subtype_columns].sum(axis=1) == summary["evaded_tackles"]).all()


def test_player_tackle_outcomes_first_tackler_and_dominant_filters_are_strict() -> None:
    raw = pd.DataFrame(
        [
            {
                "ID": 1, "FXID": 1, "teamName": "Team A", "playerName": "Player One",
                "MatchTime": 101, "period": 1, "x_coord": 20, "y_coord": 30,
                "actionName": "Tackle", "ActionResultName": "Complete",
                "qualifier5Name": "1st Tackler", "qualifier4Name": "Dominant Tackle",
            },
            {
                "ID": 2, "FXID": 1, "teamName": "Team A", "playerName": "Player One",
                "MatchTime": 102, "period": 1, "x_coord": 20, "y_coord": 30,
                "actionName": "Tackle", "ActionResultName": "Missed",
                "qualifier5Name": "1st Tackler", "qualifier4Name": "Ineffective Tackle",
            },
            {
                "ID": 3, "FXID": 1, "teamName": "Team A", "playerName": "Player Two",
                "MatchTime": 103, "period": 1, "x_coord": 20, "y_coord": 30,
                "actionName": "Tackle", "ActionResultName": "Passive",
                "qualifier5Name": "2nd Tackler", "qualifier4Name": "Dominant Tackle",
            },
        ]
    )
    events = transform_partner_events(raw)
    matrix = player_tackle_outcome_matrix(events, "Team A", sort_by="Missed")
    dominant = dominant_tackle_outcome_matrix(events, "Team A")

    assert matrix.iloc[0]["player_name"] == "Player One"
    assert matrix["total_tackle_actions"].sum() == 3
    assert matrix[["Complete", "Missed", "Passive"]].sum().sum() == 3
    assert first_tackler_missed_by_player(events, "Team A").to_dict("records") == [
        {"player_name": "Player One", "count": 1, "percentage": 100.0}
    ]
    assert dominant["dominant_tackle_records"].sum() == 2
    assert set(dominant["player_name"]) == {"Player One", "Player Two"}


def test_linebreak_achieved_and_conceded_are_team_level_source_ownership() -> None:
    raw = pd.DataFrame(
        [
            {
                "ID": 1, "FXID": 1, "teamName": "Team A", "playerName": "A One",
                "MatchTime": 101, "period": 1, "x_coord": 20, "y_coord": 30,
                "actionName": "Attacking Qualities", "ActionTypeName": "Initial Break",
                "ActionResultName": "Line Break",
            },
            {
                "ID": 2, "FXID": 1, "teamName": "Team A", "playerName": "A Two",
                "MatchTime": 102, "period": 1, "x_coord": 20, "y_coord": 30,
                "actionName": "Attacking Qualities", "ActionTypeName": "Initial Break",
                "ActionResultName": "Line Break",
            },
            {
                "ID": 3, "FXID": 1, "teamName": "Team B", "playerName": "B One",
                "MatchTime": 103, "period": 1, "x_coord": 20, "y_coord": 30,
                "actionName": "Attacking Qualities", "ActionTypeName": "Initial Break",
                "ActionResultName": "Kick Line Break",
            },
            {
                "ID": 4, "FXID": 1, "teamName": "Team B", "playerName": "B Helper",
                "MatchTime": 104, "period": 1, "x_coord": 20, "y_coord": 30,
                "actionName": "Attacking Qualities", "ActionTypeName": "Break Assist",
                "ActionResultName": "Line Break",
            },
        ]
    )
    events = transform_partner_events(raw)

    assert linebreak_achieved_conceded_summary(events, "Team A").to_dict("records") == [
        {"view": "Linebreaks achieved", "source_team": "Team A", "count": 2},
        {"view": "Linebreaks conceded", "source_team": "Team B", "count": 1},
    ]
    assert len(opponent_initial_break_events(events, "Team A")) == 1


def test_insights_use_specific_breakdown_tackle_and_tie_safe_linebreak_text() -> None:
    raw = pd.DataFrame(
        [
            {
                "ID": 1, "FXID": 1, "teamName": "Team A", "playerName": "Kicker",
                "MatchTime": 101, "period": 1, "x_coord": 20, "y_coord": 30,
                "actionName": "Kick", "ActionTypeName": "Box", "ActionResultName": "Kick in Play",
            },
            {
                "ID": 2, "FXID": 1, "teamName": "Team A", "playerName": "Halfback",
                "MatchTime": 102, "period": 1, "x_coord": 20, "y_coord": 30,
                "actionName": "Playmaker Options", "ActionTypeName": "Halfback at Breakdown",
                "ActionResultName": "Playmaker Option - Pass",
            },
            {
                "ID": 3, "FXID": 1, "teamName": "Team A", "playerName": "Tackler",
                "MatchTime": 103, "period": 1, "x_coord": 20, "y_coord": 30,
                "actionName": "Tackle", "ActionResultName": "Complete",
            },
            {
                "ID": 4, "FXID": 1, "teamName": "Team A", "playerName": "Break One",
                "MatchTime": 104, "period": 1, "x_coord": 20, "y_coord": 30,
                "actionName": "Attacking Qualities", "ActionTypeName": "Initial Break",
                "ActionResultName": "Line Break",
            },
            {
                "ID": 5, "FXID": 1, "teamName": "Team A", "playerName": "Break Two",
                "MatchTime": 105, "period": 1, "x_coord": 20, "y_coord": 30,
                "actionName": "Attacking Qualities", "ActionTypeName": "Initial Break",
                "ActionResultName": "Line Break",
            },
        ]
    )
    insights = generate_key_insights(transform_partner_events(raw), "Team A")
    texts = [insight.text for insight in insights]

    assert any("Pass from Halfback at Breakdown" in text for text in texts)
    assert any("Complete was the most common recorded Tackle outcome" in text for text in texts)
    assert any("2 players recorded one Initial Break each" in text for text in texts)
