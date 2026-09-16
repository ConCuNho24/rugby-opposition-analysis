"""Ordered event transition analysis using canonical sequence indexes."""

from __future__ import annotations

import pandas as pd


def transition_frequencies(events: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Count adjacent event-type transitions within each match."""
    if events.empty:
        return pd.DataFrame(columns=["from_event", "to_event", "transition_count", "share"])
    ordered = events.sort_values(["match_id", "sequence_index"], kind="stable").copy()
    ordered["next_match_id"] = ordered["match_id"].shift(-1)
    ordered["to_event"] = ordered["event_type"].shift(-1)
    transitions = ordered.loc[ordered["match_id"] == ordered["next_match_id"], ["event_type", "to_event"]]
    if transitions.empty:
        return pd.DataFrame(columns=["from_event", "to_event", "transition_count", "share"])
    counts = (
        transitions.rename(columns={"event_type": "from_event"})
        .groupby(["from_event", "to_event"])
        .size()
        .rename("transition_count")
        .reset_index()
        .sort_values("transition_count", ascending=False, kind="stable")
        .head(top_n)
        .reset_index(drop=True)
    )
    total = len(transitions)
    counts["share"] = counts["transition_count"] / total if total else 0.0
    return counts
