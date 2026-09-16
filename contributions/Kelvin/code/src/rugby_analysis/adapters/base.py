"""Adapter contract for bringing external event formats into the common model."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from rugby_analysis.core.schema import CanonicalEvent


class EventDataAdapter(ABC):
    """All downstream modules receive canonical events, never source columns."""

    source_name: str

    @abstractmethod
    def discover_files(self, raw_root: Path) -> list[Path]:
        """Return source files representing individual matches."""

    @abstractmethod
    def normalize_file(self, file_path: Path) -> list[CanonicalEvent]:
        """Read one source match exactly once and return canonical events."""

    def validate(self, events: list[CanonicalEvent]) -> list[str]:
        """Return non-fatal validation warnings for a normalized match."""
        warnings: list[str] = []
        if not events:
            warnings.append("No valid event rows were emitted.")
            return warnings
        timestamps = [event.timestamp_seconds for event in events if event.timestamp_seconds is not None]
        if not timestamps:
            warnings.append("No parseable event timestamps were available.")
        event_ids = [event.event_id for event in events]
        if len(set(event_ids)) != len(event_ids):
            warnings.append("Duplicate canonical event IDs were emitted within one source match.")
        if len({event.match_id for event in events}) != 1:
            warnings.append("A single source match file emitted more than one canonical match ID.")
        return warnings
