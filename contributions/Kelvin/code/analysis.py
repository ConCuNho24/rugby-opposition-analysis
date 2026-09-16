"""Beginner-friendly CSV processing for the Rugby match prototype.

Raw source names such as ``ball_recycled`` and ``ball_kicked`` are never
changed in the DataFrames. Friendly labels are applied only when results are
displayed.
"""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO, TextIO

import pandas as pd


FRIENDLY_LABELS = {
    "ball_possession": "Ball possession",
    "ball_recycled": "Ball recycled",
    "ball_kicked": "Recorded kicks",
    "kick_to_touch": "Kicks to touch",
    "recorded_kicks": "Recorded kicks",
    "kicks_to_touch": "Kicks to touch",
    "line_out": "Lineout",
    "line_out_won": "Lineout won",
    "scrum": "Scrum",
    "scrum_won": "Scrum won",
    "scrum_reset": "Scrum reset",
    "turnover": "Turnover",
    "penalty_awarded": "Penalty awarded",
    "score_change": "Score change",
    "carries": "Carries",
    "meters_run": "Metres run",
    "metres_per_carry": "Calculated metres per carry",
    "passes": "Passes",
    "offloads": "Offloads",
    "clean_breaks": "Clean breaks",
    "tries": "Tries",
    "try_assist": "Try assists",
    "tackles": "Tackles",
    "tackle_missed": "Missed tackles",
    "tackle_success_rate": "Calculated tackle success rate",
    "turnovers_won": "Turnovers won",
    "penalties_conceded": "Penalties conceded",
    "penalty_goals": "Penalty goals",
    "yellow_cards": "Yellow cards",
    "red_cards": "Red cards",
    "lineouts_won": "Lineouts won",
    "total_scrums": "Total scrums",
    "scrums_won": "Scrums won",
    "scrums_lost": "Scrums lost",
    "scrum_success_rate": "Calculated scrum success rate",
}

EVENT_COLUMNS = [
    "match_id",
    "competition",
    "season",
    "round",
    "home_team",
    "away_team",
    "venue",
    "event_order",
    "event_type",
    "event_timestamp",
    "match_time_minute",
    "match_clock",
    "competitor",
    "team",
    "x",
    "y",
    "period",
    "home_score",
    "away_score",
    "method",
    "player_name",
    "scorer_name",
]

TEAM_STAT_COLUMNS = [
    "ball_possession",
    "carries",
    "clean_breaks",
    "conversions",
    "drop_goals",
    "lineouts_won",
    "meters_run",
    "offloads",
    "passes",
    "penalties_conceded",
    "penalty_goals",
    "red_cards",
    "scrums_lost",
    "scrums_won",
    "tackle_missed",
    "tackles",
    "total_scrums",
    "tries",
    "try_assist",
    "turnovers_won",
    "yellow_cards",
]

PLAYER_STAT_COLUMNS = [
    "carries",
    "clean_breaks",
    "meters_run",
    "offloads",
    "passes",
    "tackle_missed",
    "tackles",
    "try_assist",
    "turnovers_won",
]

OVERVIEW_METRICS = [
    "ball_possession",
    "tries",
    "penalty_goals",
    "carries",
    "meters_run",
    "clean_breaks",
    "tackles",
    "turnovers_won",
    "penalties_conceded",
]


def friendly_label(source_name: str) -> str:
    """Return a readable UI label without modifying the source value."""
    return FRIENDLY_LABELS.get(source_name, source_name.replace("_", " ").title())


def _read_csv(source: str | Path | BinaryIO | TextIO) -> pd.DataFrame:
    """Read one UTF-8 CSV and convert common pandas errors to a friendly error."""
    try:
        if hasattr(source, "seek"):
            source.seek(0)
        return pd.read_csv(source, encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError, pd.errors.EmptyDataError, pd.errors.ParserError) as error:
        raise ValueError("The selected file is not a readable UTF-8 CSV file.") from error


