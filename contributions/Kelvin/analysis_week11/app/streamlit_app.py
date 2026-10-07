"""Streamlit interface for the Week 11 opposition analysis prototype.

Run from ``analysis_week11`` with ``streamlit run app/streamlit_app.py``.
Raw partner data stays local and is never packaged into source control.
"""

from __future__ import annotations

import os
import sys
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st


APP_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = APP_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from week11_analysis.analysis.breakdown import (  # noqa: E402
    available_breakdown_zones,
    breakdown_choice_table,
    playmaker_option_events,
)
from week11_analysis.analysis.game_intervals import (  # noqa: E402
    recorded_event_intervals,
    try_action_intervals,
)
from week11_analysis.analysis.event_replay import (  # noqa: E402
    build_replay_sequence,
    current_event_metadata,
    event_path,
    recent_event_trail,
    replay_actions,
)
from week11_analysis.analysis.event_effects import (  # noqa: E402
    classify_event_effect,
    event_effect_coverage,
)
from week11_analysis.analysis.insights import generate_key_insights  # noqa: E402
from week11_analysis.analysis.kicking import (  # noqa: E402
    kick_end_locations,
    kick_events,
    kick_outcome_distribution,
    kick_position_distribution,
    kick_receipt_contest_status,
    kick_summary_cards,
    kick_type_distribution,
    kick_type_events,
    kicker_summary,
)
from week11_analysis.analysis.linebreaks import (  # noqa: E402
    initial_break_events,
    initial_break_results_from_records,
    initial_breaks_by_player_from_records,
    initial_breaks_by_position_from_records,
    linebreak_achieved_conceded_summary,
    offload_pass_events,
    offload_passes_by_player,
    opponent_initial_break_events,
)
from week11_analysis.analysis.tackling import (  # noqa: E402
    dominant_tackle_outcome_matrix,
    evaded_tackles_by_associated_player,
    first_tackler_missed_by_player,
    first_tackler_outcomes,
    missed_tackle_player_positions,
    player_tackle_outcome_matrix,
    tackle_height_distribution,
    tackle_locations,
    tackle_outcome_distribution,
    tackle_summary_cards,
)
from week11_analysis.analysis.zones import ALL_ZONES_LABEL, DEFAULT_ZONE_CONFIG  # noqa: E402
from week11_analysis.data.loader import (  # noqa: E402
    PartnerFileSource,
    load_partner_batch,
    load_partner_data,
)
from week11_analysis.data.transformation import (  # noqa: E402
    filter_fixture,
    fixture_summary,
    unique_non_null,
)
from week11_analysis.visualisation.charts import count_bar_chart  # noqa: E402
from week11_analysis.visualisation.pitch import (  # noqa: E402
    coordinate_diagnostics,
    plot_event_replay,
    plot_event_locations,
    plot_field_segments,
)


PAGES = [
    "Overview",
    "Key Insights",
    "Game Intervals",
    "Event Replay",
    "Kicking",
    "Linebreaks",
    "Breakdown Choices",
    "Tackling",
]


@st.cache_data(show_spinner=False)
def load_cached_data(path_text: str):
    """Cache the development-only local-path fallback between interactions."""

    return load_partner_data(path_text)


@st.cache_data(show_spinner=False)
def load_uploaded_batch_cached(file_payloads: tuple[tuple[str, bytes], ...]):
    """Load immutable upload payloads in memory, isolated by name and content."""

    sources = tuple(
        PartnerFileSource(BytesIO(contents), filename=file_name)
        for file_name, contents in file_payloads
    )
    return load_partner_batch(sources)


