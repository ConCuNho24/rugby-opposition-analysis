"""Focused tackling analysis from explicitly labelled partner event records."""

from __future__ import annotations

import pandas as pd


TACKLE_ACTION_NAME = "Tackle"
MISSED_TACKLE_ACTION_NAME = "Missed Tackle"
FIRST_TACKLER_QUALIFIER = "1st Tackler"
DOMINANT_TACKLE_QUALIFIER = "Dominant Tackle"
EVADE_SUBTYPE_ORDER = ("Bumped Off", "Stepped", "Outpaced", "Positional")


def _count_and_percentage(
    events: pd.DataFrame, group_column: str, output_label: str
) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame(columns=[output_label, "count", "percentage"])
    usable = events.dropna(subset=[group_column]).copy()
    if usable.empty:
        return pd.DataFrame(columns=[output_label, "count", "percentage"])
    summary = (
        usable.groupby(group_column)
        .size()
        .rename("count")
        .reset_index()
        .rename(columns={group_column: output_label})
        .sort_values("count", ascending=False, kind="stable")
        .reset_index(drop=True)
    )
    summary["percentage"] = summary["count"] / summary["count"].sum() * 100
    return summary


def tackle_events(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Return the source's tackle action rows without adding other defensive events."""

    selected = events.loc[events["action_name"].eq(TACKLE_ACTION_NAME)].copy()
    if team_name is not None:
        selected = selected.loc[selected["team_name"].eq(team_name)].copy()
    return selected


def missed_tackle_events(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Return explicit Missed Tackle rows, kept distinct from tackle outcomes."""

    selected = events.loc[events["action_name"].eq(MISSED_TACKLE_ACTION_NAME)].copy()
    if team_name is not None:
        selected = selected.loc[selected["team_name"].eq(team_name)].copy()
    return selected


def tackle_outcome_distribution(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Summarise result labels for actionName == Tackle only."""

    return _count_and_percentage(tackle_events(events, team_name), "action_result_name", "tackle_outcome")


def missed_tackles_by_player(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Count explicit Missed Tackle records by the source-recorded player."""

    return _count_and_percentage(missed_tackle_events(events, team_name), "player_name", "player_name")


def tackle_locations(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Return recorded tackle start locations for the pitch map."""

    return tackle_events(events, team_name).dropna(subset=["x", "y"]).copy()


def first_tackler_outcomes(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Summarise tackles whose qualifier explicitly labels the player first tackler."""

    selected = tackle_events(events, team_name)
    selected = selected.loc[
        selected["qualifier_5_name"].eq(FIRST_TACKLER_QUALIFIER)
    ].copy()
    return _count_and_percentage(selected, "action_result_name", "tackle_outcome")


def tackle_height_distribution(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Summarise source qualifier 6 labels, when this field is populated."""

    return _count_and_percentage(tackle_events(events, team_name), "qualifier_6_name", "tackle_height")


def missed_tackle_player_positions(
    events: pd.DataFrame, team_name: str | None = None
) -> pd.DataFrame:
    """Summarise explicit missed-tackle rows by supplied player and position."""

    selected = missed_tackle_events(events, team_name).dropna(
        subset=["player_name", "player_position_name"]
    )
    columns = ["player_name", "player_position_name", "count", "percentage"]
    if selected.empty:
        return pd.DataFrame(columns=columns)
    summary = (
        selected.groupby(["player_name", "player_position_name"])
        .size()
        .rename("count")
        .reset_index()
        .sort_values(["count", "player_name"], ascending=[False, True], kind="stable")
        .reset_index(drop=True)
    )
    summary["percentage"] = summary["count"] / summary["count"].sum() * 100
    return summary.loc[:, columns]


def first_tackler_missed_by_player(
    events: pd.DataFrame, team_name: str | None = None
) -> pd.DataFrame:
    """Count source ``Tackle`` rows marked both ``Missed`` and ``1st Tackler``."""

    selected = tackle_events(events, team_name).loc[
        lambda frame: frame["action_result_name"].eq("Missed")
        & frame["qualifier_5_name"].eq(FIRST_TACKLER_QUALIFIER)
    ].copy()
    return _count_and_percentage(selected, "player_name", "player_name")


def dominant_tackle_by_player(
    events: pd.DataFrame, team_name: str | None = None
) -> pd.DataFrame:
    """Count only the explicit source qualifier ``Dominant Tackle`` by player."""

    selected = tackle_events(events, team_name).loc[
        lambda frame: frame["qualifier_4_name"].eq(DOMINANT_TACKLE_QUALIFIER)
    ].copy()
    return _count_and_percentage(selected, "player_name", "player_name")


def player_tackle_outcome_matrix(
    events: pd.DataFrame,
    team_name: str | None = None,
    sort_by: str = "total_tackle_actions",
) -> pd.DataFrame:
    """Pivot source Tackle outcomes by the source-recorded tackling player.

    Outcome columns are discovered from the selected source rows. This avoids
    inventing a fixed set of rugby outcomes while retaining every observed
    source label. Blank player or outcome fields are clearly marked rather
    than dropped from the action total.
    """

    selected = tackle_events(events, team_name)
    base_columns = ["player_name", "total_tackle_actions"]
    if selected.empty:
        return pd.DataFrame(columns=base_columns)
    prepared = selected.assign(
        _player=selected["player_name"].fillna("Not recorded"),
        _outcome=selected["action_result_name"].fillna("Not recorded"),
    )
    matrix = pd.crosstab(prepared["_player"], prepared["_outcome"], dropna=False)
    matrix.index.name = "player_name"
    matrix = matrix.reset_index()
    outcome_columns = [column for column in matrix.columns if column != "player_name"]
    matrix.insert(1, "total_tackle_actions", matrix[outcome_columns].sum(axis=1).astype(int))
    effective_sort = sort_by if sort_by in matrix.columns else "total_tackle_actions"
    return (
        matrix.sort_values(
            [effective_sort, "total_tackle_actions", "player_name"],
            ascending=[False, False, True],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def dominant_tackle_outcome_matrix(
    events: pd.DataFrame, team_name: str | None = None
) -> pd.DataFrame:
    """Pivot explicit Dominant Tackle qualifier rows by player and source outcome."""

    selected = tackle_events(events, team_name).loc[
        lambda frame: frame["qualifier_4_name"].eq(DOMINANT_TACKLE_QUALIFIER)
    ].copy()
    base_columns = ["player_name", "dominant_tackle_records"]
    if selected.empty:
        return pd.DataFrame(columns=base_columns)
    prepared = selected.assign(
        _player=selected["player_name"].fillna("Not recorded"),
        _outcome=selected["action_result_name"].fillna("Not recorded"),
    )
    matrix = pd.crosstab(prepared["_player"], prepared["_outcome"], dropna=False)
    matrix.index.name = "player_name"
    matrix = matrix.reset_index()
    outcome_columns = [column for column in matrix.columns if column != "player_name"]
    matrix.insert(1, "dominant_tackle_records", matrix[outcome_columns].sum(axis=1).astype(int))
    return (
        matrix.sort_values(
            ["dominant_tackle_records", "player_name"], ascending=[False, True], kind="stable"
        )
        .reset_index(drop=True)
    )


def evaded_tackles_by_associated_player(
    events: pd.DataFrame, defensive_team_name: str | None = None
) -> pd.DataFrame:
    """Summarise source-linked attackers from explicit Missed Tackle rows.

    In the representative workbook, the row's ``player_name`` is the source
    tackler and ``associated_player_name`` is populated with the opposing
    player linked to that missed-tackle record. Selecting ``defensive_team_name``
    therefore yields the source-linked players who evaded that team's records.
    Rows missing an associated player cannot support this table and are safely
    excluded rather than attributed to the tackler.
    """

    selected = missed_tackle_events(events, defensive_team_name).dropna(
        subset=["associated_player_name"]
    )
    base_columns = ["associated_player_name", "evaded_tackles"]
    if selected.empty:
        return pd.DataFrame(columns=base_columns)
    subtype = selected["action_type_name"].where(
        selected["action_type_name"].isin(EVADE_SUBTYPE_ORDER), "Other"
    )
    prepared = selected.assign(_subtype=subtype)
    matrix = pd.crosstab(prepared["associated_player_name"], prepared["_subtype"], dropna=False)
    matrix.index.name = "associated_player_name"
    matrix = matrix.reset_index()
    subtype_columns = [column for column in EVADE_SUBTYPE_ORDER if column in matrix.columns]
    if "Other" in matrix.columns:
        subtype_columns.append("Other")
    matrix = matrix.loc[:, ["associated_player_name", *subtype_columns]]
    matrix.insert(1, "evaded_tackles", matrix[subtype_columns].sum(axis=1).astype(int))
    return (
        matrix.sort_values(
            ["evaded_tackles", "associated_player_name"], ascending=[False, True], kind="stable"
        )
        .reset_index(drop=True)
    )


def tackle_summary_cards(events: pd.DataFrame, team_name: str | None = None) -> dict[str, object]:
    """Return source-backed tackle card values while preserving event-type separation."""

    selected = tackle_events(events, team_name)
    outcomes = tackle_outcome_distribution(events, team_name)
    missed_inside = selected.loc[selected["action_result_name"].eq("Missed")]
    return {
        "total": len(selected),
        "common_outcome": outcomes.iloc[0]["tackle_outcome"] if not outcomes.empty else "Not recorded",
        "missed_tackle_outcomes": len(missed_inside),
        "explicit_missed_actions": len(missed_tackle_events(events, team_name)),
    }
