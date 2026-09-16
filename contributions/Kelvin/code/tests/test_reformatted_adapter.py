"""Architecture proof: a differently named input format reuses generic analysis."""

from __future__ import annotations

from pathlib import Path

from rugby_analysis.adapters.reformatted_sample import ReformattedPublicSampleAdapter
from rugby_analysis.adapters.rugby_data import RugbyDataJsonAdapter
from rugby_analysis.analysis.event_frequency import event_counts, event_rates_per_match
from rugby_analysis.core.pipeline import events_to_dataframe


def test_second_reformatted_source_maps_to_canonical_events_and_reuses_analysis(
    rugby_raw_root: Path,
) -> None:
    """No generic analysis reads either source format's original column names."""
    project_root = Path(__file__).resolve().parents[1]
    alternate_source = project_root / "data" / "synthetic"
    alternate_adapter = ReformattedPublicSampleAdapter()
    alternate_file = alternate_source / "reformatted_public_sample.csv"

    alternate = events_to_dataframe(alternate_adapter.normalize_file(alternate_file))
    selected_public = events_to_dataframe(
        RugbyDataJsonAdapter(rugby_raw_root).normalize_file(rugby_raw_root / "fixture.json")
    )

    # The two formats use different raw field names, yet both have the exact
    # canonical columns consumed by the generic event-frequency module.
    assert list(alternate.columns) == list(selected_public.columns)
    assert alternate["source"].unique().tolist() == ["reformatted_public_architecture_test"]
    assert event_counts(alternate).set_index("event_type")["event_count"].to_dict() == {
        "kick": 2,
        "scrum": 1,
    }
    assert event_rates_per_match(alternate)["events_per_match"].tolist() == [2.0, 1.0]

    # This confirms the same canonical-only analytics entry point also accepts
    # events from the selected real-source adapter.
    public_counts = event_counts(selected_public)
    assert int(public_counts["event_count"].sum()) == len(selected_public)

