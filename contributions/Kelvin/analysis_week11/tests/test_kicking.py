from __future__ import annotations

from week11_analysis.analysis.kicking import (
    kick_end_locations,
    kick_events,
    kick_type_distribution,
    kicker_summary,
)
from week11_analysis.data.transformation import transform_partner_events


def test_kick_filter_uses_only_explicit_kick_action(partner_rows) -> None:
    events = transform_partner_events(partner_rows)

    assert len(kick_events(events, "NSW Waratahs")) == 2
    distribution = kick_type_distribution(events, "NSW Waratahs")
    assert set(distribution["kick_type"]) == {"Box", "Touch Kick"}
    assert distribution["percentage"].sum() == 100


def test_kicker_summary_has_safe_empty_result(partner_rows) -> None:
    events = transform_partner_events(partner_rows)

    assert kicker_summary(events, "Queensland Reds").empty


def test_kick_end_locations_use_only_documented_endpoint_fields(partner_rows) -> None:
    events = transform_partner_events(partner_rows)
    endpoints = kick_end_locations(events, "NSW Waratahs")

    assert endpoints["x"].tolist() == [65, 100]
    assert endpoints["y"].tolist() == [22, 40]
