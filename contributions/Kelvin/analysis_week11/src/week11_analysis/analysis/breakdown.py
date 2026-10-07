"""Breakdown-choice analysis using the partner's Playmaker Options records."""

from __future__ import annotations

import pandas as pd

from .zones import ALL_ZONES_LABEL, DEFAULT_ZONE_CONFIG, FieldZoneConfig, assign_relative_field_zone


PLAYMAKER_ACTION_NAME = "Playmaker Options"
PLAYMAKER_RESULT_PREFIX = "Playmaker Option - "


def playmaker_option_events(events: pd.DataFrame, team_name: str | None = None) -> pd.DataFrame:
    """Select the source records that explicitly carry a playmaker decision."""

    selected = events.loc[
        events["action_name"].eq(PLAYMAKER_ACTION_NAME)
        & events["action_result_name"].astype("string").str.startswith(
            PLAYMAKER_RESULT_PREFIX, na=False
        )
    ].copy()
    if team_name is not None:
        selected = selected.loc[selected["team_name"].eq(team_name)].copy()
    selected["decision"] = (
        selected["action_result_name"].astype("string").str.removeprefix(PLAYMAKER_RESULT_PREFIX)
    )
    selected["receiver_context"] = selected["action_type_name"].fillna("Unspecified receiver")
    selected["decision_label"] = selected["decision"] + " from " + selected["receiver_context"]
    return selected


def breakdown_choice_table(
    events: pd.DataFrame,
    team_name: str | None = None,
    zone: str = ALL_ZONES_LABEL,
    zone_config: FieldZoneConfig = DEFAULT_ZONE_CONFIG,
) -> pd.DataFrame:
    """Return count/percentage by decision and receiver context for one zone.

    Percentages use the selected team's rows in the selected zone as their
    denominator.  The segmentation is configurable and explicitly not a claim
    about the partner's unresolved A/B/C/D/E zone convention.
    """

    selected = playmaker_option_events(events, team_name)
    selected["relative_field_zone"] = assign_relative_field_zone(selected, zone_config)
    if zone != ALL_ZONES_LABEL:
        selected = selected.loc[selected["relative_field_zone"].eq(zone)].copy()

    columns = ["decision", "receiver_context", "decision_label", "count", "percentage"]
    if selected.empty:
        return pd.DataFrame(columns=columns)
    summary = (
        selected.groupby(["decision", "receiver_context", "decision_label"], dropna=False)
        .size()
        .rename("count")
        .reset_index()
        .sort_values(["count", "decision_label"], ascending=[False, True], kind="stable")
        .reset_index(drop=True)
    )
    summary["percentage"] = summary["count"] / summary["count"].sum() * 100
    return summary.loc[:, columns]


def available_breakdown_zones(
    events: pd.DataFrame, zone_config: FieldZoneConfig = DEFAULT_ZONE_CONFIG
) -> list[str]:
    """Return the fixed configuration choices, retaining empty zones for clarity."""

    del events  # Zones come from transparent configuration, not inferred labels.
    return [ALL_ZONES_LABEL, *zone_config.labels]
