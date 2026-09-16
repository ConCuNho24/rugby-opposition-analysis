"""Time-oriented analyses supported by timestamped public annotations."""

from __future__ import annotations

import pandas as pd


TIME_BINS = [-0.001, 1200, 2400, 3600, float("inf")]
TIME_LABELS = ["0-20 min", "21-40 min", "41-60 min", "61+ min"]


def time_window_distribution(events: pd.DataFrame) -> pd.DataFrame:
    """Group events by recorded match-minute windows.

    The selected source records an event minute but no verified period or half
    boundary. These descriptive windows are not official half metrics.
    """
    if events.empty or "timestamp_seconds" not in events:
        return pd.DataFrame(columns=["time_window", "event_count", "share"])
    valid = events.copy()
    valid["timestamp_seconds"] = pd.to_numeric(valid["timestamp_seconds"], errors="coerce")
    valid = valid.dropna(subset=["timestamp_seconds"])
    if valid.empty:
        return pd.DataFrame(columns=["time_window", "event_count", "share"])
    valid["time_window"] = pd.cut(
        valid["timestamp_seconds"], bins=TIME_BINS, labels=TIME_LABELS, include_lowest=True
    )
    result = valid.groupby("time_window", observed=False).size().rename("event_count").reset_index()
    total = result["event_count"].sum()
    result["share"] = result["event_count"] / total if total else 0.0
    return result
