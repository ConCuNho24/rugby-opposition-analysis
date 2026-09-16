from __future__ import annotations

from pathlib import Path

from rugby_analysis.adapters.rugby_data import RugbyDataJsonAdapter
from rugby_analysis.core.pipeline import IncrementalPipeline
from rugby_analysis.reporting.preview import generate_opposition_preview


def test_html_preview_reuses_canonical_store_after_raw_input_is_gone(
    tmp_path: Path, rugby_raw_root: Path
) -> None:
    """The report boundary must never need to reread a raw source match."""
    adapter = RugbyDataJsonAdapter(rugby_raw_root)
    IncrementalPipeline(tmp_path, adapter, rugby_raw_root).run()
    (rugby_raw_root / "fixture.json").unlink()

    report_path = generate_opposition_preview(tmp_path, "Alpha RFC")
    html = report_path.read_text(encoding="utf-8")

    assert report_path.exists()
    assert "Opposition preview: Alpha RFC" in html
    assert "Source score-event value / fixture" in html
    assert "not full play-by-play" in html
    chart_directory = tmp_path / "outputs" / "charts"
    assert (chart_directory / "alpha_rfc_event_profile.png").exists()
    assert (chart_directory / "alpha_rfc_scoring_by_fixture.png").exists()
    assert (chart_directory / "alpha_rfc_scoring_timing.png").exists()

