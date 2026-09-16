from __future__ import annotations

from pathlib import Path

from rugby_analysis.adapters.rugby_data import RugbyDataJsonAdapter
from rugby_analysis.analysis.event_frequency import available_teams, event_counts, events_for_team
from rugby_analysis.analysis.scoring import (
    discipline_events,
    player_scoring_contributions,
    scoring_breakdown,
    team_scoring_summary,
)
from rugby_analysis.core.pipeline import events_to_dataframe
from rugby_analysis.insights.rules import generate_candidate_insights, scoring_by_time_window, team_metrics


def test_team_attributed_scoring_analysis_uses_only_supported_public_fields(rugby_raw_root: Path) -> None:
    events = events_to_dataframe(RugbyDataJsonAdapter(rugby_raw_root).normalize_file(rugby_raw_root / "fixture.json"))

    assert available_teams(events) == ["Alpha RFC", "Beta RFC"]
    alpha_events = events_for_team(events, "Alpha RFC")
    assert len(alpha_events) == 7
    assert event_counts(alpha_events).set_index("event_type").loc["try", "event_count"] == 1

    summary = team_scoring_summary(events, "Alpha RFC")
    assert summary["matches_with_event_timeline"] == 1
    assert summary["source_score_event_value_total"] == 10.0
    assert summary["source_score_event_value_per_match"] == 10.0
    assert summary["tries"] == 1

    breakdown = scoring_breakdown(alpha_events).set_index("event_type")
    assert breakdown.loc["conversion", "points"] == 2
    assert breakdown.loc["missed_penalty", "missed"] == 1

    leaders = player_scoring_contributions(events, "Alpha RFC")
    assert leaders.iloc[0]["player_name"] == "Alice Flyhalf"
    assert leaders.iloc[0]["source_score_event_value"] == 10

    cards = discipline_events(events, "Alpha RFC")
    assert cards["event_type"].tolist() == ["yellow_card"]


def test_candidate_insight_withholds_rate_claims_for_a_small_fixture_sample(rugby_raw_root: Path) -> None:
    events = events_to_dataframe(RugbyDataJsonAdapter(rugby_raw_root).normalize_file(rugby_raw_root / "fixture.json"))

    metrics = team_metrics(events, "Alpha RFC")
    assert metrics["fixtures"] == 1
    assert metrics["points_from_source_score_events"] == 10.0
    assert metrics["conversion_success_rate"] == 1.0

    timing = scoring_by_time_window(events[events["team_name"] == "Alpha RFC"])
    assert timing["points"].sum() == 10

    candidates = generate_candidate_insights(events, "Alpha RFC")
    assert len(candidates) == 1
    assert candidates[0].rule_id == "small_sample"
    assert candidates[0].sample_matches == 1
