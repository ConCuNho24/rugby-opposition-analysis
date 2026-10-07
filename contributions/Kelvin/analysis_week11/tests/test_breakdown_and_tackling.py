from __future__ import annotations

from week11_analysis.analysis.breakdown import breakdown_choice_table
from week11_analysis.analysis.tackling import (
    first_tackler_outcomes,
    missed_tackles_by_player,
    tackle_outcome_distribution,
)
from week11_analysis.data.transformation import transform_partner_events


def test_breakdown_choices_classify_source_decision_and_zone(partner_rows) -> None:
    events = transform_partner_events(partner_rows)

    summary = breakdown_choice_table(events, "NSW Waratahs", "0-25: own tryline end")

    assert summary.iloc[0]["decision_label"] == "Pass from Halfback at Breakdown"
    assert summary.iloc[0]["count"] == 1
    assert summary.iloc[0]["percentage"] == 100


def test_tackle_and_explicit_missed_tackle_records_remain_separate(partner_rows) -> None:
    events = transform_partner_events(partner_rows)

    outcomes = tackle_outcome_distribution(events, "NSW Waratahs")
    misses = missed_tackles_by_player(events, "NSW Waratahs")
    first_tackler = first_tackler_outcomes(events, "NSW Waratahs")

    assert outcomes["count"].sum() == 2
    assert set(outcomes["tackle_outcome"]) == {"Complete", "Passive"}
    assert misses.iloc[0]["player_name"] == "Tackler Two"
    assert first_tackler["count"].sum() == 2
