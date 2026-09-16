"""Source-independent representation for a rugby match-event record.

The schema deliberately permits missing player, team, location and outcome fields.
Those fields must remain absent when a source does not supply them.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


CANONICAL_COLUMNS = [
    "source",
    "match_id",
    "event_id",
    "sequence_index",
    "period",
    "timestamp_seconds",
    "team_id",
    "team_name",
    "opponent_id",
    "opponent_name",
    "player_id",
    "player_name",
    "event_type",
    "event_subtype",
    "start_x",
    "start_y",
    "end_x",
    "end_y",
    "outcome",
    "metadata",
]


@dataclass(frozen=True, slots=True)
class CanonicalEvent:
    """A normalized event with source-specific details retained in ``metadata``."""

    source: str
    match_id: str
    event_id: str
    sequence_index: int
    event_type: str
    period: int | None = None
    timestamp_seconds: float | None = None
    team_id: str | None = None
    team_name: str | None = None
    opponent_id: str | None = None
    opponent_name: str | None = None
    player_id: str | None = None
    player_name: str | None = None
    event_subtype: str | None = None
    start_x: float | None = None
    start_y: float | None = None
    end_x: float | None = None
    end_y: float | None = None
    outcome: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("CanonicalEvent.source must be non-empty")
        if not self.match_id.strip():
            raise ValueError("CanonicalEvent.match_id must be non-empty")
        if not self.event_id.strip():
            raise ValueError("CanonicalEvent.event_id must be non-empty")
        if self.sequence_index < 0:
            raise ValueError("CanonicalEvent.sequence_index cannot be negative")
        if not self.event_type.strip():
            raise ValueError("CanonicalEvent.event_type must be non-empty")
        if self.timestamp_seconds is not None and self.timestamp_seconds < 0:
            raise ValueError("CanonicalEvent.timestamp_seconds cannot be negative")

    def to_record(self) -> dict[str, Any]:
        """Return a CSV/JSON-friendly record without losing metadata."""
        record = asdict(self)
        record["metadata"] = json.dumps(dict(self.metadata), sort_keys=True, default=str)
        # Dataclass declaration order prioritises required constructor fields;
        # persisted records instead use the documented source-independent schema
        # order so CSV output and direct serialisation are identical.
        return {column: record[column] for column in CANONICAL_COLUMNS}

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "CanonicalEvent":
        """Rehydrate an event persisted by :meth:`to_record`."""
        payload = dict(record)
        metadata = payload.get("metadata", {})
        if isinstance(metadata, str):
            metadata = json.loads(metadata) if metadata.strip() else {}
        for nullable in CANONICAL_COLUMNS:
            if nullable in {"source", "match_id", "event_id", "event_type", "metadata"}:
                continue
            value = payload.get(nullable)
            if value == "" or value is None:
                payload[nullable] = None
        payload["sequence_index"] = int(payload["sequence_index"])
        if payload.get("period") is not None:
            payload["period"] = int(float(payload["period"]))
        if payload.get("timestamp_seconds") is not None:
            payload["timestamp_seconds"] = float(payload["timestamp_seconds"])
        for coordinate in ("start_x", "start_y", "end_x", "end_y"):
            if payload.get(coordinate) is not None:
                payload[coordinate] = float(payload[coordinate])
        payload["metadata"] = metadata
        return cls(**{column: payload.get(column) for column in CANONICAL_COLUMNS})
