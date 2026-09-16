"""Team- and player-attributed scoring analysis supported by Rugby-Data."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd


def _metadata(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def is_scoring_event(row: pd.Series) -> bool:
    return _metadata(row.get("metadata", "")).get("event_category") == "scoring"


def scoring_events(events: pd.DataFrame) -> pd.DataFrame:
    """Return only source records identified as score attempts/results."""
    if events.empty:
        return events.copy()
    return events.loc[events.apply(is_scoring_event, axis=1)].copy()


def score_value(events: pd.DataFrame) -> pd.Series:
    """Extract the real source-provided score value from canonical metadata."""
    return events["metadata"].map(lambda value: _metadata(value).get("score_value", 0)).pipe(
        pd.to_numeric, errors="coerce"
    ).fillna(0)


def scoring_breakdown(events: pd.DataFrame) -> pd.DataFrame:
    """Break down score event types, attempts, made outcomes and source values."""
    relevant = scoring_events(events)
    if relevant.empty:
        return pd.DataFrame(columns=["event_type", "attempts", "made", "missed", "points"])
    relevant = relevant.copy()
    relevant["points"] = score_value(relevant)
    result = relevant.groupby("event_type", dropna=False).agg(
        attempts=("event_id", "count"),
        made=("outcome", lambda values: int((values == "scored").sum())),
        missed=("outcome", lambda values: int((values == "missed").sum())),
        points=("points", "sum"),
    )
    return result.reset_index().sort_values("attempts", ascending=False, kind="stable").reset_index(drop=True)


def team_scoring_summary(events: pd.DataFrame, team_name: str) -> dict[str, object]:
    """Aggregate real score-event data for one selected team.

    ``source_score_event_value_total`` deliberately does not claim to be the
    official final-score total. In particular, the source represents a penalty
    try as a value of five even where the published final score includes the
    automatic conversion. ``official_final_score_*`` comes from fixture metadata
    and is available only for matches that have a canonical event timeline.
    """
    team_events = events.loc[events["team_name"] == team_name]
    selected = scoring_events(team_events)
    # Use every source fixture in which the team has a timeline record. Counting
    # only score attempts would inflate rates for a scoreless fixture.
    matches = team_events["match_id"].nunique()
    values = score_value(selected) if not selected.empty else pd.Series(dtype="float")
    source_score_event_value_total = float(values.sum()) if not values.empty else 0.0
    tries = int((selected["event_type"] == "try").sum()) if not selected.empty else 0
    attempts = len(selected)
    final_scores: list[float] = []
    for _, match_events in team_events.groupby("match_id", sort=False):
        metadata = _metadata(match_events.iloc[0].get("metadata", ""))
        if metadata.get("home_team") == team_name:
            final_score = metadata.get("home_final_score")
        elif metadata.get("away_team") == team_name:
            final_score = metadata.get("away_final_score")
        else:
            final_score = None
        parsed_score = pd.to_numeric(pd.Series([final_score]), errors="coerce").iloc[0]
        if pd.notna(parsed_score):
            final_scores.append(float(parsed_score))
    return {
        "team": team_name,
        "matches_with_event_timeline": matches,
        "scoring_events": attempts,
        "source_score_event_value_total": source_score_event_value_total,
        "source_score_event_value_per_match": source_score_event_value_total / matches if matches else 0.0,
        "official_final_score_matches": len(final_scores),
        "official_final_score_total": float(sum(final_scores)),
        "official_final_score_per_match": float(sum(final_scores)) / len(final_scores) if final_scores else 0.0,
        "tries": tries,
        "tries_per_match": tries / matches if matches else 0.0,
    }


def player_scoring_contributions(events: pd.DataFrame, team_name: str, top_n: int = 8) -> pd.DataFrame:
    """Rank player contribution using only player names present in public events."""
    selected = scoring_events(events.loc[(events["team_name"] == team_name) & events["player_name"].notna()]).copy()
    if selected.empty:
        return pd.DataFrame(
            columns=["player_name", "events", "source_score_event_value", "team_event_share", "team_value_share"]
        )
    selected["points"] = score_value(selected)
    total = len(selected)
    result = selected.groupby("player_name").agg(
        events=("event_id", "count"), source_score_event_value=("points", "sum")
    ).reset_index()
    result["team_event_share"] = result["events"] / total
    team_value = float(selected["points"].sum())
    result["team_value_share"] = result["source_score_event_value"] / team_value if team_value else 0.0
    return (
        result.sort_values(["source_score_event_value", "events"], ascending=False, kind="stable")
        .head(top_n)
        .reset_index(drop=True)
    )


def discipline_events(events: pd.DataFrame, team_name: str) -> pd.DataFrame:
    """Return source line-up card timeline records for a selected team."""
    selected = events.loc[(events["team_name"] == team_name) & events["event_type"].isin(["yellow_card", "red_card"])].copy()
    return selected.sort_values(["timestamp_seconds", "event_id"], kind="stable")