def apply_theme() -> None:
    """Apply a compact dark visual system without changing source values."""

    st.markdown(
        """
        <style>
        .stApp { background: #0b1117; color: #e9f1ed; }
        [data-testid="stSidebar"] { background: #101a22; }
        [data-testid="stMetric"] {
          background: #14232b; border: 1px solid #29424a; border-radius: 10px;
          padding: 0.75rem;
        }
        [data-testid="stMetricLabel"], [data-testid="stMetricValue"] { color: #e9f1ed; }
        .stCaption, [data-testid="stMarkdownContainer"] p { color: #c5d2cd; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def display_summary_table(summary: pd.DataFrame, rename_columns: dict[str, str]) -> None:
    """Render a source-labelled summary with safe empty handling."""

    if summary.empty:
        st.info("No source records are available for this selection.")
        return
    display = summary.rename(columns=rename_columns)
    if "Percentage" in display.columns:
        st.dataframe(
            display.style.format({"Percentage": "{:.1f}%"}), width="stretch", hide_index=True
        )
    else:
        st.dataframe(display, width="stretch", hide_index=True)


def show_coordinate_note(events: pd.DataFrame, label: str = "Recorded coordinates") -> None:
    """Expose coordinate quality beside every pitch, rather than hiding it."""

    diagnostics = coordinate_diagnostics(events)
    st.caption(
        f"{label}: {diagnostics['count']} rows; x {diagnostics['x_range']}; "
        f"y {diagnostics['y_range']}; {diagnostics['out_of_bounds']} row(s) outside "
        "nominal 0-100 x 0-70. Values are displayed, not clamped or direction-flipped."
    )


def selected_fixture(events: pd.DataFrame) -> pd.DataFrame:
    """Offer a reusable fixture selector even for a currently single-match input."""

    fixtures = fixture_summary(events)
    if "fixture_id" in fixtures.columns:
        fixtures = fixtures.loc[fixtures["fixture_id"].notna()].copy()
    if fixtures.empty:
        st.error("No fixture identifiers are available in the selected partner file.")
        st.stop()
    labels: dict[str, str] = {}
    for row in fixtures.itertuples(index=False):
        fixture_id = str(row.fixture_id)
        home_value = getattr(row, "home_team_name", None)
        away_value = getattr(row, "away_team_name", None)
        home = (
            str(home_value).strip()
            if home_value is not None and not pd.isna(home_value) and str(home_value).strip()
            else None
        )
        away = (
            str(away_value).strip()
            if away_value is not None and not pd.isna(away_value) and str(away_value).strip()
            else None
        )
        fixture_teams = unique_non_null(filter_fixture(events, fixture_id)["team_name"])
        if home is None:
            home = next((team for team in fixture_teams if team != away), "Home team not supplied")
        if away is None:
            away = next((team for team in fixture_teams if team != home), "Opponent not supplied")
        labels[fixture_id] = f"{home} vs {away} (fixture {fixture_id})"
    fixture_ids = list(labels)
    selected_id = st.sidebar.selectbox(
        "Fixture", fixture_ids, format_func=lambda fixture_id: labels[fixture_id]
    )
    return filter_fixture(events, selected_id)


def show_overview(events: pd.DataFrame, team_name: str, source_name: str) -> None:
    st.header("Overview")
    st.caption("A descriptive view of the selected fixture. It is not a competition benchmark.")
    fixture = fixture_summary(events).iloc[0]
    cards = st.columns(4)
    cards[0].metric("Fixture", str(fixture["fixture_id"]))
    cards[1].metric("Selected team", team_name)
    cards[2].metric("Event records", len(events))
    cards[3].metric("Analysis pages", "7")
    st.caption(
        f"Event Replay | Kicking | Linebreaks | Breakdown Choices | Tackling | Game Intervals | Key Insights. "
        f"Loaded from {source_name}."
    )
    before, now = st.columns(2)
    with before:
        st.subheader("Earlier prototype")
        st.write(
            "Week 9 explored public Sportradar event data. It informed the interface, but used a different "
            "data structure from the partner export."
        )
    with now:
        st.subheader("Week 11 prototype")
        st.write(
            "This version loads the partner event schema, validates it, and presents recorded event views for "
            "opposition analysis."
        )
    st.subheader("Workflow")
    st.code(
        "Authorised partner XLSX / CSV -> schema validation -> event transformation -> "
        "analysis pages -> Streamlit preview",
        language="text",
    )
    st.warning(
        "Current limits: one representative fixture, no competition averages, and no possession, phase, "
        "ball-in-play or inferred success measures."
    )
    st.info(
        "Coordinate convention: x=0 is the event team's own tryline and x=100 is its opposition tryline. "
        "The app preserves that orientation for every team."
    )


def show_key_insights(events: pd.DataFrame, team_name: str) -> None:
    st.header("Key Insights")
    st.caption("Observations based on the selected team's recorded event rows.")
    insights = generate_key_insights(events, team_name)
    if not insights:
        st.info("No recorded-event insight is available for this selection.")
        return
    for insight in insights:
        st.markdown(f"**{insight.module}** - {insight.text}")
    st.caption("These describe recorded rows rather than forecasts, rankings, or causal claims.")


def show_game_intervals(events: pd.DataFrame, team_name: str) -> None:
    st.header("Game Intervals")
    st.caption(
        "MatchTime is the partner's mmss display clock. Intervals count recorded event activity; "
        "they are not possession or ball-in-play durations."
    )
    density = recorded_event_intervals(events, team_name)
    tries = try_action_intervals(events, team_name)
    cards = st.columns(3)
    cards[0].metric("Selected-team event rows", len(events.loc[events["team_name"].eq(team_name)]))
    cards[1].metric("Valid-clock event rows", int(density["count"].sum()) if not density.empty else 0)
    cards[2].metric("Source Try action rows", int(tries["count"].sum()) if not tries.empty else 0)
    left, right = st.columns(2)
    with left:
        st.subheader("Recorded event activity")
        st.plotly_chart(
            count_bar_chart(density, "interval", "All source event rows by 10-minute interval"),
            width="stretch",
        )
        display_summary_table(density, {"interval": "Match-time interval", "count": "Source event rows"})
    with right:
        st.subheader("Explicit Try action records")
        st.plotly_chart(
            count_bar_chart(tries, "interval", "Try action rows by 10-minute interval"), width="stretch"
        )
        display_summary_table(tries, {"interval": "Match-time interval", "count": "Try action rows"})
    st.info("A `Try` row is shown exactly as supplied. Goal-kick rows and conversion outcomes are not combined into a calculated score.")


def _format_event_coordinates(coordinates: tuple[float, float] | None) -> str | None:
    """Format one recorded coordinate pair for the Event Replay detail panel."""

    if coordinates is None:
        return None
    return f"x={coordinates[0]:g}, y={coordinates[1]:g}"


def _event_text_value(value: object) -> str | None:
    """Return one non-empty source value for concise Event Replay metadata."""

    if value is None:
        return None
    try:
        if bool(pd.isna(value)):
            return None
    except (TypeError, ValueError):
        return None
    text = str(value).strip()
    return text or None


def _move_replay_index(delta: int, upper_bound: int) -> None:
    """Advance the replay slider from a button callback before the page reruns."""

    current = int(st.session_state.get("event_replay_index", 0))
    st.session_state["event_replay_index"] = min(max(current + delta, 0), upper_bound)


def _action_effect_summary(events: pd.DataFrame) -> pd.DataFrame:
    """Condense the reusable coverage audit into one row per source action."""

    coverage = event_effect_coverage(events)
    if coverage.empty:
        return pd.DataFrame(columns=["Action", "Effect family", "Records", "Coverage"])

    def family_text(values: pd.Series) -> str:
        return ", ".join(sorted(set(values)))

    def status_text(values: pd.Series) -> str:
        unique = set(values)
        if unique == {"covered"}:
            return "Covered"
        if unique == {"fallback"}:
            return "Fallback"
        return "Covered with fallback"

    return (
        coverage.groupby("action_name", as_index=False, dropna=False)
        .agg(
            effect_family=("effect_family", family_text),
            record_count=("record_count", "sum"),
            coverage_status=("coverage_status", status_text),
        )
        .rename(
            columns={
                "action_name": "Action",
                "effect_family": "Effect family",
                "record_count": "Records",
                "coverage_status": "Coverage",
            }
        )
        .sort_values(["Records", "Action"], ascending=[False, True], kind="stable")
        .reset_index(drop=True)
    )


def show_event_replay(events: pd.DataFrame, team_name: str) -> None:
    """Show recorded rows with semantic, source-faithful visual cues."""

    st.header("Event Replay")
    st.caption(
        "Event Replay shows the sequence and field location of recorded match events. "
        "It is event data, not continuous player tracking."
    )
    st.caption(
        "Event locations use team-relative source coordinates: x=0 is the team's own tryline and "
        "x=100 is the opposition tryline."
    )
    fixture_ids = events["fixture_id"].dropna()
    if fixture_ids.empty:
        st.info("No fixture identifier is available for Event Replay.")
        return
    fixture_id = fixture_ids.iloc[0]

    filter_column, trail_column = st.columns([3, 2])
    with filter_column:
        event_label = st.selectbox(
            "Event action or type",
            ["All recorded events", *replay_actions(events, fixture_id, team_name)],
            key="event_replay_action_filter",
            help="Options come from the selected team's recorded action and action-type labels.",
        )
    with trail_column:
        show_trail = st.checkbox(
            "Show previous five events",
            value=True,
            key="event_replay_show_trail",
        )

    action_filter = None if event_label == "All recorded events" else event_label
    replay_events = build_replay_sequence(events, fixture_id, team_name, action_filter)
    if replay_events.empty:
        st.info("No recorded events match this team and event filter.")
        return

    signature = (str(fixture_id), team_name, action_filter, len(replay_events))
    index_key = "event_replay_index"
    signature_key = "event_replay_sequence_signature"
    if st.session_state.get(signature_key) != signature:
        st.session_state[signature_key] = signature
        st.session_state[index_key] = 0
    current_index = int(st.session_state.get(index_key, 0))
    current_index = min(max(current_index, 0), len(replay_events) - 1)
    st.session_state[index_key] = current_index

    if len(replay_events) == 1:
        event_index = 0
        st.caption("One recorded event matches this filter.")
    else:
        previous_column, timeline_column, next_column = st.columns([1, 4, 1])
        with previous_column:
            st.button(
                "Previous",
                key="event_replay_previous",
                disabled=current_index == 0,
                on_click=_move_replay_index,
                args=(-1, len(replay_events) - 1),
            )
        with next_column:
            st.button(
                "Next",
                key="event_replay_next",
                disabled=current_index == len(replay_events) - 1,
                on_click=_move_replay_index,
                args=(1, len(replay_events) - 1),
            )
        with timeline_column:
            event_index = st.slider(
                "Recorded event position",
                min_value=0,
                max_value=len(replay_events) - 1,
                key=index_key,
                help="Move through the filtered sequence one recorded event row at a time.",
            )

    metadata = current_event_metadata(replay_events, event_index)
    current_event = replay_events.iloc[event_index]
    if metadata is None:
        st.info("No event is available at this timeline position.")
        return
    st.caption(
        f"Event {metadata['event_number']} of {metadata['event_count']}"
        + (f" | Match time: {metadata['match_time']}" if metadata["match_time"] else "")
        + ". Events are ordered by source period and event timestamp; MatchTime is shown as recorded."
    )

    trail = recent_event_trail(replay_events, event_index, limit=5) if show_trail else replay_events.iloc[0:0]
    recorded_path = event_path(current_event)
    effect_profile = classify_event_effect(current_event)
    effect_column, animation_column = st.columns([2, 3])
    with effect_column:
        show_event_effect = st.checkbox(
            "Show event effect",
            value=True,
            key="event_replay_show_effect",
            help="Show the source-supported cue for the selected event type.",
        )
    with animation_column:
        animate_event = False
        if effect_profile.allows_local_interpolation and recorded_path is not None:
            animate_event = st.checkbox(
                "Animate source movement",
                value=False,
                key="event_replay_animate_effect",
                help="Play a short cue from this event's recorded start to end only.",
            )

    pitch_column, details_column = st.columns([3, 2])
    with pitch_column:
        st.plotly_chart(
            plot_event_replay(
                current_event,
                trail,
                recorded_path,
                effect_profile=effect_profile,
                show_event_effect=show_event_effect,
                animate_event=animate_event,
            ),
            width="stretch",
            config={"displayModeBar": False},
        )
        if show_event_effect and effect_profile.uses_recorded_path:
            st.caption(
                "The route and optional motion use start and end coordinates recorded on this event only. "
                "They do not connect separate events."
            )
        if not metadata["has_recorded_location"]:
            st.info("No field location was recorded for this event.")
        elif metadata["location_within_nominal_field"] is False:
            st.warning("This event is outside the nominal 0-100 by 0-70 field and is shown as supplied.")

    with details_column:
        st.subheader("Current event")
        st.markdown(f"**Visual effect:** {effect_profile.visual_label}")
        if metadata["match_time"]:
            st.metric("Match time", metadata["match_time"])
        if metadata["team_name"]:
            st.markdown(f"**Team:** {metadata['team_name']}")
        if metadata["player_name"]:
            st.markdown(f"**Player:** {metadata['player_name']}")
        if metadata["action_name"]:
            action_text = metadata["action_name"]
            if metadata["action_type_name"] and metadata["action_type_name"] != action_text:
                action_text += f" - {metadata['action_type_name']}"
            st.markdown(f"**Event:** {action_text}")
        if metadata["action_result_name"]:
            st.markdown(f"**Outcome:** {metadata['action_result_name']}")
        if effect_profile.show_associated_player:
            associated_player = _event_text_value(current_event.get("associated_player_name"))
            if associated_player:
                st.markdown(f"**Associated player:** {associated_player}")
        start = _format_event_coordinates(metadata["start_coordinates"])
        end = _format_event_coordinates(metadata["end_coordinates"])
        if start:
            st.markdown(f"**Start:** {start}")
        if end:
            st.markdown(f"**End:** {end}")
        if metadata["recorded_qualifiers"]:
            st.caption("Recorded details")
            for qualifier in metadata["recorded_qualifiers"]:
                st.write(f"- {qualifier}")
        if metadata["source_file_name"]:
            st.caption(f"Source file: {metadata['source_file_name']}")

    raw_columns = [
        "event_id",
        "source_file_name",
        "fixture_id",
        "period",
        "start_seconds",
        "match_time_raw",
        "match_clock",
        "team_name",
        "player_name",
        "action_name",
        "action_type_name",
        "action_result_name",
        "x",
        "y",
        "x_end",
        "y_end",
        "qualifier_3_name",
        "qualifier_4_name",
        "qualifier_5_name",
        "qualifier_6_name",
        "qualifier_7_name",
        "qualifier_8_name",
        "qualifier_9_name",
        "qualifier_10_name",
        "associated_player_name",
        "associated_player_team_name",
    ]
    available_columns = [column for column in raw_columns if column in current_event.index]
    with st.expander("View source event details"):
        st.dataframe(
            current_event.reindex(available_columns).to_frame().T,
            width="stretch",
            hide_index=True,
        )

    with st.expander("Event-effect coverage for this fixture"):
        st.caption(
            "Every action is assigned a visual family. Rows without enough source semantics use the "
            "neutral fallback rather than an inferred rugby action."
        )
        st.dataframe(_action_effect_summary(events), width="stretch", hide_index=True)


def show_kicking(events: pd.DataFrame, team_name: str) -> None:
    st.header("Kicking")
    st.caption("Scope: `actionName = Kick` only. `Goal Kick` and `Defensive Exits` remain separate source actions.")
    cards = kick_summary_cards(events, team_name)
    metric_columns = st.columns(4)
    metric_columns[0].metric("Kick records", cards["total"])
    metric_columns[1].metric("Most common type", str(cards["common_type"]))
    metric_columns[2].metric("Top source-recorded kicker", str(cards["top_kicker"]))
    metric_columns[3].metric("Most common outcome", str(cards["common_outcome"]))

    types = kick_type_distribution(events, team_name)
    outcomes = kick_outcome_distribution(events, team_name)
    left, right = st.columns(2)
    with left:
        st.subheader("Kick selection")
        st.plotly_chart(count_bar_chart(types, "kick_type", "Source kick types"), width="stretch")
        display_summary_table(types, {"kick_type": "Kick type", "count": "Count", "percentage": "Percentage"})
    with right:
        st.subheader("Recorded outcomes")
        st.plotly_chart(count_bar_chart(outcomes, "kick_outcome", "Source kick outcomes", horizontal=True), width="stretch")
        display_summary_table(outcomes, {"kick_outcome": "Source outcome", "count": "Count", "percentage": "Percentage"})

    contest, positions = st.columns(2)
    with contest:
        st.subheader("Recorded Kick Receipt Contest Status")
        st.caption(
            "This view uses contest status recorded in source event qualifiers. It is not assumed "
            "to be identical to the Reds' official 'Contestable Kick' metric."
        )
        display_summary_table(
            kick_receipt_contest_status(events, team_name),
            {"contest_status": "Source receipt status", "count": "Kick records", "percentage": "Percentage"},
        )
    with positions:
        st.subheader("Kicks by source-recorded player position")
        st.caption("Exact `playerpositionName` values are displayed; no broad positional grouping is inferred.")
        display_summary_table(
            kick_position_distribution(events, team_name),
            {"player_position_name": "Source position", "count": "Kick records", "percentage": "Percentage"},
        )

    source_types = [str(value) for value in types["kick_type"].tolist()]
    selected_type = st.selectbox(
        "Kick category for location and kicker detail", ["All Kick records", *source_types]
    )
    selected = (
        kick_events(events, team_name)
        if selected_type == "All Kick records"
        else kick_type_events(events, team_name, selected_type)
    )
    detail_title = "all Kick records" if selected_type == "All Kick records" else f"{selected_type} records"
    st.subheader(f"Recorded locations: {detail_title}")
    starts, ends = st.columns(2)
    with starts:
        start_locations = selected.dropna(subset=["x", "y"])
        st.plotly_chart(
            plot_event_locations(start_locations, f"Kick start locations - {detail_title}", "action_type_name"),
            width="stretch",
        )
        show_coordinate_note(start_locations, "Recorded start coordinates")
    with ends:
        end_locations = kick_end_locations(selected)
        st.plotly_chart(
            plot_event_locations(end_locations, f"Kick end locations - {detail_title}", "action_type_name"),
            width="stretch",
        )
        show_coordinate_note(end_locations, "Recorded end coordinates")
    st.subheader("Kickers")
    display_summary_table(
        kicker_summary(selected),
        {"player_name": "Source-recorded player", "count": "Kick records", "percentage": "Percentage"},
    )
    st.caption("These pitches show recorded start and end coordinates, not a reconstructed trajectory or kick-distance model.")


def _show_linebreak_side(records: pd.DataFrame, title: str, category_label: str) -> None:
    """Render one source-owned side of the team-level Initial Break comparison."""

    st.subheader(title)
    summary_left, summary_right = st.columns(2)
    with summary_left:
        display_summary_table(
            initial_break_results_from_records(records),
            {"source_result": "Source result", "count": "Count", "percentage": "Percentage"},
        )
    with summary_right:
        display_summary_table(
            initial_breaks_by_player_from_records(records),
            {"player_name": "Player", "count": "Initial Break records", "percentage": "Percentage"},
        )
        display_summary_table(
            initial_breaks_by_position_from_records(records),
            {"player_position_name": "Position", "count": "Initial Break records", "percentage": "Percentage"},
        )
    locations = records.dropna(subset=["x", "y"])
    st.plotly_chart(
        plot_event_locations(locations, f"Initial Break start locations - {category_label}", "action_result_name"),
        width="stretch",
    )
    show_coordinate_note(locations, f"Recorded coordinates - {category_label}")


def show_linebreaks(events: pd.DataFrame, team_name: str) -> None:
    st.header("Linebreaks")
    st.caption(
        "Supported subset: `actionName = Attacking Qualities` and `actionTypeName = Initial Break`. "
        "Results retain source labels, including `Line Break` and `Kick Line Break`."
    )
    achieved = initial_break_events(events, team_name)
    conceded = opponent_initial_break_events(events, team_name)
    comparison = linebreak_achieved_conceded_summary(events, team_name)
    cards = st.columns(3)
    cards[0].metric("Linebreaks achieved", int(comparison.iloc[0]["count"]))
    cards[1].metric("Linebreaks conceded", int(comparison.iloc[1]["count"]))
    cards[2].metric("Source Offload pass rows", len(offload_pass_events(events, team_name)))
    st.caption(
        "Achieved = selected-team Initial Break events. Conceded = opponent Initial Break events in this selected "
        "fixture. This is a team-level comparison only; no individual defender is attributed."
    )
    display_summary_table(
        comparison,
        {"view": "View", "source_team": "Source-owned event team", "count": "Initial Break records"},
    )
    achieved_tab, conceded_tab = st.tabs(["Achieved", "Conceded"])
    with achieved_tab:
        _show_linebreak_side(achieved, f"Achieved by {team_name}", team_name)
    with conceded_tab:
        opponent_label = ", ".join(sorted({str(value) for value in conceded["team_name"].dropna().unique()}))
        _show_linebreak_side(
            conceded,
            f"Conceded to {opponent_label or 'opponent records'}",
            opponent_label or "opponents",
        )
    st.subheader("Source-recorded Offload passes")
    st.caption("`actionName = Pass` and `actionTypeName = Offload`; it is not attributed to a tackle without an explicit link.")
    display_summary_table(
        offload_passes_by_player(events, team_name),
        {"player_name": "Player", "count": "Offload pass rows", "percentage": "Percentage"},
    )
    st.info("This page does not infer individual defender responsibility, phase, or a relationship between a linebreak and another event type.")


def show_breakdown(events: pd.DataFrame, team_name: str) -> None:
    st.header("Breakdown Choices")
    st.caption(
        "Uses `Playmaker Options` rows with `Playmaker Option - Pass/Carry/Kick` results. The bands are transparent "
        "25m x-coordinate filters, not asserted Reds A/B/C/D/E zones."
    )
    zones = available_breakdown_zones(events)
    zone = st.radio("Relative field segment", zones, horizontal=True)
    highlight = "" if zone == ALL_ZONES_LABEL else zone
    st.plotly_chart(
        plot_field_segments(highlight, DEFAULT_ZONE_CONFIG.labels, DEFAULT_ZONE_CONFIG.edges),
        width="stretch",
        config={"displayModeBar": False},
    )
    summary = breakdown_choice_table(events, team_name, zone)
    st.metric("Playmaker Option records in selected segment", int(summary["count"].sum()) if not summary.empty else 0)
    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            count_bar_chart(summary, "decision_label", f"Breakdown choices: {zone}", horizontal=True),
            width="stretch",
        )
    with right:
        display_summary_table(
            summary,
            {
                "decision": "Decision",
                "receiver_context": "Receiver context",
                "decision_label": "Breakdown choice",
                "count": "Count",
                "percentage": "Percentage",
            },
        )
    st.caption(f"All selected-team Playmaker Option records before zone filter: {len(playmaker_option_events(events, team_name))}.")


def show_tackling(events: pd.DataFrame, team_name: str) -> None:
    st.header("Tackling")
    st.caption("`Tackle` outcome rows and explicit `Missed Tackle` action rows remain separate event types throughout.")
    cards = tackle_summary_cards(events, team_name)
    metric_columns = st.columns(4)
    metric_columns[0].metric("Tackle action records", cards["total"])
    metric_columns[1].metric("Most common Tackle outcome", str(cards["common_outcome"]))
    metric_columns[2].metric("Missed inside Tackle outcomes", cards["missed_tackle_outcomes"])
    metric_columns[3].metric("Explicit Missed Tackle actions", cards["explicit_missed_actions"])

    outcomes = tackle_outcome_distribution(events, team_name)
    left, right = st.columns(2)
    with left:
        st.subheader("Tackle outcomes")
        st.plotly_chart(
            count_bar_chart(outcomes, "tackle_outcome", "Source Tackle outcomes", horizontal=True),
            width="stretch",
        )
        display_summary_table(
            outcomes,
            {"tackle_outcome": "Source outcome", "count": "Count", "percentage": "Percentage"},
        )
    with right:
        st.subheader("Explicit Missed Tackle records by source tackler")
        st.caption("This table names the player on the Missed Tackle row, not the linked evading ball carrier.")
        display_summary_table(
            missed_tackle_player_positions(events, team_name),
            {
                "player_name": "Source-recorded tackler",
                "player_position_name": "Source position",
                "count": "Records",
                "percentage": "Percentage",
            },
        )

    raw_matrix = player_tackle_outcome_matrix(events, team_name)
    st.subheader("Player Tackle Outcome Matrix")
    st.caption("Each outcome column is a source `ActionResultName` observed in the selected team's `Tackle` rows.")
    if raw_matrix.empty:
        st.info("No source Tackle records are available for this selection.")
    else:
        sort_column = st.selectbox(
            "Sort player tackle outcome matrix by",
            list(raw_matrix.columns[1:]),
            key="tackle_outcome_matrix_sort",
        )
        matrix = player_tackle_outcome_matrix(events, team_name, sort_by=sort_column)
        display_summary_table(matrix, {"player_name": "Player", "total_tackle_actions": "Total Tackle Actions"})

    lower_left, lower_right = st.columns(2)
    with lower_left:
        st.subheader("First-tackler outcomes")
        st.caption("Only Tackle rows with `qualifier5Name = 1st Tackler`.")
        display_summary_table(
            first_tackler_outcomes(events, team_name),
            {"tackle_outcome": "Source outcome", "count": "Count", "percentage": "Percentage"},
        )
        st.subheader("First-tackler missed outcomes by player")
        display_summary_table(
            first_tackler_missed_by_player(events, team_name),
            {"player_name": "Player", "count": "Missed outcome rows", "percentage": "Percentage"},
        )
        st.subheader("Most Evaded Tackles")
        st.caption(
            "Uses explicit Missed Tackle rows: `playerName` is the recorded tackler and the linked "
            "`assoc_playerName` is the opposing ball carrier on the associated Carry event."
        )
        display_summary_table(
            evaded_tackles_by_associated_player(events, team_name),
            {"associated_player_name": "Source-linked evading player", "evaded_tackles": "Evaded Tackles"},
        )
    with lower_right:
        st.subheader("Tackle height")
        st.caption("Only populated `qualifier6Name` source labels are shown.")
        display_summary_table(
            tackle_height_distribution(events, team_name),
            {"tackle_height": "Source height label", "count": "Count", "percentage": "Percentage"},
        )
        st.subheader("Source qualifier: Dominant Tackle")
        st.caption("Only `qualifier4Name = Dominant Tackle`; no inferred dominance rule is used.")
        display_summary_table(
            dominant_tackle_outcome_matrix(events, team_name),
            {"player_name": "Player", "dominant_tackle_records": "Dominant Tackle records"},
        )

    st.subheader("Tackle locations")
    locations = tackle_locations(events, team_name)
    st.plotly_chart(
        plot_event_locations(locations, f"Tackle start locations: {team_name}", "action_result_name"),
        width="stretch",
    )
    show_coordinate_note(locations)


def _fixture_count(events: pd.DataFrame) -> int:
    """Count source fixture IDs for ingestion feedback without inventing matches."""

    if events.empty or "fixture_id" not in events.columns:
        return 0
    return int(events["fixture_id"].dropna().nunique())


def _show_load_feedback(
    selected_count: int,
    loaded_files: tuple,
    events: pd.DataFrame,
    issues: tuple = (),
    duplicate_files: tuple[str, ...] = (),
) -> None:
    """Keep all upload outcome details visible without interrupting a valid batch."""

    st.sidebar.caption(
        f"Selected: {selected_count} | Loaded: {len(loaded_files)} | "
        f"Fixtures: {_fixture_count(events)} | Event rows: {len(events)}"
    )
    for issue in issues:
        st.sidebar.error(f"{issue.source_file_name}: {issue.message}")
    if duplicate_files:
        st.sidebar.warning(
            "Skipped duplicate upload(s), matched by filename and size: "
            + ", ".join(duplicate_files)
        )
    for loaded_file in loaded_files:
        for message in loaded_file.validation.user_messages():
            st.sidebar.warning(f"{loaded_file.source_file_name}: {message}")


def main() -> None:
    st.set_page_config(page_title="Queensland Reds | Opposition Preview", page_icon="R", layout="wide")
    apply_theme()
    st.title("Queensland Reds | Opposition Analysis")
    st.caption("Week 11 Capstone prototype | Partner event data")
    st.sidebar.header("Partner event data")
    upload_mode = st.sidebar.radio(
        "Upload selection",
        ("Files", "Folder"),
        horizontal=True,
        help="Choose one or more event files, or a folder of files.",
    )
    if upload_mode == "Files":
        uploaded_files = st.sidebar.file_uploader(
            "Upload authorised XLSX or CSV event files",
            type=["xlsx", "csv"],
            accept_multiple_files=True,
            key="partner_event_files",
            help="Select one or more fixtures. Files are read in memory and are not copied to data/raw/.",
        )
    else:
        uploaded_files = st.sidebar.file_uploader(
            "Upload a folder of authorised XLSX or CSV event files",
            type=["xlsx", "csv"],
            accept_multiple_files="directory",
            key="partner_event_folder",
            help="Choose a folder of files. They are read in memory.",
        )

    with st.sidebar.expander("Advanced / Development input", expanded=False):
        source_path = st.text_input(
            "Local XLSX or CSV event-file path",
            value=os.environ.get("PARTNER_DATA_PATH", ""),
            help=(
                "Development fallback. PARTNER_DATA_PATH can prefill this field; uploaded files take priority."
            ),
        ).strip()
    st.sidebar.caption("Uploaded files take priority over the development path.")

    selected_uploads = uploaded_files or []
    if selected_uploads:
        file_payloads = tuple((upload.name, upload.getvalue()) for upload in selected_uploads)
        try:
            batch = load_uploaded_batch_cached(file_payloads)
        except Exception:  # Keep a malformed browser selection from exposing a traceback in the UI.
            st.error("The selected uploads could not be processed. Please choose valid XLSX or CSV event files.")
            st.stop()
        combined_events = batch.events
        _show_load_feedback(
            len(selected_uploads),
            batch.loaded_files,
            combined_events,
            batch.issues,
            batch.duplicate_files,
        )
        if not batch.loaded_files:
            st.error("No valid partner event file was loaded. Review the file messages in the sidebar and try again.")
            st.stop()
        loaded_names = [loaded_file.source_file_name for loaded_file in batch.loaded_files]
        source_name = ", ".join(loaded_names[:3])
        if len(loaded_names) > 3:
            source_name += f" and {len(loaded_names) - 3} more"
    elif source_path:
        try:
            loaded = load_cached_data(source_path)
        except (FileNotFoundError, OSError, TypeError, ValueError) as error:
            st.error(str(error))
            st.stop()
        combined_events = loaded.events
        _show_load_feedback(1, (loaded,), combined_events)
        source_name = loaded.source_file_name
    else:
        st.info(
            "Upload one or more authorised partner XLSX or CSV event files from the sidebar to begin. "
            "Nothing is loaded by default."
        )
        st.caption(
            "Use Files for multi-file upload, Folder for a supported directory upload, or the advanced "
            "development path when working locally."
        )
        st.stop()

    fixture_events = selected_fixture(combined_events)
    teams = unique_non_null(fixture_events["team_name"])
    if not teams:
        st.error("The selected fixture does not contain usable teamName values.")
        st.stop()
    analysis_team = st.sidebar.selectbox("Team to analyse", teams)
    page = st.sidebar.radio("Analysis section", PAGES)
    if page == "Overview":
        show_overview(fixture_events, analysis_team, source_name)
    elif page == "Key Insights":
        show_key_insights(fixture_events, analysis_team)
    elif page == "Game Intervals":
        show_game_intervals(fixture_events, analysis_team)
    elif page == "Event Replay":
        show_event_replay(fixture_events, analysis_team)
    elif page == "Kicking":
        show_kicking(fixture_events, analysis_team)
    elif page == "Linebreaks":
        show_linebreaks(fixture_events, analysis_team)
    elif page == "Breakdown Choices":
        show_breakdown(fixture_events, analysis_team)
    else:
        show_tackling(fixture_events, analysis_team)
    st.divider()
    st.caption("See the project documentation for field mappings, coverage, and current limitations.")


if __name__ == "__main__":
    main()
