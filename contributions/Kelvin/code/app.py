"""Streamlit interface for the small CSV-based Rugby analysis prototype."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from analysis import (
    OVERVIEW_METRICS,
    calculate_attack_metrics,
    calculate_defence_metrics,
    calculate_discipline_metrics,
    calculate_kicking_metrics,
    calculate_match_overview,
    calculate_player_leaderboard,
    calculate_scoring_events,
    calculate_set_piece_metrics,
    calculate_team_performance,
    calculate_turnover_metrics,
    filter_event_locations,
    filter_match_data,
    friendly_label,
    generate_event_observation,
    generate_metric_observations,
    get_event_counts,
    get_match_metadata,
    get_matches,
    get_team_statistics,
    load_included_csv_data,
    load_uploaded_event_csv,
)
from charts import (
    create_event_comparison_chart,
    create_metric_comparison_chart,
    create_player_leaderboard,
    create_scoring_timeline,
    create_team_comparison_chart,
    plot_events_on_rugby_pitch,
)


APP_DIRECTORY = Path(__file__).resolve().parent
BUNDLED_CSV_DIRECTORY = APP_DIRECTORY / "data" / "sportradar_10_matches_csv"
REPOSITORY_CSV_DIRECTORY = (
    APP_DIRECTORY.parent / "data" / "raw" / "sportradar_10_matches_csv"
)

# The standalone contribution keeps CSVs beside the app. During local
# development, the prototype can continue using the repository-level source.
CSV_DATA_DIRECTORY = (
    BUNDLED_CSV_DIRECTORY
    if BUNDLED_CSV_DIRECTORY.is_dir()
    else REPOSITORY_CSV_DIRECTORY
)

ANALYSIS_OPTIONS = [
    "Match Overview",
    "Team Performance",
    "Attacking Analysis",
    "Defensive Analysis",
    "Set Piece Analysis",
    "Kicking Analysis",
    "Turnover Analysis",
    "Discipline Analysis",
    "Event Locations",
    "Scoring Analysis",
    "Player Analysis",
]


@st.cache_data(show_spinner=False)
def get_included_data() -> dict[str, pd.DataFrame]:
    """Cache the small five-file dataset between Streamlit widget changes."""
    return load_included_csv_data(CSV_DATA_DIRECTORY)


def display_number(value: object, decimals: int = 0) -> str:
    """Format a possibly missing numeric value for the interface."""
    if pd.isna(value):
        return "Not provided"
    number = float(value)
    if decimals == 0 and number.is_integer():
        return str(int(number))
    return f"{number:.{decimals}f}"


def display_metric_value(metric: str, value: object) -> str:
    if pd.isna(value):
        return "Not available"
    if metric in {"ball_possession", "tackle_success_rate", "scrum_success_rate"}:
        return f"{float(value):.1f}%"
    if metric == "metres_per_carry":
        return f"{float(value):.2f}"
    return display_number(value)


def create_display_table(data: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    """Create a readable metric-by-team table without renaming source columns."""
    rows: list[dict[str, str]] = []
    for metric in metrics:
        if metric not in data.columns:
            continue
        row: dict[str, str] = {"Metric": friendly_label(metric)}
        for _, team_row in data.iterrows():
            row[str(team_row["team"])] = display_metric_value(metric, team_row[metric])
        rows.append(row)
    return pd.DataFrame(rows)


def show_observations(observations: list[str]) -> None:
    st.subheader("Match observations")
    if observations:
        for observation in observations:
            st.write(f"- {observation}")
    else:
        st.info("No factual comparison is available for this selection.")


def show_pitch_caption() -> None:
    st.caption(
        "Locations use source-provided match coordinates. This prototype does not infer "
        "attacking direction."
    )


def match_label(row: pd.Series) -> str:
    round_text = "" if pd.isna(row["round"]) else f" — Round {display_number(row['round'])}"
    season = row["season"] if pd.notna(row["season"]) else "Season not provided"
    return f"{row['home_team']} vs {row['away_team']} — {season}{round_text}"


def show_player_leaders(
    player_stats: pd.DataFrame,
    team_names: list[str],
    metrics: list[str],
    key_prefix: str,
) -> None:
    """Display one selectable player leaderboard inside a team analysis page."""
    st.subheader("Player leaders")
    if player_stats.empty:
        st.info("Player statistics are not available for this match.")
        return
    selected_team = st.selectbox(
        "Team for player leaders", team_names, key=f"{key_prefix}_player_team"
    )
    selected_metric = st.selectbox(
        "Player metric",
        metrics,
        format_func=friendly_label,
        key=f"{key_prefix}_player_metric",
    )
    leaderboard = calculate_player_leaderboard(
        player_stats, selected_team, selected_metric
    )
    if leaderboard.empty:
        st.info("No player values are available for this selection.")
        return
    st.plotly_chart(
        create_player_leaderboard(
            leaderboard,
            selected_metric,
            f"{friendly_label(selected_metric)}: {selected_team}",
        ),
        width="stretch",
    )
    display = leaderboard.rename(
        columns={"player_name": "Player", selected_metric: friendly_label(selected_metric)}
    )
    st.dataframe(display, width="stretch", hide_index=True)


def show_match_overview(
    team_stats: pd.DataFrame,
    events: pd.DataFrame,
    team_names: list[str],
) -> None:
    overview = calculate_match_overview(team_stats)
    if overview.empty:
        st.info("Detailed box-score statistics are not available for this uploaded file.")
        event_types = [
            "ball_recycled",
            "ball_kicked",
            "line_out",
            "scrum",
            "turnover",
            "penalty_awarded",
        ]
        counts = get_event_counts(events, team_names, event_types)
        display = counts.copy()
        display["Event"] = display["event_type"].map(friendly_label)
        table = display.pivot(index="Event", columns="team", values="count").reset_index()
        st.dataframe(table, width="stretch", hide_index=True)
        st.plotly_chart(
            create_event_comparison_chart(counts, "Recorded event overview"),
            width="stretch",
        )
        kick_metrics = calculate_kicking_metrics(events, team_names)["metrics"]
        show_observations(
            generate_event_observation(kick_metrics, "recorded_kicks", "kick events", team_names)
        )
        return

    indexed = overview.set_index("team")
    columns = st.columns(4)
    columns[0].metric(
        f"{team_names[0]} possession",
        display_metric_value("ball_possession", indexed.loc[team_names[0], "ball_possession"]),
    )
    columns[1].metric(
        f"{team_names[1]} possession",
        display_metric_value("ball_possession", indexed.loc[team_names[1], "ball_possession"]),
    )
    columns[2].metric(
        f"{team_names[0]} tries", display_number(indexed.loc[team_names[0], "tries"])
    )
    columns[3].metric(
        f"{team_names[1]} tries", display_number(indexed.loc[team_names[1], "tries"])
    )
    st.dataframe(create_display_table(overview, OVERVIEW_METRICS), width="stretch", hide_index=True)
    chart_metrics = [
        "carries",
        "meters_run",
        "clean_breaks",
        "tackles",
        "turnovers_won",
        "penalties_conceded",
    ]
    st.plotly_chart(
        create_team_comparison_chart(overview, chart_metrics, "Selected match statistics"),
        width="stretch",
    )
    show_observations(
        generate_metric_observations(overview, ["carries", "meters_run"], team_names)
    )


def show_team_performance(team_stats: pd.DataFrame, team_names: list[str]) -> None:
    result = calculate_team_performance(team_stats)
    if result.empty:
        st.info("Detailed team statistics are not available for this match.")
        show_observations([])
        return
    source_metrics = [
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
    st.subheader("Source team statistics")
    st.dataframe(create_display_table(result, source_metrics), width="stretch", hide_index=True)
    st.plotly_chart(
        create_team_comparison_chart(result, source_metrics, "Team performance comparison"),
        width="stretch",
    )
    st.subheader("Calculated metrics")
    st.dataframe(
        create_display_table(result, ["metres_per_carry", "tackle_success_rate"]),
        width="stretch",
        hide_index=True,
    )
    st.caption(
        "Metres per carry = metres run / carries. Tackle success rate = tackles / "
        "(tackles + missed tackles). Values are calculated only when the denominator is positive."
    )
    show_observations(
        generate_metric_observations(
            result, ["metres_per_carry", "tackle_success_rate"], team_names
        )
    )


def show_attacking_analysis(
    team_stats: pd.DataFrame, player_stats: pd.DataFrame, team_names: list[str]
) -> None:
    result = calculate_attack_metrics(team_stats)
    if result.empty:
        st.info("Detailed team statistics are not available for this match.")
        show_observations([])
        return
    metrics = [
        "carries",
        "meters_run",
        "metres_per_carry",
        "passes",
        "offloads",
        "clean_breaks",
        "tries",
        "try_assist",
    ]
    st.dataframe(create_display_table(result, metrics), width="stretch", hide_index=True)
    st.plotly_chart(
        create_team_comparison_chart(
            result,
            ["carries", "meters_run", "passes", "offloads", "clean_breaks", "tries"],
            "Recorded attacking statistics",
        ),
        width="stretch",
    )
    st.caption("Calculated metres per carry is labelled separately from source statistics.")
    show_player_leaders(
        player_stats,
        team_names,
        ["carries", "meters_run", "clean_breaks", "offloads"],
        "attack",
    )
    show_observations(
        generate_metric_observations(result, ["meters_run", "clean_breaks"], team_names)
    )


def show_defensive_analysis(
    team_stats: pd.DataFrame, player_stats: pd.DataFrame, team_names: list[str]
) -> None:
    result = calculate_defence_metrics(team_stats)
    if result.empty:
        st.info("Detailed team statistics are not available for this match.")
        show_observations([])
        return
    metrics = ["tackles", "tackle_missed", "tackle_success_rate", "turnovers_won"]
    st.dataframe(create_display_table(result, metrics), width="stretch", hide_index=True)
    st.plotly_chart(
        create_team_comparison_chart(
            result, ["tackles", "tackle_missed", "turnovers_won"], "Recorded defensive statistics"
        ),
        width="stretch",
    )
    st.caption(
        "Calculated tackle success rate = tackles / (tackles + missed tackles), when attempts "
        "are greater than zero."
    )
    show_player_leaders(
        player_stats, team_names, ["tackles", "turnovers_won"], "defence"
    )
    show_observations(
        generate_metric_observations(
            result, ["tackle_success_rate", "turnovers_won"], team_names
        )
    )


def show_set_piece_analysis(
    team_stats: pd.DataFrame, events: pd.DataFrame, team_names: list[str]
) -> None:
    result = calculate_set_piece_metrics(team_stats)
    if result.empty:
        st.info("Detailed team statistics are not available for this match.")
        observations: list[str] = []
    else:
        metrics = [
            "lineouts_won",
            "total_scrums",
            "scrums_won",
            "scrums_lost",
            "scrum_success_rate",
        ]
        st.dataframe(create_display_table(result, metrics), width="stretch", hide_index=True)
        st.plotly_chart(
            create_team_comparison_chart(
                result,
                ["lineouts_won", "total_scrums", "scrums_won", "scrums_lost"],
                "Recorded set-piece statistics",
            ),
            width="stretch",
        )
        st.caption(
            "Calculated scrum success rate = scrums won / total scrums when total scrums is "
            "greater than zero."
        )
        observations = generate_metric_observations(
            result, ["lineouts_won", "scrum_success_rate"], team_names
        )

    st.subheader("Set-piece event locations")
    set_piece_types = ["line_out", "line_out_won", "scrum", "scrum_won", "scrum_reset"]
    selected_team = st.selectbox("Team", team_names, key="set_piece_team")
    selected_event = st.selectbox(
        "Set-piece event", set_piece_types, format_func=friendly_label, key="set_piece_event"
    )
    locations = filter_event_locations(events, selected_event, selected_team)
    if locations.empty:
        st.info("No location data is available for the selected events.")
    else:
        st.plotly_chart(
            plot_events_on_rugby_pitch(
                locations, f"{friendly_label(selected_event)} locations: {selected_team}"
            ),
            width="stretch",
        )
        show_pitch_caption()
    st.caption(
        "Timeline event locations provide context only. They do not reconstruct set-piece "
        "possession or attacking direction."
    )
    show_observations(observations)


def show_kicking_analysis(events: pd.DataFrame, team_names: list[str]) -> None:
    result = calculate_kicking_metrics(events, team_names)
    metrics = result["metrics"]
    display = metrics.rename(
        columns={
            "team": "Team",
            "recorded_kicks": "Recorded kicks",
            "kicks_to_touch": "Kicks to touch",
        }
    )
    st.dataframe(display, width="stretch", hide_index=True)
    st.plotly_chart(
        create_metric_comparison_chart(metrics, "recorded_kicks", "Kick events by team"),
        width="stretch",
    )
    st.caption(
        "The calculations retain the source labels ball_kicked and kick_to_touch. Separate "
        "records are not assumed to represent unique physical kicks."
    )
    selected_team = st.selectbox("Team for kick locations", team_names, key="kick_team")
    locations = result["locations"].loc[result["locations"]["team"] == selected_team]
    if locations.empty:
        st.info("No location data is available for the selected events.")
    else:
        st.plotly_chart(
            plot_events_on_rugby_pitch(locations, f"Kick locations: {selected_team}"),
            width="stretch",
        )
        show_pitch_caption()
    show_observations(
        generate_event_observation(metrics, "recorded_kicks", "kick events", team_names)
    )


def show_turnover_analysis(events: pd.DataFrame, team_names: list[str]) -> None:
    result = calculate_turnover_metrics(events, team_names)
    metrics = result["metrics"]
    st.dataframe(
        metrics.rename(columns={"team": "Team", "turnovers": "Turnovers"}),
        width="stretch",
        hide_index=True,
    )
    st.plotly_chart(
        create_metric_comparison_chart(metrics, "turnovers", "Turnover events by team"),
        width="stretch",
    )
    selected_team = st.selectbox("Team for turnover locations", team_names, key="turnover_team")
    locations = result["locations"].loc[result["locations"]["team"] == selected_team]
    if locations.empty:
        st.info("No location data is available for the selected events.")
    else:
        st.plotly_chart(
            plot_events_on_rugby_pitch(locations, f"Turnover locations: {selected_team}"),
            width="stretch",
        )
        show_pitch_caption()

    st.subheader("Next recorded event")
    if result["next_events"].empty:
        st.info("No following timeline events are available to classify.")
    else:
        table = result["next_events"].pivot(
            index="next_recorded_event", columns="team", values="count"
        ).fillna(0).reset_index()
        st.dataframe(table, width="stretch", hide_index=True)
    st.caption(
        "This uses only the next recorded timeline event. It is not a reconstructed possession "
        "sequence or tactical outcome."
    )
    show_observations(
        generate_event_observation(metrics, "turnovers", "turnover events", team_names)
    )


def show_discipline_analysis(
    team_stats: pd.DataFrame, events: pd.DataFrame, team_names: list[str]
) -> None:
    result = calculate_discipline_metrics(team_stats, events, team_names)
    if result["metrics"].empty:
        st.info("Detailed team statistics are not available for this match.")
        observations: list[str] = []
    else:
        metrics = ["penalties_conceded", "yellow_cards", "red_cards"]
        st.dataframe(
            create_display_table(result["metrics"], metrics), width="stretch", hide_index=True
        )
        st.plotly_chart(
            create_team_comparison_chart(
                result["metrics"], metrics, "Recorded discipline statistics"
            ),
            width="stretch",
        )
        observations = generate_metric_observations(
            result["metrics"], ["penalties_conceded", "yellow_cards"], team_names
        )

    st.subheader("Penalty awarded event locations")
    selected_team = st.selectbox("Team recorded on event", team_names, key="penalty_team")
    locations = result["locations"].loc[result["locations"]["team"] == selected_team]
    if locations.empty:
        st.info("No location data is available for the selected events.")
    else:
        st.plotly_chart(
            plot_events_on_rugby_pitch(
                locations, f"Penalty awarded locations: {selected_team}"
            ),
            width="stretch",
        )
        show_pitch_caption()
    st.caption(
        "penalty_awarded locations use the team recorded on the timeline event and are kept "
        "separate from the box-score penalties_conceded values."
    )
    show_observations(observations)


def show_event_locations(events: pd.DataFrame, team_names: list[str]) -> None:
    available_types = sorted(str(value) for value in events["event_type"].dropna().unique())
    if not available_types:
        st.info("No named event types were found for this match.")
        show_observations([])
        return
    selected_team = st.selectbox("Team", team_names, key="location_team")
    selected_event = st.selectbox(
        "Event type", available_types, format_func=friendly_label, key="location_event"
    )
    locations = filter_event_locations(events, selected_event, selected_team)
    if locations.empty:
        st.info("No location data is available for the selected events.")
    else:
        st.plotly_chart(
            plot_events_on_rugby_pitch(
                locations, f"{friendly_label(selected_event)} locations: {selected_team}"
            ),
            width="stretch",
        )
        show_pitch_caption()
    show_observations(
        [
            f"Among the recorded events, {len(locations)} {friendly_label(selected_event).lower()} "
            f"location(s) are available for {selected_team}."
        ]
    )


def show_scoring_analysis(events: pd.DataFrame, team_names: list[str]) -> None:
    scores = calculate_scoring_events(events)
    if scores.empty:
        st.info("No recorded score change events were found.")
        show_observations([])
        return
    st.plotly_chart(
        create_scoring_timeline(scores, team_names[0], team_names[1]), width="stretch"
    )
    table = scores[
        ["display_time", "team", "method", "scorer_name", "score"]
    ].rename(
        columns={
            "display_time": "Time",
            "team": "Team",
            "method": "Method",
            "scorer_name": "Player",
            "score": "Score",
        }
    )
    st.dataframe(table, width="stretch", hide_index=True)
    if st.checkbox("Show scoring locations", value=True):
        locations = scores.dropna(subset=["x", "y"])
        if locations.empty:
            st.info("No scoring location data is available for this match.")
        else:
            st.plotly_chart(
                plot_events_on_rugby_pitch(
                    locations, "Recorded scoring locations", colour_by="team"
                ),
                width="stretch",
            )
            show_pitch_caption()
    final = scores.iloc[-1]
    if pd.notna(final["home_score"]) and pd.notna(final["away_score"]):
        observations = [
            f"The last recorded score change shows {team_names[0]} "
            f"{display_number(final['home_score'])} and {team_names[1]} "
            f"{display_number(final['away_score'])}."
        ]
    else:
        observations = []
    show_observations(observations)


def show_player_analysis(player_stats: pd.DataFrame, team_names: list[str]) -> None:
    if player_stats.empty:
        st.info("Player statistics are not available for this match.")
        show_observations([])
        return
    selected_team = st.selectbox("Team", team_names, key="player_team")
    metrics = ["carries", "meters_run", "tackles", "clean_breaks", "turnovers_won"]
    selected_metric = st.selectbox(
        "Choose player metric", metrics, format_func=friendly_label, key="player_metric"
    )
    leaderboard = calculate_player_leaderboard(
        player_stats, selected_team, selected_metric
    )
    if leaderboard.empty:
        st.info("No player values are available for this selection.")
        show_observations([])
        return
    st.plotly_chart(
        create_player_leaderboard(
            leaderboard,
            selected_metric,
            f"{friendly_label(selected_metric)}: {selected_team}",
        ),
        width="stretch",
    )
    display = leaderboard.rename(
        columns={"player_name": "Player", selected_metric: friendly_label(selected_metric)}
    )
    st.dataframe(display, width="stretch", hide_index=True)
    leader = leaderboard.iloc[0]
    show_observations(
        [
            f"For {selected_team}, {leader['player_name']} recorded the highest displayed "
            f"{friendly_label(selected_metric).lower()} value ({display_number(leader[selected_metric])})."
        ]
    )


def main() -> None:
    st.set_page_config(page_title="Rugby Match Analysis Prototype", layout="wide")
    st.title("Rugby Match Analysis Prototype")
    st.write("Explore structured Rugby Union match data through interactive analysis.")

    st.header("Data source")
    use_included_dataset = st.checkbox("Use included CSV dataset", value=True)

    try:
        if use_included_dataset:
            all_data = get_included_data()
        else:
            uploaded_file = st.file_uploader(
                "Upload a compatible event-level CSV", type=["csv"]
            )
            if uploaded_file is None:
                st.info("Upload an event-level CSV to continue.")
                return
            all_data = load_uploaded_event_csv(uploaded_file)
    except ValueError as error:
        st.error(str(error))
        return

    matches = get_matches(all_data["metadata"])
    if matches.empty:
        st.error("No matches were found in the selected CSV data.")
        return
    labels = [match_label(row) for _, row in matches.iterrows()]
    default_index = next(
        (
            index
            for index, match_id in enumerate(matches["match_id"])
            if str(match_id) == "sr:sport_event:65866090"
        ),
        0,
    )
    selected_label = st.selectbox("Select match", labels, index=default_index)
    selected_index = labels.index(selected_label)
    selected_match_id = matches.iloc[selected_index]["match_id"]
    match_data = filter_match_data(all_data, selected_match_id)
    info = get_match_metadata(match_data["metadata"])
    if not info:
        st.error("Match information is not available for this selection.")
        return

    home_team = info["home_team"]
    away_team = info["away_team"]
    if pd.isna(home_team) or pd.isna(away_team):
        st.error("The selected CSV does not identify both home and away teams.")
        return
    team_names = [str(home_team), str(away_team)]
    events = match_data["events"]
    team_stats = get_team_statistics(match_data["team_stats"], team_names)
    player_stats = match_data["player_stats"]

    st.header("Match information")
    st.subheader(f"{home_team} vs {away_team}")
    competition = info["competition"] if pd.notna(info["competition"]) else "Competition not provided"
    season = info["season"] if pd.notna(info["season"]) else "Season not provided"
    round_text = (
        f"Round {display_number(info['round'])}" if pd.notna(info["round"]) else "Round not provided"
    )
    st.write(f"{competition} — {season} — {round_text}")
    first, second, third = st.columns(3)
    first.metric(
        "Final score",
        f"{home_team} {display_number(info['final_home_score'])} – "
        f"{display_number(info['final_away_score'])} {away_team}",
    )
    venue = info["venue"] if pd.notna(info["venue"]) else "Not provided"
    second.metric("Venue", venue)
    event_count = len(events)
    third.metric("Timeline events", event_count)

    st.header("Analysis")
    analysis_choice = st.selectbox("Choose analysis", ANALYSIS_OPTIONS)

    if analysis_choice == "Match Overview":
        show_match_overview(team_stats, events, team_names)
    elif analysis_choice == "Team Performance":
        show_team_performance(team_stats, team_names)
    elif analysis_choice == "Attacking Analysis":
        show_attacking_analysis(team_stats, player_stats, team_names)
    elif analysis_choice == "Defensive Analysis":
        show_defensive_analysis(team_stats, player_stats, team_names)
    elif analysis_choice == "Set Piece Analysis":
        show_set_piece_analysis(team_stats, events, team_names)
    elif analysis_choice == "Kicking Analysis":
        show_kicking_analysis(events, team_names)
    elif analysis_choice == "Turnover Analysis":
        show_turnover_analysis(events, team_names)
    elif analysis_choice == "Discipline Analysis":
        show_discipline_analysis(team_stats, events, team_names)
    elif analysis_choice == "Event Locations":
        show_event_locations(events, team_names)
    elif analysis_choice == "Scoring Analysis":
        show_scoring_analysis(events, team_names)
    elif analysis_choice == "Player Analysis":
        show_player_analysis(player_stats, team_names)

    st.caption(
        "This is a one-match descriptive proof of concept. Source event names remain unchanged "
        "internally, and observations do not infer tactical intent."
    )


if __name__ == "__main__":
    main()
