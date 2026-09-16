"""Deterministic, descriptive candidate-insight rules.

The rules use canonical events only. They intentionally surface observations for
analyst review; they never make a tactical recommendation or imply causation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import pandas as pd

from rugby_analysis.analysis.event_frequency import available_teams, metadata_dict
from rugby_analysis.analysis.scoring import score_value, scoring_events


TIME_BINS = [-0.001, 1200, 2400, 3600, float("inf")]
TIME_LABELS = ["0-20 min", "21-40 min", "41-60 min", "61+ min"]


@dataclass(frozen=True, slots=True)
class CandidateInsight:
    """Structured evidence for one candidate observation."""

    rule_id: str
    category: str
    statement: str
    metric: str
    team_value: float | None
    baseline_value: float | None
    sample_matches: int
    confidence_note: str
    evidence: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        """Return a report- and JSON-friendly representation."""
        return asdict(self)


def team_events(
    events: pd.DataFrame, team_name: str, match_ids: Iterable[str] | None = None
) -> pd.DataFrame:
    """Return source-attributed canonical events for a selected team."""
    if events.empty or "team_name" not in events:
        return events.iloc[0:0].copy()
    selected = events.loc[events["team_name"] == team_name].copy()
    if match_ids is not None:
        selected = selected.loc[selected["match_id"].isin(set(match_ids))].copy()
    return selected


def team_fixture_ids(
    events: pd.DataFrame, team_name: str, match_ids: Iterable[str] | None = None
) -> list[str]:
    """List event-timeline fixtures for a team in stable chronological ID order."""
    selected = team_events(events, team_name, match_ids)
    return sorted(selected["match_id"].astype(str).unique().tolist()) if not selected.empty else []


def scoring_by_time_window(events: pd.DataFrame) -> pd.DataFrame:
    """Summarise source score-event values by recorded minute window.

    The source has minute values but no verified half or period boundary. The
    returned windows are descriptive source-minute windows, not match periods.
    """
    empty = pd.DataFrame(columns=["time_window", "events", "points", "point_share"])
    selected = scoring_events(events)
    if selected.empty:
        return empty
    selected = selected.copy()
    selected["timestamp_seconds"] = pd.to_numeric(selected["timestamp_seconds"], errors="coerce")
    selected = selected.dropna(subset=["timestamp_seconds"])
    if selected.empty:
        return empty
    selected["points"] = pd.to_numeric(score_value(selected), errors="coerce").fillna(0.0)
    selected["time_window"] = pd.cut(
        selected["timestamp_seconds"], bins=TIME_BINS, labels=TIME_LABELS, include_lowest=True
    )
    grouped = (
        selected.groupby("time_window", observed=False)
        .agg(events=("event_id", "count"), points=("points", "sum"))
        .reset_index()
    )
    total = float(grouped["points"].sum())
    grouped["point_share"] = grouped["points"] / total if total else 0.0
    return grouped


def _official_final_scores(events: pd.DataFrame, team_name: str) -> list[float]:
    """Read published final scores retained as canonical metadata, if present."""
    scores: list[float] = []
    for _, fixture_events in team_events(events, team_name).groupby("match_id", sort=False):
        metadata = metadata_dict(fixture_events.iloc[0].get("metadata", ""))
        value: object | None
        if metadata.get("home_team") == team_name:
            value = metadata.get("home_final_score")
        elif metadata.get("away_team") == team_name:
            value = metadata.get("away_final_score")
        else:
            value = None
        numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        if pd.notna(numeric):
            scores.append(float(numeric))
    return scores


def team_metrics(
    events: pd.DataFrame, team_name: str, match_ids: Iterable[str] | None = None
) -> dict[str, float | int | str]:
    """Calculate only team metrics supported by the current public source."""
    selected = team_events(events, team_name, match_ids)
    fixtures = int(selected["match_id"].nunique()) if not selected.empty else 0
    scores = scoring_events(selected).copy()
    if scores.empty:
        values = pd.Series(dtype="float")
    else:
        values = pd.to_numeric(score_value(scores), errors="coerce").fillna(0.0)
        scores["source_score_value"] = values
    source_score_value_total = float(values.sum()) if not values.empty else 0.0
    conversion_attempts = int(scores["event_type"].isin(["conversion", "missed_conversion"]).sum()) if not scores.empty else 0
    successful_conversions = int((scores["event_type"] == "conversion").sum()) if not scores.empty else 0
    tries = int((scores["event_type"] == "try").sum()) if not scores.empty else 0
    yellow_cards = int((selected["event_type"] == "yellow_card").sum()) if not selected.empty else 0
    red_cards = int((selected["event_type"] == "red_card").sum()) if not selected.empty else 0
    official_scores = _official_final_scores(selected, team_name)
    return {
        "team": team_name,
        "fixtures": fixtures,
        "scoring_events": int(len(scores)),
        # This explicit name distinguishes source event values from official score.
        "points_from_source_score_events": source_score_value_total,
        "source_score_event_value_per_fixture": source_score_value_total / fixtures if fixtures else 0.0,
        "tries": tries,
        "tries_per_fixture": tries / fixtures if fixtures else 0.0,
        "conversion_attempts": conversion_attempts,
        "successful_conversions": successful_conversions,
        "conversion_success_rate": successful_conversions / conversion_attempts if conversion_attempts else 0.0,
        "yellow_cards": yellow_cards,
        "yellow_cards_per_fixture": yellow_cards / fixtures if fixtures else 0.0,
        "red_cards": red_cards,
        "red_cards_per_fixture": red_cards / fixtures if fixtures else 0.0,
        "official_final_score_matches": len(official_scores),
        "official_final_score_total": float(sum(official_scores)),
        "official_final_score_per_fixture": float(sum(official_scores)) / len(official_scores) if official_scores else 0.0,
    }


def competition_baseline_metrics(events: pd.DataFrame) -> dict[str, float | int]:
    """Return the unweighted average of available team per-fixture metrics."""
    rows = [team_metrics(events, name) for name in available_teams(events)]
    rows = [row for row in rows if int(row["fixtures"]) > 0]
    if not rows:
        return {"teams": 0, "source_score_event_value_per_fixture": 0.0, "tries_per_fixture": 0.0,
                "yellow_cards_per_fixture": 0.0, "conversion_success_rate": 0.0}
    metrics = pd.DataFrame(rows)
    return {
        "teams": int(len(metrics)),
        "source_score_event_value_per_fixture": float(metrics["source_score_event_value_per_fixture"].mean()),
        "tries_per_fixture": float(metrics["tries_per_fixture"].mean()),
        "yellow_cards_per_fixture": float(metrics["yellow_cards_per_fixture"].mean()),
        "conversion_success_rate": float(metrics.loc[metrics["conversion_attempts"] > 0, "conversion_success_rate"].mean()),
    }


def _rate_observation(
    insights: list[CandidateInsight],
    *,
    rule_id: str,
    category: str,
    team_name: str,
    metric: str,
    label: str,
    team_value: float,
    baseline_value: float,
    fixtures: int,
) -> None:
    if baseline_value <= 0:
        return
    ratio = team_value / baseline_value
    if ratio >= 1.20:
        direction = "higher"
    elif ratio <= 0.80:
        direction = "lower"
    else:
        return
    insights.append(
        CandidateInsight(
            rule_id=rule_id,
            category=category,
            statement=(
                f"Candidate pattern: {team_name} recorded {team_value:.2f} {label} per available fixture, "
                f"{direction} than the dataset team average of {baseline_value:.2f}."
            ),
            metric=metric,
            team_value=team_value,
            baseline_value=baseline_value,
            sample_matches=fixtures,
            confidence_note="Descriptive comparison only; review fixture context and source coverage before interpretation.",
            evidence={"ratio_to_dataset_average": ratio, "dataset_teams": "unweighted team average"},
        )
    )


def generate_candidate_insights(
    events: pd.DataFrame, team_name: str, match_ids: Iterable[str] | None = None, min_sample_matches: int = 3
) -> list[CandidateInsight]:
    """Surface deterministic candidate observations with visible sample safeguards."""
    scoped = team_events(events, team_name, match_ids)
    metrics = team_metrics(scoped, team_name)
    fixtures = int(metrics["fixtures"])
    if fixtures == 0:
        return [
            CandidateInsight(
                rule_id="no_supported_records",
                category="data_quality",
                statement=f"No team-attributed canonical records are available for {team_name} in this selection.",
                metric="available_fixtures",
                team_value=0.0,
                baseline_value=None,
                sample_matches=0,
                confidence_note="No analytic claim is made when the source has no records for the selection.",
                evidence={},
            )
        ]
    if fixtures < min_sample_matches:
        return [
            CandidateInsight(
                rule_id="small_sample",
                category="data_quality",
                statement=(
                    f"Only {fixtures} available fixture(s) are in scope for {team_name}; rate comparisons are "
                    "withheld until a larger sample is selected."
                ),
                metric="available_fixtures",
                team_value=float(fixtures),
                baseline_value=float(min_sample_matches),
                sample_matches=fixtures,
                confidence_note="Small sample: descriptive totals may be viewed, but comparative candidate insights are withheld.",
                evidence={"minimum_sample_matches": min_sample_matches},
            )
        ]

    baseline = competition_baseline_metrics(events)
    insights: list[CandidateInsight] = []
    _rate_observation(
        insights,
        rule_id="source_score_event_value_rate",
        category="scoring",
        team_name=team_name,
        metric="source_score_event_value_per_fixture",
        label="source score-event value",
        team_value=float(metrics["source_score_event_value_per_fixture"]),
        baseline_value=float(baseline["source_score_event_value_per_fixture"]),
        fixtures=fixtures,
    )
    _rate_observation(
        insights,
        rule_id="try_rate",
        category="scoring",
        team_name=team_name,
        metric="tries_per_fixture",
        label="tries",
        team_value=float(metrics["tries_per_fixture"]),
        baseline_value=float(baseline["tries_per_fixture"]),
        fixtures=fixtures,
    )
    if int(metrics["yellow_cards"]) >= 3:
        _rate_observation(
            insights,
            rule_id="yellow_card_rate",
            category="discipline",
            team_name=team_name,
            metric="yellow_cards_per_fixture",
            label="yellow cards",
            team_value=float(metrics["yellow_cards_per_fixture"]),
            baseline_value=float(baseline["yellow_cards_per_fixture"]),
            fixtures=fixtures,
        )

    scoring = scoring_events(scoped)
    known_players = scoring.loc[scoring["player_name"].notna()].copy()
    if not known_players.empty and len(scoring) >= 10:
        leader = known_players.groupby("player_name").size().sort_values(ascending=False).head(1)
        if not leader.empty:
            player_name = str(leader.index[0])
            event_count = int(leader.iloc[0])
            share = event_count / len(scoring)
            if share >= 0.35:
                insights.append(
                    CandidateInsight(
                        rule_id="player_scoring_event_share",
                        category="player_contribution",
                        statement=(
                            f"Candidate pattern: {player_name} appears in {share:.0%} of {team_name}'s "
                            "source-recorded scoring events in the selected fixtures."
                        ),
                        metric="player_scoring_event_share",
                        team_value=share,
                        baseline_value=None,
                        sample_matches=fixtures,
                        confidence_note="Player attribution follows the public score timeline; this is involvement, not a causal assessment.",
                        evidence={"player_name": player_name, "player_events": event_count, "team_scoring_events": int(len(scoring))},
                    )
                )

    timing = scoring_by_time_window(scoped)
    if not timing.empty and float(timing["points"].sum()) >= 15:
        largest = timing.loc[timing["point_share"].idxmax()]
        if float(largest["point_share"]) >= 0.45:
            insights.append(
                CandidateInsight(
                    rule_id="scoring_time_concentration",
                    category="timing",
                    statement=(
                        f"Candidate pattern: {float(largest['point_share']):.0%} of {team_name}'s source score-event "
                        f"value falls in the {largest['time_window']} source-minute window."
                    ),
                    metric="source_score_event_value_time_share",
                    team_value=float(largest["point_share"]),
                    baseline_value=None,
                    sample_matches=fixtures,
                    confidence_note="The public source has no verified period boundary; this is a source-minute concentration only.",
                    evidence={"time_window": str(largest["time_window"]), "source_score_event_value": float(largest["points"])},
                )
            )
    return insights

