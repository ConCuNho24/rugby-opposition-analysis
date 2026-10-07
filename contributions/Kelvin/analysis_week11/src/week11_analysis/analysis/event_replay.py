"""Helpers for replaying recorded partner match events.

The partner feed records individual events, rather than continuous tracking
positions.  These helpers therefore preserve source rows and coordinates: they
filter and order the events for the replay UI, but never create positions
between them.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from math import isfinite
from typing import Any

import pandas as pd


Coordinate = tuple[float, float]

_QUALIFIER_COLUMNS = tuple(f"qualifier_{number}_name" for number in range(3, 11))
_NOMINAL_X_BOUNDS = (0.0, 100.0)
_NOMINAL_Y_BOUNDS = (0.0, 70.0)


def _require_columns(events: pd.DataFrame, columns: Iterable[str]) -> None:
    missing = [column for column in columns if column not in events.columns]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Replay events are missing required column(s): {joined}.")


def _normalise_filter_values(values: str | Iterable[str] | None) -> set[str] | None:
    if values is None:
        return None
    if isinstance(values, str):
        values = [values]

    cleaned = {text for value in values if (text := _optional_text(value)) is not None}
    return cleaned or None


def _matches_value(values: pd.Series, selected: object) -> pd.Series:
    """Match selector values without losing numeric fixture identifiers."""

    direct = values.eq(selected).fillna(False)
    if direct.any():
        return direct

    numeric_selected = pd.to_numeric(pd.Series([selected]), errors="coerce").iloc[0]
    if pd.notna(numeric_selected):
        numeric_matches = pd.to_numeric(values, errors="coerce").eq(numeric_selected).fillna(False)
        if numeric_matches.any():
            return numeric_matches

    return values.astype("string").eq(str(selected).strip()).fillna(False)


def _coordinate_value(value: object) -> float | None:
    """Return a finite numeric source coordinate, without changing its value."""

    if value is None or isinstance(value, bool):
        return None
    try:
        if pd.isna(value):
            return None
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if isfinite(numeric) else None


def _coordinates(event: Mapping[str, object], x_column: str, y_column: str) -> Coordinate | None:
    x = _coordinate_value(event.get(x_column))
    y = _coordinate_value(event.get(y_column))
    if x is None or y is None:
        return None
    return (x, y)


def _optional_text(value: object) -> str | None:
    value = _optional_value(value)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_value(value: object) -> object | None:
    """Convert pandas missing values to ``None`` for display-oriented output."""

    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        return None
    return value


def filter_replay_events(
    events: pd.DataFrame,
    fixture_id: object,
    team_name: str,
    action_filter: str | Iterable[str] | None = None,
) -> pd.DataFrame:
    """Keep recorded rows for one fixture, one team, and optional event labels.

    ``action_filter`` checks both source action and action-type labels.  This
    lets a selector use labels such as ``Kick`` as well as source-specific
    types such as ``Initial Break`` without inventing a new classification.
    """

    _require_columns(events, ("fixture_id", "team_name"))
    selected = events.loc[
        _matches_value(events["fixture_id"], fixture_id)
        & _matches_value(events["team_name"], team_name)
    ].copy()

    action_values = _normalise_filter_values(action_filter)
    if not action_values or selected.empty:
        return selected

    action_mask = pd.Series(False, index=selected.index)
    for column in ("action_name", "action_type_name"):
        if column in selected.columns:
            labels = selected[column].astype("string").str.strip()
            action_mask |= labels.isin(action_values).fillna(False)
    return selected.loc[action_mask].copy()


def order_replay_events(events: pd.DataFrame) -> pd.DataFrame:
    """Order source events by period and ``ps_timestamp`` with stable fallback.

    Transformed Week 11 events store ``ps_timestamp`` as ``start_seconds``.
    When source period is available, it keeps the two halves from interleaving
    if the coding timestamp jumps at halftime.  Tied or missing timestamps use
    ``source_order`` (or the supplied row order) as a stable fallback.  Match
    clock values remain display data; no source timing is repaired.
    """

    ordered = events.copy()
    if ordered.empty:
        ordered["replay_event_index"] = pd.Series(dtype="int64")
        return ordered

    timestamp = pd.Series(pd.NA, index=ordered.index, dtype="Float64")
    for column in ("start_seconds", "ps_timestamp"):
        if column in ordered.columns:
            source_timestamp = pd.to_numeric(ordered[column], errors="coerce")
            timestamp = timestamp.fillna(source_timestamp)
    ordered["_replay_timestamp"] = timestamp

    if "period" in ordered.columns:
        ordered["_replay_period"] = pd.to_numeric(ordered["period"], errors="coerce")
    else:
        ordered["_replay_period"] = pd.NA

    input_order = pd.Series(range(len(ordered)), index=ordered.index, dtype="int64")
    if "source_order" in ordered.columns:
        source_order = pd.to_numeric(ordered["source_order"], errors="coerce")
        ordered["_replay_source_order"] = source_order.where(source_order.notna(), input_order)
    else:
        ordered["_replay_source_order"] = input_order
    ordered["_replay_input_order"] = input_order

    ordered = ordered.sort_values(
        ["_replay_period", "_replay_timestamp", "_replay_source_order", "_replay_input_order"],
        kind="stable",
        na_position="last",
    ).drop(
        columns=[
            "_replay_period",
            "_replay_timestamp",
            "_replay_source_order",
            "_replay_input_order",
        ]
    )
    ordered = ordered.reset_index(drop=True)
    ordered["replay_event_index"] = range(len(ordered))
    return ordered


def build_replay_sequence(
    events: pd.DataFrame,
    fixture_id: object,
    team_name: str,
    action_filter: str | Iterable[str] | None = None,
) -> pd.DataFrame:
    """Return the ordered, recorded-event sequence for the Event Replay page."""

    return order_replay_events(filter_replay_events(events, fixture_id, team_name, action_filter))


def replay_actions(
    events: pd.DataFrame,
    fixture_id: object,
    team_name: str,
) -> list[str]:
    """Return available source action and action-type labels for the selector."""

    selected = filter_replay_events(events, fixture_id, team_name)
    labels: set[str] = set()
    for column in ("action_name", "action_type_name"):
        if column in selected.columns:
            labels.update(
                text for value in selected[column] if (text := _optional_text(value)) is not None
            )
    return sorted(labels)


def current_replay_event(replay_events: pd.DataFrame, event_index: int) -> pd.Series | None:
    """Return one recorded replay row, or ``None`` when the sequence is empty."""

    if replay_events.empty:
        return None
    if not 0 <= event_index < len(replay_events):
        raise IndexError(f"Replay event index {event_index} is outside the available sequence.")
    return replay_events.iloc[event_index].copy()


def has_recorded_location(event: Mapping[str, object]) -> bool:
    """Whether an event contains a finite recorded start coordinate pair."""

    return _coordinates(event, "x", "y") is not None


def has_recorded_end_location(event: Mapping[str, object]) -> bool:
    """Whether an event contains a finite recorded end coordinate pair."""

    return _coordinates(event, "x_end", "y_end") is not None


def event_path(event: Mapping[str, object]) -> pd.DataFrame | None:
    """Return one source-recorded start/end path, with no interpolation.

    The two returned rows contain only the recorded start and end values, so
    the pitch renderer does not imply unrecorded movement.
    """

    start = _coordinates(event, "x", "y")
    end = _coordinates(event, "x_end", "y_end")
    if start is None or end is None:
        return None
    return pd.DataFrame(
        {
            "x": [start[0], end[0]],
            "y": [start[1], end[1]],
            "point": ["Start", "End"],
        }
    )


def recent_event_trail(
    replay_events: pd.DataFrame, event_index: int, limit: int = 5
) -> pd.DataFrame:
    """Return up to ``limit`` earlier recorded events, ordered oldest to newest."""

    if limit < 0:
        raise ValueError("Trail limit cannot be negative.")
    if replay_events.empty or event_index <= 0 or limit == 0:
        return replay_events.iloc[0:0].copy()
    if event_index >= len(replay_events):
        raise IndexError(f"Replay event index {event_index} is outside the available sequence.")
    return replay_events.iloc[max(0, event_index - limit) : event_index].copy()


def _coordinates_within_nominal_field(coordinates: Coordinate | None) -> bool | None:
    if coordinates is None:
        return None
    x, y = coordinates
    return _NOMINAL_X_BOUNDS[0] <= x <= _NOMINAL_X_BOUNDS[1] and _NOMINAL_Y_BOUNDS[0] <= y <= _NOMINAL_Y_BOUNDS[1]


def current_event_metadata(replay_events: pd.DataFrame, event_index: int) -> dict[str, Any] | None:
    """Provide compact, display-ready details for the selected recorded event."""

    event = current_replay_event(replay_events, event_index)
    if event is None:
        return None

    start = _coordinates(event, "x", "y")
    end = _coordinates(event, "x_end", "y_end")
    qualifiers: list[str] = []
    for column in _QUALIFIER_COLUMNS:
        if column not in event.index:
            continue
        qualifier = _optional_text(event[column])
        if qualifier and qualifier not in qualifiers:
            qualifiers.append(qualifier)

    action_name = _optional_text(event.get("action_name"))
    action_type_name = _optional_text(event.get("action_type_name"))
    metadata: dict[str, Any] = {
        "event_number": event_index + 1,
        "event_count": len(replay_events),
        "event_id": _optional_value(event.get("event_id")),
        "fixture_id": _optional_value(event.get("fixture_id")),
        "match_time": _optional_text(event.get("match_clock"))
        or _optional_text(event.get("match_time_raw")),
        "team_name": _optional_text(event.get("team_name")),
        "player_name": _optional_text(event.get("player_name")),
        "action_name": action_name or action_type_name,
        "action_type_name": action_type_name,
        "action_result_name": _optional_text(event.get("action_result_name")),
        "start_coordinates": start,
        "end_coordinates": end,
        "has_recorded_location": start is not None,
        "location_within_nominal_field": _coordinates_within_nominal_field(start),
        "recorded_qualifiers": qualifiers,
        "source_file_name": _optional_text(event.get("source_file_name")),
    }
    return metadata
