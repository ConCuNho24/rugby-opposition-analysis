"""Transparent time-banded descriptions of source event records.

The partner Q&A defines MatchTime as mmss.  Intervals here are therefore
descriptive groupings of recorded source rows, not ball-in-play calculations.
"""

from __future__ import annotations

import pandas as pd


def minute_from_match_time(values: pd.Series) -> pd.Series:
    """Extract source clock minutes from valid partner mmss values."""

    numeric = pd.to_numeric(values, errors="coerce")
    whole = numeric.where(numeric.ge(0)).round().astype("Int64")
    valid = whole.notna() & whole.mod(100).lt(60)
    return (whole // 100).where(valid, pd.NA).astype("Int64")


def interval_label_from_minutes(minutes: pd.Series, width: int = 10) -> pd.Series:
    """Create labels such as 00-10 and 10-20, with 80+ as the final rugby band."""

    if width <= 0:
        raise ValueError("Interval width must be positive.")
    values = pd.to_numeric(minutes, errors="coerce")
    starts = (values // width * width).astype("Int64")
    labels = starts.astype("string").str.zfill(2) + "-" + (starts + width).astype("string").str.zfill(2)
    labels = labels.where(starts.lt(80), starts.astype("string") + "+")
    return labels.where(values.notna() & values.ge(0), pd.NA)


def interval_events(
    events: pd.DataFrame, team_name: str | None = None, width: int = 10
) -> pd.DataFrame:
    """Attach source clock minute and transparent interval label to event rows."""

    selected = events.copy()
    if team_name is not None:
        selected = selected.loc[selected["team_name"].eq(team_name)].copy()
    selected["match_minute"] = minute_from_match_time(selected["match_time_raw"])
    selected["interval"] = interval_label_from_minutes(selected["match_minute"], width)
    return selected


def recorded_event_intervals(
    events: pd.DataFrame, team_name: str | None = None, width: int = 10
) -> pd.DataFrame:
    """Count all valid-clock source event rows by interval for one team or fixture."""

    selected = interval_events(events, team_name, width).dropna(subset=["interval"])
    columns = ["interval", "count"]
    if selected.empty:
        return pd.DataFrame(columns=columns)
    summary = selected.groupby("interval", sort=False).size().rename("count").reset_index()
    starts = summary["interval"].str.extract(r"^(\d+)", expand=False).astype(int)
    return summary.assign(_start=starts).sort_values("_start").drop(columns="_start").reset_index(drop=True)


def try_action_intervals(
    events: pd.DataFrame, team_name: str | None = None, width: int = 10
) -> pd.DataFrame:
    """Count rows explicitly labelled `Try` by source MatchTime interval.

    This is deliberately not converted into a score or a points total.
    """

    selected = interval_events(events, team_name, width)
    selected = selected.loc[selected["action_name"].eq("Try")].dropna(subset=["interval"])
    if selected.empty:
        return pd.DataFrame(columns=["interval", "count"])
    summary = selected.groupby("interval", sort=False).size().rename("count").reset_index()
    starts = summary["interval"].str.extract(r"^(\d+)", expand=False).astype(int)
    return summary.assign(_start=starts).sort_values("_start").drop(columns="_start").reset_index(drop=True)
