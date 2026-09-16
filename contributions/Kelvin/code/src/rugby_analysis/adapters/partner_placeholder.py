"""Future Queensland Reds / partner adapter contract.

No parser is implemented here because the partner CSV files and their schema have
not been supplied. A future implementation must profile real headers, qualifiers,
identifiers, time semantics and coordinate conventions before defining mappings.
"""

from __future__ import annotations

from pathlib import Path

from rugby_analysis.adapters.base import EventDataAdapter
from rugby_analysis.core.schema import CanonicalEvent


class PartnerAdapterPlaceholder(EventDataAdapter):
    """Documented extension point; intentionally not a speculative Opta parser."""

    source_name = "partner_data_pending"

    def discover_files(self, raw_root: Path) -> list[Path]:
        raise NotImplementedError(
            "Partner data is not available. Profile supplied files and implement a header-based mapping first."
        )

    def normalize_file(self, file_path: Path) -> list[CanonicalEvent]:
        raise NotImplementedError(
            "No partner schema assumptions are encoded. Implement after receiving and profiling partner CSVs."
        )
