"""Transparent, configurable field segmentation for the Week 11 demo.

These are *not* asserted to be the Reds' A/B/C/D/E definitions.  The Q&A has
an unanswered question about the partner's zone convention.  They are simply
four equal, lengthwise x-coordinate bands based on the documented source
orientation, isolated here so an agreed partner definition can replace them.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class FieldZoneConfig:
    """Lengthwise relative-coordinate zone edges and human-readable labels."""

    edges: tuple[float, ...] = (0.0, 25.0, 50.0, 75.0, 100.0)
    labels: tuple[str, ...] = (
        "0-25: own tryline end",
        "25-50: own half",
        "50-75: opposition half",
        "75-100: opposition tryline end",
    )

    def __post_init__(self) -> None:
        if len(self.edges) != len(self.labels) + 1:
            raise ValueError("Zone configuration needs exactly one more edge than labels.")
        if tuple(sorted(self.edges)) != self.edges:
            raise ValueError("Zone edges must be ascending.")


DEFAULT_ZONE_CONFIG = FieldZoneConfig()
ALL_ZONES_LABEL = "All source coordinates"


def assign_relative_field_zone(
    events: pd.DataFrame, config: FieldZoneConfig = DEFAULT_ZONE_CONFIG
) -> pd.Series:
    """Assign a configurable x-coordinate band without flipping team orientation."""

    x_values = pd.to_numeric(events["x"], errors="coerce")
    # Out-of-range coordinates are deliberately not forced into a zone.
    return pd.cut(
        x_values,
        bins=list(config.edges),
        labels=list(config.labels),
        include_lowest=True,
        right=True,
    ).astype("string")
