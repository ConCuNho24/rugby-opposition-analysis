"""Run incremental normalization, optionally generating one fixture-context preview."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rugby_analysis.adapters.rugby_data import RugbyDataJsonAdapter  # noqa: E402
from rugby_analysis.core.pipeline import IncrementalPipeline  # noqa: E402
from rugby_analysis.reporting.preview import generate_opposition_preview  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Reprocess all raw match CSV files.")
    parser.add_argument("--team", help="Generate a fixture-context preview for this published fixture team.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    raw_root = PROJECT_ROOT / "data" / "raw" / "rugby_data_premiership_2024_2025" / "matches"
    adapter = RugbyDataJsonAdapter(raw_root)
    pipeline = IncrementalPipeline(PROJECT_ROOT, adapter, raw_root)
    summary = pipeline.run(force=args.force)
    print(
        "[INFO] Processing summary: "
        f"{summary.discovered_matches} detected; {summary.skipped_matches} skipped; "
        f"{summary.processed_matches} processed; {summary.total_normalized_events} canonical events; "
        f"{summary.elapsed_seconds:.3f}s"
    )
    for warning in summary.warnings:
        print(f"[WARNING] {warning}")
    if args.team:
        report_path = generate_opposition_preview(PROJECT_ROOT, args.team)
        print(f"[INFO] Preview report written to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
