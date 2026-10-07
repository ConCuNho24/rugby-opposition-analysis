from __future__ import annotations

from week11_analysis.data.transformation import transform_partner_events
from week11_analysis.visualisation.pitch import coordinate_diagnostics


def test_coordinate_diagnostics_reports_without_clamping(partner_rows) -> None:
    events = transform_partner_events(partner_rows)
    report = coordinate_diagnostics(events)

    assert report["count"] == 7
    assert report["out_of_bounds"] == 1
    assert report["x_range"] == "12 to 104"
    assert report["y_range"] == "20 to 35"
