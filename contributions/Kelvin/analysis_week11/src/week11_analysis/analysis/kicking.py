"""Kicking analysis based only on source rows explicitly labelled ``Kick``."""

from __future__ import annotations

import pandas as pd


KICK_ACTION_NAME = "Kick"
CONTEST_STATUS_MAP = {
    "Kick Receipt Contested": "Contested",
    "Kick Receipt Not Contested": "Not Contested",
}


def kick_events(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Return source kick records, optionally for one team.

    ``Goal Kick`` and ``Defensive Exits`` are deliberately not merged into this
    subset.  They are separate source action names, so treating their records
    as the same physical kick category would be an unsupported assumption.
    """

    selected = events.loc[events["action_name"].eq(KICK_ACTION_NAME)].copy()
    if team_name is not None:
        selected = selected.loc[selected["team_name"].eq(team_name)].copy()
    return selected


def _count_and_percentage(
    events: pd.DataFrame, group_column: str, output_label: str
) -> pd.DataFrame:
    """Create a source-label count and percentage table with safe empty output."""

    empty = pd.DataFrame(columns=[output_label, "count", "percentage"])
    if events.empty or group_column not in events.columns:
        return empty
    usable = events.dropna(subset=[group_column]).copy()
    if usable.empty:
        return empty
    summary = (
        usable.groupby(group_column, dropna=True)
        .size()
        .rename("count")
        .reset_index()
        .rename(columns={group_column: output_label})
        .sort_values("count", ascending=False, kind="stable")
        .reset_index(drop=True)
    )
    summary["percentage"] = summary["count"] / summary["count"].sum() * 100
    return summary


def kick_type_distribution(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Count source kick types such as Box, Touch Kick, Territorial, Bomb, or Low."""

    return _count_and_percentage(kick_events(events, team_name), "action_type_name", "kick_type")


def kick_position_distribution(
    events: pd.DataFrame, team_name: str | None = None
) -> pd.DataFrame:
    """Count source-recorded player positions across the selected team's Kick rows.

    ``Not recorded`` is a display value for a blank source field, not an
    inferred rugby position. Percentages use every selected Kick row as their
    denominator so an incomplete position field remains visible.
    """

    selected = kick_events(events, team_name)
    columns = ["player_position_name", "count", "percentage"]
    if selected.empty:
        return pd.DataFrame(columns=columns)
    positions = selected["player_position_name"].fillna("Not recorded")
    summary = (
        positions.value_counts(dropna=False)
        .rename_axis("player_position_name")
        .rename("count")
        .reset_index()
        .sort_values(["count", "player_position_name"], ascending=[False, True], kind="stable")
        .reset_index(drop=True)
    )
    summary["percentage"] = summary["count"] / len(selected) * 100
    return summary.loc[:, columns]


def kick_receipt_contest_status(
    events: pd.DataFrame, team_name: str | None = None
) -> pd.DataFrame:
    """Summarise the source's recorded kick-receipt qualifier, without redefinition.

    The representative workbook records `Kick Receipt Contested` and `Kick
    Receipt Not Contested` in ``qualifier5Name`` on Kick rows. Any other or
    blank source value is surfaced as ``Not recorded / other`` rather than
    silently treated as not contested.
    """

    selected = kick_events(events, team_name)
    columns = ["contest_status", "count", "percentage"]
    if selected.empty:
        return pd.DataFrame(columns=columns)
    status = selected["qualifier_5_name"].map(CONTEST_STATUS_MAP).fillna("Not recorded / other")
    summary = (
        status.value_counts()
        .rename_axis("contest_status")
        .rename("count")
        .reset_index()
    )
    preferred_order = {"Contested": 0, "Not Contested": 1, "Not recorded / other": 2}
    summary["_order"] = summary["contest_status"].map(preferred_order).fillna(99)
    summary = summary.sort_values(["_order", "contest_status"], kind="stable").drop(columns="_order")
    summary["percentage"] = summary["count"] / len(selected) * 100
    return summary.reset_index(drop=True).loc[:, columns]


def kick_outcome_distribution(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Count only source-provided kick result labels; no success rule is inferred."""

    return _count_and_percentage(
        kick_events(events, team_name), "action_result_name", "kick_outcome"
    )


def kicker_summary(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Return source-recorded kick rows by player name."""

    return _count_and_percentage(kick_events(events, team_name), "player_name", "player_name")


def kick_locations(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Keep recorded kick start locations, including source labels for hover text."""

    return kick_events(events, team_name).dropna(subset=["x", "y"]).copy()


def kick_end_locations(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Return recorded kick end coordinates, without inferring a trajectory."""

    selected = kick_events(events, team_name).dropna(subset=["x_end", "y_end"]).copy()
    # The pitch helper deliberately consumes x/y.  Keep the source start fields
    # in the frame, while using its documented endpoint pair for this view.
    selected["x"] = selected["x_end"]
    selected["y"] = selected["y_end"]
    return selected


def kick_type_events(
    events: pd.DataFrame, team_name: str | None, kick_type: str
) -> pd.DataFrame:
    """Return a clearly labelled source kick-type subset without reclassification."""

    return kick_events(events, team_name).loc[
        lambda frame: frame["action_type_name"].eq(kick_type)
    ].copy()


def kick_summary_cards(events: pd.DataFrame, team_name: str | None = None) -> dict[str, object]:
    """Return small, deterministic source-label summaries for the UI."""

    selected = kick_events(events, team_name)
    types = kick_type_distribution(events, team_name)
    outcomes = kick_outcome_distribution(events, team_name)
    kickers = kicker_summary(events, team_name)
    return {
        "total": len(selected),
        "common_type": types.iloc[0]["kick_type"] if not types.empty else "Not recorded",
        "top_kicker": kickers.iloc[0]["player_name"] if not kickers.empty else "Not recorded",
        "common_outcome": outcomes.iloc[0]["kick_outcome"] if not outcomes.empty else "Not recorded",
    }
