from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from rugby_analysis.adapters.rugby_data import RugbyDataJsonAdapter
from rugby_analysis.core.pipeline import IncrementalPipeline, load_canonical_events

def test_incremental_pipeline_is_idempotent_and_reprocesses_changed_match(
    tmp_path: Path, rugby_raw_root: Path
) -> None:
    project_root = tmp_path
    adapter = RugbyDataJsonAdapter(rugby_raw_root)
    pipeline = IncrementalPipeline(project_root, adapter, rugby_raw_root)

    first = pipeline.run()
    first_store = load_canonical_events(project_root / "data" / "processed" / "canonical_events.csv")

    assert first.discovered_matches == 1
    assert first.processed_matches == 1
    assert first.skipped_matches == 0
    assert first.total_normalized_events == 8
    assert len(first_store) == 8

    second = pipeline.run()
    second_store = load_canonical_events(project_root / "data" / "processed" / "canonical_events.csv")

    assert second.processed_matches == 0
    assert second.skipped_matches == 1
    assert second.total_normalized_events == 8
    pd.testing.assert_frame_equal(second_store, first_store)

    changed_record = json.loads((rugby_raw_root / "fixture.json").read_text(encoding="utf-8"))
    changed_record["away"]["lineup"]["13"]["reds"] = [70]  # type: ignore[index]
    (rugby_raw_root / "fixture.json").write_text(json.dumps(changed_record), encoding="utf-8")

    third = pipeline.run()
    third_store = load_canonical_events(project_root / "data" / "processed" / "canonical_events.csv")

    assert third.processed_matches == 1
    assert third.skipped_matches == 0
    assert third.total_normalized_events == 9
    assert (third_store["event_type"] == "red_card").sum() == 1
    assert third_store["match_id"].nunique() == 1
