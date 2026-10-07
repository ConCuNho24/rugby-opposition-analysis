"""Deterministic, evidence-bound coach-facing observations.

No generative model or unsupported performance inference is used here.  Every
sentence names the source subset it describes and safely returns no insights
when the needed records do not exist.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .breakdown import playmaker_option_events
from .kicking import kick_events, kick_type_distribution
from .linebreaks import initial_breaks_by_player
from .tackling import (
    evaded_tackles_by_associated_player,
    tackle_events,
    tackle_outcome_distribution,
)


@dataclass(frozen=True)
class Insight:
    """A concise observation with an auditable source label."""

    module: str
    text: str


def _top_row(summary: pd.DataFrame) -> pd.Series | None:
    return None if summary.empty else summary.iloc[0]


def generate_key_insights(events: pd.DataFrame, team_name: str) -> list[Insight]:
    """Generate stable observations only when their source rows are present."""

    insights: list[Insight] = []
    kick_type = _top_row(kick_type_distribution(events, team_name))
    if kick_type is not None:
        kick_total = len(kick_events(events, team_name))
        insights.append(
            Insight(
                "Kicking",
                f"{team_name}: {kick_type['kick_type']} was the most frequent recorded kick type: "
                f"{int(kick_type['count'])} of {kick_total} kicks ({kick_type['percentage']:.1f}%).",
            )
        )

    choices = playmaker_option_events(events, team_name)
    if not choices.empty:
        top_choice = (
            choices.groupby("decision_label").size().rename("count").reset_index()
            .sort_values(["count", "decision_label"], ascending=[False, True], kind="stable").iloc[0]
        )
        insights.append(
            Insight(
                "Breakdown Choices",
                f"{team_name}: {top_choice['decision_label']} was the most frequent recorded breakdown "
                f"choice: {int(top_choice['count'])} of {len(choices)} Playmaker Option records.",
            )
        )

    break_summary = initial_breaks_by_player(events, team_name)
    top_break = _top_row(break_summary)
    if top_break is not None:
        total_breaks = int(break_summary["count"].sum())
        leader_count = int(top_break["count"])
        leader_count_of_players = int((break_summary["count"] == leader_count).sum())
        all_single = leader_count == 1 and leader_count_of_players == len(break_summary)
        if all_single:
            text = f"{team_name}: {len(break_summary)} players recorded one Initial Break each ({total_breaks} records)."
        elif leader_count_of_players > 1:
            text = (
                f"{team_name}: {leader_count_of_players} players shared the highest Initial Break count "
                f"({leader_count} each; {total_breaks} records)."
            )
        else:
            text = (
                f"{team_name}: {top_break['player_name']} recorded the most source Initial Breaks: "
                f"{leader_count} of {total_breaks}."
            )
        insights.append(
            Insight("Linebreaks", text)
        )

    tackle_outcomes = tackle_outcome_distribution(events, team_name)
    top_outcome = _top_row(tackle_outcomes)
    if top_outcome is not None:
        insights.append(
            Insight(
                "Tackling",
                f"{team_name}: {top_outcome['tackle_outcome']} was the most common recorded Tackle outcome: "
                f"{int(top_outcome['count'])} of {len(tackle_events(events, team_name))} Tackle actions.",
            )
        )

    evasion = evaded_tackles_by_associated_player(events, team_name)
    top_evasion = _top_row(evasion)
    if top_evasion is not None:
        leader_count = int(top_evasion["evaded_tackles"])
        if leader_count >= 2 and int((evasion["evaded_tackles"] == leader_count).sum()) == 1:
            insights.append(
                Insight(
                    "Evasion",
                    f"{top_evasion['associated_player_name']} recorded the most source-linked tackle evasions "
                    f"against {team_name}: {leader_count}.",
                )
            )
    return insights
