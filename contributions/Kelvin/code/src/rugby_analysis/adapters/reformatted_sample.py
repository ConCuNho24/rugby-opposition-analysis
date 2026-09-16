"""Second-format architecture test adapter.

This is not a second real provider. It maps a tiny deliberately reformatted sample
of public annotation records to prove the analysis pipeline depends on the
canonical schema, not a source's header names.
"""

from __future__ import annotations

import csv
from pathlib import Path

from rugby_analysis.adapters.base import EventDataAdapter
from rugby_analysis.core.schema import CanonicalEvent


class ReformattedPublicSampleAdapter(EventDataAdapter):
    source_name = "reformatted_public_architecture_test"

    def discover_files(self, raw_root: Path) -> list[Path]:
        return sorted(Path(raw_root).glob("*.csv"))

    def normalize_file(self, file_path: Path) -> list[CanonicalEvent]:
        events: list[CanonicalEvent] = []
        with file_path.open("r", encoding="utf-8", newline="") as source_file:
            for index, row in enumerate(csv.DictReader(source_file)):
                match_id = row["game"].strip()
                events.append(
                    CanonicalEvent(
                        source=self.source_name,
                        match_id=match_id,
                        event_id=row.get("annotation_id") or f"{match_id}_{index}",
                        sequence_index=index,
                        timestamp_seconds=float(row["event_time_seconds"]),
                        event_type=row["action_type"].strip().casefold(),
                        metadata={"fixture_label": row.get("fixture", ""), "architecture_test": True},
                    )
                )
        return events
