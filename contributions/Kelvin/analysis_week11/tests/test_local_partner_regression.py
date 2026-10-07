"""Local-only baseline test; it never requires the private workbook in Git."""

from __future__ import annotations

from pathlib import Path

import pytest

from week11_analysis.analysis.breakdown import playmaker_option_events
from week11_analysis.analysis.event_effects import classify_event_effect
from week11_analysis.analysis.kicking import (
    kick_events,
    kick_position_distribution,
    kick_receipt_contest_status,
)
from week11_analysis.analysis.linebreaks import linebreak_achieved_conceded_summary
from week11_analysis.analysis.tackling import (
    evaded_tackles_by_associated_player,
    missed_tackle_events,
    player_tackle_outcome_matrix,
    tackle_events,
)
from week11_analysis.data.loader import load_partner_data


SOURCE = Path(__file__).resolve().parents[1] / "data" / "raw" / "949231_REDSvWARA_BI.xlsx"


@pytest.mark.skipif(not SOURCE.exists(), reason="Authorised local representative workbook is not available.")
def test_waratahs_existing_partner_baseline_is_preserved() -> None:
    events = load_partner_data(SOURCE).events
    team = "NSW Waratahs"

    assert len(kick_events(events, team)) == 37
    assert len(playmaker_option_events(events, team)) == 278
    assert len(tackle_events(events, team)) == 142
    assert len(missed_tackle_events(events, team)) == 22

    positions = kick_position_distribution(events, team)
    statuses = kick_receipt_contest_status(events, team)
    evasions = evaded_tackles_by_associated_player(events, team)
    matrix = player_tackle_outcome_matrix(events, team)
    linebreaks = linebreak_achieved_conceded_summary(events, team)

    assert positions["count"].sum() == 37
    assert positions["player_position_name"].eq("Not recorded").sum() == 0
    assert statuses.to_dict("records") == [
        {"contest_status": "Contested", "count": 5, "percentage": pytest.approx(13.5135135135)},
        {"contest_status": "Not Contested", "count": 32, "percentage": pytest.approx(86.4864864865)},
    ]
    assert evasions["evaded_tackles"].sum() == 22
    assert matrix["total_tackle_actions"].sum() == 142
    assert linebreaks["count"].tolist() == [5, 6]


@pytest.mark.skipif(not SOURCE.exists(), reason="Authorised local representative workbook is not available.")
def test_representative_partner_taxonomy_has_complete_event_effect_coverage() -> None:
    """Keep the local event-effect audit tied to the actual representative export."""

    events = load_partner_data(SOURCE).events
    profiles = events.apply(classify_event_effect, axis=1)

    assert len(profiles) == len(events)
    assert all(profile.effect_family for profile in profiles)
    assert all(profile.visual_label for profile in profiles)
    assert all(profile.coverage_status in {"covered", "fallback"} for profile in profiles)
    assert sum(profile.coverage_status == "fallback" for profile in profiles) == 2
    assert all(
        not profile.allows_local_interpolation
        or action in {"Kick", "Pass", "Carry", "Restart", "Goal Kick"}
        for action, profile in zip(events["action_name"], profiles, strict=True)
    )