def _add_missing_columns(data: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Add optional columns so later calculations can safely reference them."""
    result = data.copy()
    for column in columns:
        if column not in result.columns:
            result[column] = pd.NA
    return result


def _prepare_events(events: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalise an event-level CSV DataFrame."""
    if "event_type" not in events.columns:
        raise ValueError("This CSV does not contain the required event_type column.")
    if events.empty:
        raise ValueError("The event CSV is empty, so there are no events to analyse.")

    result = _add_missing_columns(events, EVENT_COLUMNS)
    if result["match_id"].isna().all():
        result["match_id"] = "uploaded_match"

    numeric_columns = [
        "event_order",
        "match_time_minute",
        "x",
        "y",
        "home_score",
        "away_score",
    ]
    for column in numeric_columns:
        result[column] = pd.to_numeric(result[column], errors="coerce")

    # Compatible event files can contain home/away while leaving team blank.
    home_names = result["home_team"].where(result["competitor"] == "home")
    away_names = result["away_team"].where(result["competitor"] == "away")
    inferred_team = home_names.combine_first(away_names)
    result["team"] = result["team"].where(result["team"].notna(), inferred_team)

    result["source_order"] = range(len(result))
    return result.sort_values(
        ["event_order", "source_order"], kind="stable", na_position="last"
    ).reset_index(drop=True)


def _prepare_metadata(metadata: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "match_id",
        "competition",
        "season",
        "round",
        "home_team",
        "away_team",
        "venue",
        "venue_city",
        "venue_country",
        "status",
        "final_home_score",
        "final_away_score",
        "timeline_event_count",
    ]
    result = _add_missing_columns(metadata, columns)
    for column in ["round", "final_home_score", "final_away_score", "timeline_event_count"]:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    return result


def _prepare_team_statistics(team_stats: pd.DataFrame) -> pd.DataFrame:
    result = _add_missing_columns(team_stats, ["match_id", "team", *TEAM_STAT_COLUMNS])
    for column in TEAM_STAT_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    return result


def _prepare_player_statistics(player_stats: pd.DataFrame) -> pd.DataFrame:
    result = _add_missing_columns(
        player_stats, ["match_id", "team", "player_name", *PLAYER_STAT_COLUMNS]
    )
    for column in PLAYER_STAT_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    return result


def load_included_csv_data(data_directory: str | Path) -> dict[str, pd.DataFrame]:
    """Load the five CSV files supplied with the 10-match dataset."""
    directory = Path(data_directory)
    required_files = {
        "events": "combined_match_events.csv",
        "metadata": "match_metadata.csv",
        "team_stats": "team_statistics.csv",
        "player_stats": "player_statistics.csv",
        "period_scores": "period_scores.csv",
    }
    missing = [name for name in required_files.values() if not (directory / name).is_file()]
    if missing:
        raise ValueError(f"Included CSV dataset is missing: {', '.join(missing)}.")

    return {
        "events": _prepare_events(_read_csv(directory / required_files["events"])),
        "metadata": _prepare_metadata(_read_csv(directory / required_files["metadata"])),
        "team_stats": _prepare_team_statistics(
            _read_csv(directory / required_files["team_stats"])
        ),
        "player_stats": _prepare_player_statistics(
            _read_csv(directory / required_files["player_stats"])
        ),
        "period_scores": _read_csv(directory / required_files["period_scores"]),
    }


def _metadata_from_events(events: pd.DataFrame) -> pd.DataFrame:
    """Build the small metadata table needed when only event CSVs are uploaded."""
    rows: list[dict[str, object]] = []
    for match_id, match_events in events.groupby("match_id", dropna=False, sort=False):
        first = match_events.iloc[0]
        score_rows = match_events.dropna(subset=["home_score", "away_score"])
        last_score = score_rows.iloc[-1] if not score_rows.empty else None
        rows.append(
            {
                "match_id": match_id,
                "competition": first.get("competition"),
                "season": first.get("season"),
                "round": first.get("round"),
                "home_team": first.get("home_team"),
                "away_team": first.get("away_team"),
                "venue": first.get("venue"),
                "final_home_score": last_score.get("home_score") if last_score is not None else pd.NA,
                "final_away_score": last_score.get("away_score") if last_score is not None else pd.NA,
                "timeline_event_count": len(match_events),
            }
        )
    return _prepare_metadata(pd.DataFrame(rows))


def load_uploaded_event_csv(source: BinaryIO | TextIO) -> dict[str, pd.DataFrame]:
    """Load one compatible event CSV; box-score tables are intentionally empty."""
    events = _prepare_events(_read_csv(source))
    if events["home_team"].isna().all() or events["away_team"].isna().all():
        raise ValueError("This event CSV must identify home_team and away_team.")
    return {
        "events": events,
        "metadata": _metadata_from_events(events),
        "team_stats": _prepare_team_statistics(pd.DataFrame()),
        "player_stats": _prepare_player_statistics(pd.DataFrame()),
        "period_scores": pd.DataFrame(),
    }


def get_matches(metadata: pd.DataFrame) -> pd.DataFrame:
    """Return one selectable row per match."""
    columns = ["match_id", "home_team", "away_team", "competition", "season", "round"]
    return metadata[columns].drop_duplicates("match_id").reset_index(drop=True)


def filter_match_data(
    all_data: dict[str, pd.DataFrame], match_id: object
) -> dict[str, pd.DataFrame]:
    """Filter every available table to the selected match ID."""
    selected: dict[str, pd.DataFrame] = {}
    for name, table in all_data.items():
        if "match_id" in table.columns:
            selected[name] = table.loc[table["match_id"] == match_id].copy()
        else:
            selected[name] = table.copy()
    return selected


def get_match_metadata(metadata: pd.DataFrame) -> dict[str, object]:
    """Extract display-ready information for one selected match."""
    if metadata.empty:
        return {}
    row = metadata.iloc[0]
    return {
        "match_id": row.get("match_id"),
        "competition": row.get("competition"),
        "season": row.get("season"),
        "round": row.get("round"),
        "home_team": row.get("home_team"),
        "away_team": row.get("away_team"),
        "venue": row.get("venue"),
        "venue_city": row.get("venue_city"),
        "final_home_score": row.get("final_home_score"),
        "final_away_score": row.get("final_away_score"),
        "timeline_event_count": row.get("timeline_event_count"),
    }


def get_team_statistics(team_stats: pd.DataFrame, team_names: list[str]) -> pd.DataFrame:
    """Return team statistics in home-then-away display order."""
    if team_stats.empty:
        return team_stats.copy()
    return team_stats.set_index("team").reindex(team_names).reset_index()


def get_player_statistics(player_stats: pd.DataFrame, team_name: str) -> pd.DataFrame:
    """Return available player rows for one team."""
    if player_stats.empty:
        return player_stats.copy()
    return player_stats.loc[player_stats["team"] == team_name].copy()


def calculate_metres_per_carry(data: pd.DataFrame) -> pd.Series:
    """Calculate metres per carry only when carries are greater than zero."""
    carries = pd.to_numeric(data["carries"], errors="coerce")
    metres = pd.to_numeric(data["meters_run"], errors="coerce")
    return (metres / carries).where(carries > 0)


def calculate_tackle_success_rate(data: pd.DataFrame) -> pd.Series:
    """Calculate tackle success percentage only with a positive denominator."""
    tackles = pd.to_numeric(data["tackles"], errors="coerce")
    missed = pd.to_numeric(data["tackle_missed"], errors="coerce")
    attempts = tackles + missed
    return (tackles / attempts * 100).where(attempts > 0)


def _select_team_metrics(team_stats: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    if team_stats.empty:
        return pd.DataFrame(columns=["team", *metrics])
    return team_stats[["team", *metrics]].copy()


def calculate_match_overview(team_stats: pd.DataFrame) -> pd.DataFrame:
    return _select_team_metrics(team_stats, OVERVIEW_METRICS)


def calculate_team_performance(team_stats: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "ball_possession",
        "carries",
        "meters_run",
        "passes",
        "offloads",
        "clean_breaks",
        "turnovers_won",
        "tackles",
        "tackle_missed",
        "penalties_conceded",
    ]
    result = _select_team_metrics(team_stats, metrics)
    if not result.empty:
        result["metres_per_carry"] = calculate_metres_per_carry(result)
        result["tackle_success_rate"] = calculate_tackle_success_rate(result)
    return result


def calculate_attack_metrics(team_stats: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "carries",
        "meters_run",
        "passes",
        "offloads",
        "clean_breaks",
        "tries",
        "try_assist",
    ]
    result = _select_team_metrics(team_stats, metrics)
    if not result.empty:
        result["metres_per_carry"] = calculate_metres_per_carry(result)
    return result


def calculate_defence_metrics(team_stats: pd.DataFrame) -> pd.DataFrame:
    result = _select_team_metrics(
        team_stats, ["tackles", "tackle_missed", "turnovers_won"]
    )
    if not result.empty:
        result["tackle_success_rate"] = calculate_tackle_success_rate(result)
    return result


def calculate_set_piece_metrics(team_stats: pd.DataFrame) -> pd.DataFrame:
    result = _select_team_metrics(
        team_stats, ["lineouts_won", "total_scrums", "scrums_won", "scrums_lost"]
    )
    if not result.empty:
        total = pd.to_numeric(result["total_scrums"], errors="coerce")
        result["scrum_success_rate"] = (result["scrums_won"] / total * 100).where(total > 0)
    return result


def get_event_counts(
    events: pd.DataFrame, team_names: list[str], event_types: list[str]
) -> pd.DataFrame:
    """Count exact source event types and include zero rows for both teams."""
    attributed = events.loc[
        events["team"].notna() & events["event_type"].isin(event_types),
        ["event_type", "team"],
    ]
    counts = attributed.groupby(["event_type", "team"]).size()
    complete_index = pd.MultiIndex.from_product(
        [event_types, team_names], names=["event_type", "team"]
    )
    return counts.reindex(complete_index, fill_value=0).rename("count").reset_index()


def calculate_kicking_metrics(
    events: pd.DataFrame, team_names: list[str]
) -> dict[str, pd.DataFrame]:
    counts = get_event_counts(events, team_names, ["ball_kicked", "kick_to_touch"])
    metrics = (
        counts.pivot(index="team", columns="event_type", values="count")
        .reindex(team_names, fill_value=0)
        .reset_index()
        .rename(columns={"ball_kicked": "recorded_kicks", "kick_to_touch": "kicks_to_touch"})
    )
    locations = events.loc[
        events["event_type"].isin(["ball_kicked", "kick_to_touch"])
        & events["team"].notna()
        & events["x"].notna()
        & events["y"].notna()
    ].copy()
    return {"metrics": metrics, "locations": locations}


def _classify_next_event(event_type: object) -> str:
    if event_type in {"ball_kicked", "kick_to_touch"}:
        return "Kick"
    if event_type == "ball_recycled":
        return "Ball recycled"
    if event_type == "penalty_awarded":
        return "Penalty"
    return "Other"


def calculate_turnover_metrics(
    events: pd.DataFrame, team_names: list[str]
) -> dict[str, pd.DataFrame]:
    ordered = events.sort_values(["event_order", "source_order"], kind="stable").reset_index(
        drop=True
    )
    turnovers = ordered.loc[ordered["event_type"] == "turnover"].copy()
    counts = get_event_counts(ordered, team_names, ["turnover"])
    metrics = counts.drop(columns="event_type").rename(columns={"count": "turnovers"})

    following_rows: list[dict[str, object]] = []
    for position in turnovers.index:
        next_type = ordered.iloc[position + 1]["event_type"] if position + 1 < len(ordered) else None
        following_rows.append(
            {"team": ordered.iloc[position]["team"], "next_recorded_event": _classify_next_event(next_type)}
        )
    following = pd.DataFrame(following_rows, columns=["team", "next_recorded_event"])
    if not following.empty:
        following = (
            following.dropna(subset=["team"])
            .groupby(["team", "next_recorded_event"])
            .size()
            .rename("count")
            .reset_index()
        )
    return {
        "metrics": metrics,
        "locations": turnovers.dropna(subset=["x", "y"]),
        "next_events": following,
    }


def calculate_discipline_metrics(
    team_stats: pd.DataFrame, events: pd.DataFrame, team_names: list[str]
) -> dict[str, pd.DataFrame]:
    metrics = _select_team_metrics(
        team_stats, ["penalties_conceded", "yellow_cards", "red_cards"]
    )
    penalty_counts = get_event_counts(events, team_names, ["penalty_awarded"])
    penalty_locations = events.loc[
        (events["event_type"] == "penalty_awarded")
        & events["team"].notna()
        & events["x"].notna()
        & events["y"].notna()
    ].copy()
    return {
        "metrics": metrics,
        "penalty_counts": penalty_counts,
        "locations": penalty_locations,
    }


def filter_event_locations(
    events: pd.DataFrame, event_type: str, team_name: str
) -> pd.DataFrame:
    return events.loc[
        (events["event_type"] == event_type)
        & (events["team"] == team_name)
        & events["x"].notna()
        & events["y"].notna()
    ].copy()


def calculate_scoring_events(events: pd.DataFrame) -> pd.DataFrame:
    scores = events.loc[events["event_type"] == "score_change"].copy()
    if scores.empty:
        return pd.DataFrame(
            columns=[
                "match_time_minute",
                "display_time",
                "team",
                "method",
                "scorer_name",
                "home_score",
                "away_score",
                "score",
                "x",
                "y",
            ]
        )
    scores["scorer_name"] = scores["scorer_name"].where(
        scores["scorer_name"].notna(), scores["player_name"]
    ).fillna("Not provided")
    scores["method"] = scores["method"].fillna("Not provided")
    scores["display_time"] = scores.apply(
        lambda row: str(row["match_clock"])
        if pd.notna(row["match_clock"]) and str(row["match_clock"]).strip()
        else (
            f"{row['match_time_minute']:g} min"
            if pd.notna(row["match_time_minute"])
            else "Not provided"
        ),
        axis=1,
    )
    scores["score"] = scores.apply(
        lambda row: f"{int(row['home_score'])}-{int(row['away_score'])}"
        if pd.notna(row["home_score"]) and pd.notna(row["away_score"])
        else "Not provided",
        axis=1,
    )
    return scores.sort_values(["event_order", "source_order"], kind="stable")


def calculate_player_leaderboard(
    player_stats: pd.DataFrame, team_name: str, metric: str, limit: int = 8
) -> pd.DataFrame:
    if player_stats.empty or metric not in player_stats.columns:
        return pd.DataFrame(columns=["player_name", metric])
    selected = player_stats.loc[
        (player_stats["team"] == team_name) & player_stats["player_name"].notna(),
        ["player_name", metric],
    ].copy()
    selected[metric] = pd.to_numeric(selected[metric], errors="coerce")
    return selected.dropna(subset=[metric]).nlargest(limit, metric).reset_index(drop=True)


def _format_observation_value(metric: str, value: float) -> str:
    if metric in {"ball_possession", "tackle_success_rate", "scrum_success_rate"}:
        return f"{value:.1f}%"
    if metric == "metres_per_carry":
        return f"{value:.2f}"
    return f"{value:g}"


def generate_metric_observations(
    table: pd.DataFrame,
    metrics: list[str],
    team_names: list[str],
    max_observations: int = 2,
) -> list[str]:
    """Create conservative two-team comparisons from calculated table values."""
    if table.empty or len(team_names) != 2 or "team" not in table.columns:
        return []
    indexed = table.set_index("team")
    observations: list[str] = []
    for metric in metrics:
        if metric not in indexed.columns:
            continue
        first = pd.to_numeric(pd.Series([indexed[metric].get(team_names[0])]), errors="coerce").iloc[0]
        second = pd.to_numeric(pd.Series([indexed[metric].get(team_names[1])]), errors="coerce").iloc[0]
        if pd.isna(first) or pd.isna(second):
            continue
        label = friendly_label(metric).lower()
        if first == second:
            sentence = (
                f"In this match, both teams recorded {_format_observation_value(metric, first)} "
                f"for {label}."
            )
        else:
            high_team, high_value, low_team, low_value = (
                (team_names[0], first, team_names[1], second)
                if first > second
                else (team_names[1], second, team_names[0], first)
            )
            wording = "a higher" if "rate" in metric or metric == "ball_possession" else "more"
            sentence = (
                f"In this match, {high_team} recorded {wording} {label} than {low_team} "
                f"({_format_observation_value(metric, high_value)} compared with "
                f"{_format_observation_value(metric, low_value)})."
            )
        observations.append(sentence)
        if len(observations) >= max_observations:
            break
    return observations


def generate_event_observation(
    event_metrics: pd.DataFrame,
    metric: str,
    label: str,
    team_names: list[str],
) -> list[str]:
    """Create one factual event-count comparison."""
    if event_metrics.empty or metric not in event_metrics.columns:
        return []
    first = event_metrics.set_index("team")[metric].get(team_names[0], 0)
    second = event_metrics.set_index("team")[metric].get(team_names[1], 0)
    if first == second:
        return [f"In this match, both teams recorded {int(first)} {label}."]
    high_team, high_value, low_team, low_value = (
        (team_names[0], first, team_names[1], second)
        if first > second
        else (team_names[1], second, team_names[0], first)
    )
    return [
        f"In this match, {high_team} recorded {int(high_value)} {label} compared with "
        f"{int(low_value)} for {low_team}."
    ]
