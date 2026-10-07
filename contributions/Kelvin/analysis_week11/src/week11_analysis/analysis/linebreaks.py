"""Source-labelled attacking-break and offload views.

The partner file has no standalone, validated universal "linebreak" event
schema.  This module therefore exposes only the explicit `Attacking Qualities`
records whose source type is `Initial Break`, together with their source result
labels.  It never links defensive records to a conceded break.
"""

from __future__ import annotations

import pandas as pd


ATTACKING_QUALITIES_ACTION = "Attacking Qualities"
INITIAL_BREAK_TYPE = "Initial Break"
OFFLOAD_PASS_TYPE = "Offload"


def _count_and_percentage(events: pd.DataFrame, group_column: str, output_label: str) -> pd.DataFrame:
    columns = [output_label, "count", "percentage"]
    if events.empty or group_column not in events.columns:
        return pd.DataFrame(columns=columns)
    usable = events.dropna(subset=[group_column])
    if usable.empty:
        return pd.DataFrame(columns=columns)
    summary = (
        usable.groupby(group_column)
        .size()
        .rename("count")
        .reset_index()
        .rename(columns={group_column: output_label})
        .sort_values(["count", output_label], ascending=[False, True], kind="stable")
        .reset_index(drop=True)
    )
    summary["percentage"] = summary["count"] / summary["count"].sum() * 100
    return summary.loc[:, columns]


def initial_break_events(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Return only source `Attacking Qualities` / `Initial Break` records."""

    selected = events.loc[
        events["action_name"].eq(ATTACKING_QUALITIES_ACTION)
        & events["action_type_name"].eq(INITIAL_BREAK_TYPE)
    ].copy()
    if team_name is not None:
        selected = selected.loc[selected["team_name"].eq(team_name)].copy()
    return selected


def initial_break_results(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Count source result labels for the selected Initial Break subset."""

    return _count_and_percentage(initial_break_events(events, team_name), "action_result_name", "source_result")


def initial_breaks_by_player(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Count source Initial Break records by the source-recorded player."""

    return _count_and_percentage(initial_break_events(events, team_name), "player_name", "player_name")


def initial_breaks_by_position(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Count only supplied source player-position labels for Initial Break rows."""

    return _count_and_percentage(
        initial_break_events(events, team_name), "player_position_name", "player_position_name"
    )


def initial_break_locations(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Return preserved Initial Break coordinates for a source-relative pitch map."""

    return initial_break_events(events, team_name).dropna(subset=["x", "y"]).copy()


def opponent_initial_break_events(events: pd.DataFrame, team_name: str) -> pd.DataFrame:
    """Return Initial Break rows recorded for other teams in the supplied fixture frame.

    Pages pass one selected fixture into this module. At that fixture level,
    these source-owned opponent events are a transparent team-level measure of
    breaks conceded by the selected team; no individual defender is inferred.
    """

    return initial_break_events(events).loc[
        lambda frame: frame["team_name"].notna() & ~frame["team_name"].eq(team_name)
    ].copy()


def linebreak_achieved_conceded_summary(events: pd.DataFrame, team_name: str) -> pd.DataFrame:
    """Compare selected-team Initial Break rows with source-owned opponent rows."""

    achieved = initial_break_events(events, team_name)
    conceded = opponent_initial_break_events(events, team_name)
    opponent_names = sorted({str(value) for value in conceded["team_name"].dropna().unique()})
    return pd.DataFrame(
        [
            {
                "view": "Linebreaks achieved",
                "source_team": team_name,
                "count": len(achieved),
            },
            {
                "view": "Linebreaks conceded",
                "source_team": ", ".join(opponent_names) if opponent_names else "No opponent records",
                "count": len(conceded),
            },
        ]
    )


def initial_break_results_from_records(records: pd.DataFrame) -> pd.DataFrame:
    """Count Initial Break source results from an already-selected side of a fixture."""

    return _count_and_percentage(records, "action_result_name", "source_result")


def initial_breaks_by_player_from_records(records: pd.DataFrame) -> pd.DataFrame:
    """Count source-recorded Initial Break players from a selected side."""

    return _count_and_percentage(records, "player_name", "player_name")


def initial_breaks_by_position_from_records(records: pd.DataFrame) -> pd.DataFrame:
    """Count supplied Initial Break positions from a selected side."""

    return _count_and_percentage(records, "player_position_name", "player_position_name")


def offload_pass_events(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Return `Pass` records labelled `Offload` by the data source."""

    selected = events.loc[
        events["action_name"].eq("Pass") & events["action_type_name"].eq(OFFLOAD_PASS_TYPE)
    ].copy()
    if team_name is not None:
        selected = selected.loc[selected["team_name"].eq(team_name)].copy()
    return selected


def offload_passes_by_player(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Count source-offload pass rows by source-recorded player."""

    return _count_and_percentage(offload_pass_events(events, team_name), "player_name", "player_name")
