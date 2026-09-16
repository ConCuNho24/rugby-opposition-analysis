"""Adapter for CodeProcessor's public video-annotation CSV files.

The source has one row per annotation and three unnamed values:
event name, start time and end time. It does *not* attribute an annotation to a
team or player and does not provide field coordinates or outcomes. This adapter
preserves that absence rather than inferring values from fixture participants.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from rugby_analysis.adapters.base import EventDataAdapter
from rugby_analysis.core.schema import CanonicalEvent


SOURCE_NAME = "codeprocessor_rugby_events_dataset"
SOURCE_REPOSITORY = "https://github.com/CodeProcessor/rugby-events-dataset"
_MATCH_ID_RE = re.compile(r"match#(?P<number>\d+)\.csv$", re.IGNORECASE)


def parse_annotation_time(raw_time: str | None) -> float | None:
    """Parse the documented ``mm.ss`` / ``hh.mm.ss`` annotation formats.

    A few source cells contain spacing or a duplicated separator. Empty segments
    are removed only for parsing; the untouched source token is retained in event
    metadata for auditability. Values that still cannot be parsed are returned as
    ``None`` rather than fabricated.
    """
    if raw_time is None:
        return None
    cleaned = raw_time.strip()
    if not cleaned:
        return None
    parts = [part.strip() for part in cleaned.split(".") if part.strip()]
    if len(parts) not in {2, 3}:
        return None
    try:
        numbers = [int(part) for part in parts]
    except ValueError:
        return None
    if any(number < 0 for number in numbers):
        return None
    if len(numbers) == 2:
        minutes, seconds = numbers
        return float(minutes * 60 + seconds)
    hours, minutes, seconds = numbers
    return float(hours * 3600 + minutes * 60 + seconds)


class CodeProcessorVideoAnnotationAdapter(EventDataAdapter):
    """Normalize video annotations while retaining fixture context as metadata."""

    source_name = SOURCE_NAME

    def __init__(self, raw_root: Path, manifest_path: Path | None = None) -> None:
        self.raw_root = Path(raw_root)
        self.manifest_path = manifest_path or self.raw_root.parent / "source_manifest.json"
        self._fixture_lookup = self._load_fixture_lookup()
        self._last_warnings: list[str] = []

    def _load_fixture_lookup(self) -> dict[str, dict[str, Any]]:
        if not self.manifest_path.exists():
            return {}
        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return {
            str(item.get("match_id")): item
            for item in manifest.get("matches", [])
            if item.get("match_id") is not None
        }

    def discover_files(self, raw_root: Path | None = None) -> list[Path]:
        directory = Path(raw_root or self.raw_root)
        return sorted(directory.glob("match#*.csv"), key=self._match_sort_key)

    @staticmethod
    def _match_sort_key(path: Path) -> tuple[int, str]:
        match = _MATCH_ID_RE.search(path.name)
        return (int(match.group("number")) if match else 10**9, path.name)

    @staticmethod
    def match_id_for_file(file_path: Path) -> str:
        match = _MATCH_ID_RE.search(file_path.name)
        if not match:
            raise ValueError(f"Expected CodeProcessor match CSV name, got {file_path.name!r}")
        return f"codeprocessor_match_{int(match.group('number'))}"

    def normalize_file(self, file_path: Path) -> list[CanonicalEvent]:
        match_id = self.match_id_for_file(file_path)
        fixture = self._fixture_lookup.get(match_id, {})
        source_rows: list[tuple[str, str, str, int]] = []
        malformed_rows = 0
        blank_event_rows = 0
        unparseable_start_rows = 0
        with file_path.open("r", encoding="utf-8-sig", newline="") as source_file:
            for source_row_number, row in enumerate(csv.reader(source_file), start=1):
                if not row or not any(value.strip() for value in row):
                    continue
                if len(row) < 3:
                    malformed_rows += 1
                    continue
                event_type = row[0].strip().casefold()
                if event_type in {"event name", "event_type"}:
                    continue
                if not event_type:
                    blank_event_rows += 1
                    continue
                if parse_annotation_time(row[1].strip()) is None:
                    unparseable_start_rows += 1
                source_rows.append((event_type, row[1].strip(), row[2].strip(), source_row_number))

        source_rows.sort(key=lambda item: (parse_annotation_time(item[1]) is None, parse_annotation_time(item[1]) or 0, item[3]))
        self._last_warnings = []
        if malformed_rows:
            self._last_warnings.append(f"{malformed_rows} source row(s) had fewer than three fields and were skipped.")
        if blank_event_rows:
            self._last_warnings.append(f"{blank_event_rows} blank event-label row(s) were skipped; no event type was invented.")
        if unparseable_start_rows:
            self._last_warnings.append(f"{unparseable_start_rows} event(s) retain a null canonical timestamp due to unparseable source time.")
        events: list[CanonicalEvent] = []
        for sequence_index, (event_type, start_raw, end_raw, source_row_number) in enumerate(source_rows):
            start_seconds = parse_annotation_time(start_raw)
            end_seconds = parse_annotation_time(end_raw)
            metadata: dict[str, Any] = {
                "source_repository": SOURCE_REPOSITORY,
                "source_file": file_path.name,
                "source_row_number": source_row_number,
                "start_time_raw": start_raw,
                "end_time_raw": end_raw,
                "start_time_parse_status": "parsed" if start_seconds is not None else "unparseable",
                "fixture_label": fixture.get("fixture_label"),
                "home_team": fixture.get("home_team"),
                "away_team": fixture.get("away_team"),
                "duration_seconds": (end_seconds - start_seconds)
                if start_seconds is not None and end_seconds is not None and end_seconds >= start_seconds
                else None,
            }
            events.append(
                CanonicalEvent(
                    source=self.source_name,
                    match_id=match_id,
                    event_id=f"{match_id}_{source_row_number}",
                    sequence_index=sequence_index,
                    timestamp_seconds=start_seconds,
                    event_type=event_type,
                    metadata=metadata,
                )
            )
        return events

    def validate(self, events: list[CanonicalEvent]) -> list[str]:
        return [*super().validate(events), *self._last_warnings]
