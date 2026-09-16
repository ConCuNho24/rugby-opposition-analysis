"""Event frequency and fixture-context metrics on canonical events only."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

import pandas as pd


def metadata_dict(value: object) -> dict[str, Any]:
    """Safely decode canonical metadata persisted as JSON text."""
    if isinstance(value, dict):
        return value
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return decoded if isinstance(decoded, dict) else {}


def fixture_context(events: pd.DataFrame) -> pd.DataFrame:
    """Return one record per source match with real fixture metadata, when available."""
    records: list[dict[str, object]] = []
    if events.empty:
        return pd.DataFrame(
            columns=[
                "match_id",
                "fixture_label",
                "match_date",
                "round",
                "home_team",
                "away_team",
                "home_final_score",
                "away_final_score",
                "event_count",
            ]
        )
    for match_id, group in events.groupby("match_id", sort=True):
        metadata = metadata_dict(group.iloc[0].get("metadata", ""))
        records.append(
            {
                "match_id": match_id,
                "fixture_label": metadata.get("fixture_label") or "Fixture metadata unavailable",
                "match_date": metadata.get("match_date"),
                "round": metadata.get("round"),
                "home_team": metadata.get("home_team"),
                "away_team": metadata.get("away_team"),
                "home_final_score": metadata.get("home_final_score"),
                "away_final_score": metadata.get("away_final_score"),
                "event_count": len(group),
            }
        )
    return pd.DataFrame(records)


def available_teams(events: pd.DataFrame) -> list[str]:
    """List real event teams when available, otherwise fixture metadata teams."""
    if "team_name" in events.columns:
        attributed = sorted(
            value for value in events["team_name"].dropna().astype(str).unique().tolist() if value.strip()
        )
        if attributed:
            return attributed
    context = fixture_context(events)
    values = set(context["home_team"].dropna().astype(str)) | set(context["away_team"].dropna().astype(str))
    return sorted(value for value in values if value.strip())


def events_for_fixture_team(events: pd.DataFrame, team_name: str, match_ids: Iterable[str] | None = None) -> pd.DataFrame:
    """Select annotations from fixtures involving ``team_name``.

    Important: this does not claim that a selected event belongs to the team. The
    selected public data lacks team attribution at event level, so the caller must
    label outputs as fixture-context observations.
    """
    context = fixture_context(events)
    context_matches = context.loc[
        (context["home_team"] == team_name) | (context["away_team"] == team_name), "match_id"
    ].tolist()
    if match_ids is not None:
        requested = set(match_ids)
        context_matches = [match_id for match_id in context_matches if match_id in requested]
    return events[events["match_id"].isin(context_matches)].copy()


def events_for_team(events: pd.DataFrame, team_name: str, match_ids: Iterable[str] | None = None) -> pd.DataFrame:
    """Return genuinely team-attributed events where the source supplies them.

    Sources without event team attribution return an empty frame rather than
    borrowing fixture membership. Call :func:`events_for_fixture_team` explicitly
    if an analyst intentionally needs fixture-context annotations.
    """
    selected = events.loc[events["team_name"] == team_name].copy()
    if match_ids is not None:
        selected = selected[selected["match_id"].isin(set(match_ids))]
    return selected


def event_counts(events: pd.DataFrame) -> pd.DataFrame:
    """Count supported event types, highest first."""
    if events.empty:
        return pd.DataFrame(columns=["event_type", "event_count"])
    return (
        events.groupby("event_type", dropna=False)
        .size()
        .rename("event_count")
        .reset_index()
        .sort_values("event_count", ascending=False, kind="stable")
        .reset_index(drop=True)
    )


def event_rates_per_match(events: pd.DataFrame) -> pd.DataFrame:
    """Return per-match event rates and their sample denominator."""
    match_count = events["match_id"].nunique() if not events.empty else 0
    counts = event_counts(events)
    if match_count == 0:
        counts["matches"] = pd.Series(dtype="int")
        counts["events_per_match"] = pd.Series(dtype="float")
        return counts
    counts["matches"] = match_count
    counts["events_per_match"] = counts["event_count"] / match_count
    return counts


def match_by_match_profile(events: pd.DataFrame) -> pd.DataFrame:
    """Pivot event counts by source match for a trend chart/table."""
    if events.empty:
        return pd.DataFrame(columns=["match_id"])
    profile = pd.crosstab(events["match_id"], events["event_type"]).reset_index()
    return profile.sort_values("match_id", kind="stable").reset_index(drop=True)
