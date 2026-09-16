"""Matplotlib charts for the evidence available in the canonical event store."""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from rugby_analysis.analysis.event_frequency import event_counts, fixture_context
from rugby_analysis.analysis.scoring import score_value, scoring_events
from rugby_analysis.insights.rules import scoring_by_time_window, team_events, team_fixture_ids


TEAM_BLUE = "#1565c0"
ACCENT_GREEN = "#2e7d32"
NEUTRAL_GREY = "#607d8b"
WARNING_AMBER = "#ef6c00"


def filename_slug(value: str) -> str:
    """Return a portable, deterministic filename fragment."""

    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_") or "team"


def _save_figure(figure: plt.Figure, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(output_path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path


def _empty_chart(axis: plt.Axes, title: str, detail: str) -> None:
    axis.set_title(title, loc="left", fontweight="bold")
    axis.text(0.5, 0.5, detail, ha="center", va="center", color=NEUTRAL_GREY, wrap=True)
    axis.set_axis_off()


def render_event_profile_chart(
    events: pd.DataFrame,
    team_name: str,
    output_path: Path,
    match_ids: Iterable[str] | None = None,
) -> Path:
    """Plot counts of all source-recorded event types attributed to a team."""

    selected = team_events(events, team_name, match_ids)
    fixture_count = len(team_fixture_ids(events, team_name, match_ids))
    figure, axis = plt.subplots(figsize=(8.4, 4.8))
    counts = event_counts(selected)
    if counts.empty:
        _empty_chart(
            axis,
            f"{team_name}: source-recorded event profile",
            "No team-attributed canonical events are available for this selection.",
        )
        return _save_figure(figure, output_path)

    counts = counts.sort_values("event_count", ascending=True, kind="stable")
    axis.barh(counts["event_type"], counts["event_count"], color=TEAM_BLUE)
    axis.set_title(f"{team_name}: source-recorded event profile", loc="left", fontweight="bold")
    axis.set_xlabel("Number of canonical event records")
    axis.set_ylabel("")
    axis.grid(axis="x", alpha=0.2)
    axis.set_axisbelow(True)
    for bar, value in zip(axis.patches, counts["event_count"], strict=True):
        axis.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f" {int(value)}", va="center", fontsize=8)
    figure.text(
        0.01,
        0.01,
        f"{fixture_count} fixture(s) in scope. Event categories reflect the public source and are not full play-by-play.",
        fontsize=8,
        color=NEUTRAL_GREY,
    )
    return _save_figure(figure, output_path)


def _fixture_labels(events: pd.DataFrame, match_ids: list[str], team_name: str) -> dict[str, str]:
    context = fixture_context(events)
    labels: dict[str, str] = {}
    if context.empty:
        return {match_id: match_id for match_id in match_ids}
    for _, row in context.loc[context["match_id"].isin(match_ids)].iterrows():
        date = str(row.get("match_date") or "")[:10]
        home_team = str(row.get("home_team") or "")
        away_team = str(row.get("away_team") or "")
        opponent = away_team if home_team == team_name else home_team
        label = f"{date}\nvs {opponent}" if date and opponent else str(row.get("fixture_label") or row["match_id"])
        labels[str(row["match_id"])] = label
    return {match_id: labels.get(match_id, match_id) for match_id in match_ids}


def render_scoring_by_fixture_chart(
    events: pd.DataFrame,
    team_name: str,
    output_path: Path,
    match_ids: Iterable[str] | None = None,
) -> Path:
    """Plot source-provided score-event values per selected fixture, including zeros."""

    fixture_ids = team_fixture_ids(events, team_name, match_ids)
    selected = team_events(events, team_name, fixture_ids)
    scoring = scoring_events(selected).copy()
    figure, axis = plt.subplots(figsize=(max(8.4, min(15.0, 0.62 * max(len(fixture_ids), 1))), 4.8))
    if not fixture_ids:
        _empty_chart(
            axis,
            f"{team_name}: source score-event values by fixture",
            "No fixtures are available for this selection.",
        )
        return _save_figure(figure, output_path)

    if scoring.empty:
        point_map: dict[str, float] = {}
    else:
        scoring["points"] = pd.to_numeric(score_value(scoring), errors="coerce").fillna(0.0)
        point_map = scoring.groupby("match_id")["points"].sum().to_dict()
    points = [float(point_map.get(match_id, 0.0)) for match_id in fixture_ids]
    labels_by_match = _fixture_labels(events, fixture_ids, team_name)
    x_positions = list(range(len(fixture_ids)))
    axis.bar(x_positions, points, color=ACCENT_GREEN)
    axis.set_xticks(x_positions, [labels_by_match[match_id] for match_id in fixture_ids], rotation=55, ha="right", fontsize=8)
    axis.set_ylabel("Source score-event values")
    axis.set_title(f"{team_name}: source score-event values by fixture", loc="left", fontweight="bold")
    axis.grid(axis="y", alpha=0.2)
    axis.set_axisbelow(True)
    for x_position, value in zip(x_positions, points, strict=True):
        axis.text(x_position, value, f"{value:g}", ha="center", va="bottom", fontsize=8)
    figure.text(
        0.01,
        0.01,
        "Values are sums of the public source's score-event values; fixture labels come from source metadata.",
        fontsize=8,
        color=NEUTRAL_GREY,
    )
    return _save_figure(figure, output_path)


def render_scoring_timing_chart(
    events: pd.DataFrame,
    team_name: str,
    output_path: Path,
    match_ids: Iterable[str] | None = None,
) -> Path:
    """Plot score-event values in source-minute windows, without claiming periods."""

    selected = team_events(events, team_name, match_ids)
    windows = scoring_by_time_window(selected)
    figure, axis = plt.subplots(figsize=(8.4, 4.8))
    if windows.empty or float(windows["points"].sum()) == 0:
        _empty_chart(
            axis,
            f"{team_name}: timing of source score-event values",
            "No timed scoring points are available in the selected public records.",
        )
        return _save_figure(figure, output_path)

    colors = [TEAM_BLUE, TEAM_BLUE, ACCENT_GREEN, WARNING_AMBER]
    axis.bar(windows["time_window"].astype(str), windows["points"], color=colors[: len(windows)])
    axis.set_ylabel("Source score-event values")
    axis.set_xlabel("Source-minute window")
    axis.set_title(f"{team_name}: timing of source score-event values", loc="left", fontweight="bold")
    axis.grid(axis="y", alpha=0.2)
    axis.set_axisbelow(True)
    for bar, value, share in zip(axis.patches, windows["points"], windows["point_share"], strict=True):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:g} ({share * 100:.0f}%)",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    figure.text(
        0.01,
        0.01,
        "These are source-minute windows, not verified first-half/second-half periods.",
        fontsize=8,
        color=NEUTRAL_GREY,
    )
    return _save_figure(figure, output_path)


def generate_team_charts(
    events: pd.DataFrame,
    team_name: str,
    output_directory: Path,
    match_ids: Iterable[str] | None = None,
) -> dict[str, Path]:
    """Generate all report charts and return their local paths."""

    slug = filename_slug(team_name)
    output_directory = Path(output_directory)
    return {
        "event_profile": render_event_profile_chart(
            events, team_name, output_directory / f"{slug}_event_profile.png", match_ids
        ),
        "scoring_by_fixture": render_scoring_by_fixture_chart(
            events, team_name, output_directory / f"{slug}_scoring_by_fixture.png", match_ids
        ),
        "scoring_timing": render_scoring_timing_chart(
            events, team_name, output_directory / f"{slug}_scoring_timing.png", match_ids
        ),
    }
