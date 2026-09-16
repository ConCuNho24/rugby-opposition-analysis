"""Process each raw match once, persist canonical events, then reuse that store."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from rugby_analysis.adapters.base import EventDataAdapter
from rugby_analysis.core.manifest import ProcessingManifest, sha256_file
from rugby_analysis.core.schema import CANONICAL_COLUMNS, CanonicalEvent

LOGGER = logging.getLogger(__name__)


@dataclass
class ProcessingSummary:
    discovered_matches: int
    processed_matches: int
    skipped_matches: int
    total_normalized_events: int
    elapsed_seconds: float
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "discovered_matches": self.discovered_matches,
            "processed_matches": self.processed_matches,
            "skipped_matches": self.skipped_matches,
            "total_normalized_events": self.total_normalized_events,
            "elapsed_seconds": round(self.elapsed_seconds, 4),
            "warnings": self.warnings,
        }


def events_to_dataframe(events: list[CanonicalEvent]) -> pd.DataFrame:
    """Convert events to a stable column order for the processed CSV store."""
    if not events:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)
    frame = pd.DataFrame([event.to_record() for event in events], columns=CANONICAL_COLUMNS)
    return frame.sort_values(["match_id", "sequence_index"], kind="stable").reset_index(drop=True)


def load_canonical_events(path: Path) -> pd.DataFrame:
    """Load the combined canonical store without touching raw source data."""
    if not path.exists():
        return pd.DataFrame(columns=CANONICAL_COLUMNS)
    frame = pd.read_csv(path, keep_default_na=False)
    for numeric_column in ("sequence_index", "period", "timestamp_seconds", "start_x", "start_y", "end_x", "end_y"):
        if numeric_column in frame.columns:
            frame[numeric_column] = pd.to_numeric(frame[numeric_column], errors="coerce")
    return frame.reindex(columns=CANONICAL_COLUMNS)


class IncrementalPipeline:
    """Adapter-first incremental processor.

    Each changed raw CSV is normalized once to a per-match canonical file. Analyses,
    insights and reporting read only the combined canonical store afterwards.
    """

    def __init__(self, project_root: Path, adapter: EventDataAdapter, raw_root: Path) -> None:
        self.project_root = Path(project_root)
        self.adapter = adapter
        self.raw_root = Path(raw_root)
        self.matches_root = self.project_root / "data" / "processed" / "matches"
        self.store_path = self.project_root / "data" / "processed" / "canonical_events.csv"
        self.manifest_path = self.project_root / "data" / "state" / "processing_manifest.json"

    def run(self, force: bool = False) -> ProcessingSummary:
        started = time.perf_counter()
        raw_files = self.adapter.discover_files(self.raw_root)
        manifest = ProcessingManifest.load(self.manifest_path, self.adapter.source_name)
        processed = 0
        skipped = 0
        warnings: list[str] = []
        self.matches_root.mkdir(parents=True, exist_ok=True)

        LOGGER.info("Discovered %s source matches", len(raw_files))
        for raw_file in raw_files:
            match_id = self._match_id(raw_file)
            output_file = self.matches_root / f"{match_id}.csv"
            content_hash = sha256_file(raw_file)
            if not force and manifest.is_current(raw_file, content_hash, output_file):
                skipped += 1
                LOGGER.info("Skipping already processed %s", raw_file.name)
                continue

            LOGGER.info("Processing %s", raw_file.name)
            events = self.adapter.normalize_file(raw_file)
            match_warnings = self.adapter.validate(events)
            warnings.extend(f"{raw_file.name}: {warning}" for warning in match_warnings)
            events_to_dataframe(events).to_csv(output_file, index=False)
            manifest.record(raw_file, content_hash, match_id, output_file, len(events))
            processed += 1
            LOGGER.info("%s events normalized for %s", len(events), match_id)

        self._rebuild_combined_store(raw_files)
        manifest.save(self.manifest_path)
        total_events = len(load_canonical_events(self.store_path))
        elapsed = time.perf_counter() - started
        LOGGER.info(
            "Incremental processing complete: %s processed, %s skipped, %s canonical events, %.3fs",
            processed,
            skipped,
            total_events,
            elapsed,
        )
        return ProcessingSummary(
            discovered_matches=len(raw_files),
            processed_matches=processed,
            skipped_matches=skipped,
            total_normalized_events=total_events,
            elapsed_seconds=elapsed,
            warnings=warnings,
        )

    def _match_id(self, raw_file: Path) -> str:
        # The public adapter exposes this method; the fallback supports generic adapters in tests.
        match_id_for_file = getattr(self.adapter, "match_id_for_file", None)
        return str(match_id_for_file(raw_file)) if callable(match_id_for_file) else raw_file.stem

    def _rebuild_combined_store(self, raw_files: list[Path]) -> None:
        frames: list[pd.DataFrame] = []
        for raw_file in raw_files:
            per_match_path = self.matches_root / f"{self._match_id(raw_file)}.csv"
            if per_match_path.exists():
                frame = pd.read_csv(per_match_path, keep_default_na=False)
                # A published fixture can have a final score but no timeline
                # details. Its deliberately empty canonical file remains in the
                # manifest, but it must not trigger pandas' all-NA concat warning.
                if not frame.empty:
                    frames.append(frame)
        if frames:
            combined = pd.concat(frames, ignore_index=True).reindex(columns=CANONICAL_COLUMNS)
            combined["sequence_index"] = pd.to_numeric(combined["sequence_index"], errors="coerce").fillna(0).astype(int)
            combined = combined.sort_values(["match_id", "sequence_index"], kind="stable")
        else:
            combined = pd.DataFrame(columns=CANONICAL_COLUMNS)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        combined.to_csv(self.store_path, index=False)
