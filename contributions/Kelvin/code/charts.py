"""Small Plotly chart helpers for the CSV Rugby prototype."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from analysis import friendly_label


TEAM_COLOURS = ["#1565C0", "#D32F2F"]
EVENT_COLOURS = ["#1565C0", "#EF6C00", "#7B1FA2", "#00897B"]
PLOT_BACKGROUND = "#0E1117"
PITCH_BACKGROUND = "#173C2A"
PLOT_TEXT = "#F2F4F8"
PLOT_GRID = "rgba(255,255,255,0.38)"


def create_team_comparison_chart(
    data: pd.DataFrame, metrics: list[str], title: str
) -> go.Figure:
    """Create one grouped chart from team-level source or calculated metrics."""
    available = [metric for metric in metrics if metric in data.columns]
    chart_data = data[["team", *available]].melt(
        id_vars="team", var_name="metric", value_name="value"
    )
    chart_data["metric_label"] = chart_data["metric"].map(friendly_label)
    figure = px.bar(
        chart_data,
        x="metric_label",
        y="value",
        color="team",
        barmode="group",
        title=title,
        labels={"metric_label": "Metric", "value": "Recorded value", "team": "Team"},
        color_discrete_sequence=TEAM_COLOURS,
    )
    figure.update_layout(legend_title_text="Team", xaxis_tickangle=-25)
    return figure


def create_metric_comparison_chart(
    data: pd.DataFrame, metric: str, title: str
) -> go.Figure:
    """Create a simple two-team comparison for one metric."""
    figure = px.bar(
        data,
        x="team",
        y=metric,
        color="team",
        title=title,
        text_auto=True,
        labels={"team": "Team", metric: friendly_label(metric)},
        color_discrete_sequence=TEAM_COLOURS,
    )
    figure.update_layout(showlegend=False)
    return figure


def create_event_comparison_chart(event_counts: pd.DataFrame, title: str) -> go.Figure:
    """Compare exact source event counts while displaying friendly labels."""
    chart_data = event_counts.copy()
    chart_data["event_label"] = chart_data["event_type"].map(friendly_label)
    figure = px.bar(
        chart_data,
        x="event_label",
        y="count",
        color="team",
        barmode="group",
        title=title,
        labels={"event_label": "Event", "count": "Recorded events", "team": "Team"},
        color_discrete_sequence=TEAM_COLOURS,
    )
    figure.update_layout(legend_title_text="Team", xaxis_tickangle=-25)
    return figure


def create_rugby_pitch(title: str = "Recorded event locations") -> go.Figure:
    """Draw a reusable Rugby Union pitch using fixed Plotly shapes.

    The main field is 0-100 by 0-70. The displayed margins include every
    coordinate found in the supplied 10-match dataset without changing it.
    """
    figure = go.Figure()

    # Main playing area.
    figure.add_shape(
        type="rect",
        x0=0,
        y0=0,
        x1=100,
        y1=70,
        fillcolor=PITCH_BACKGROUND,
        line={"color": "#A5D6A7", "width": 3},
        layer="below",
    )

    # Goal lines, 22-metre lines, and halfway line.
    for x_value, dash, width in [
        (0, "solid", 3),
        (22, "dash", 1.5),
        (50, "solid", 2),
        (78, "dash", 1.5),
        (100, "solid", 3),
    ]:
        figure.add_shape(
            type="line",
            x0=x_value,
            y0=0,
            x1=x_value,
            y1=70,
            line={"color": "rgba(255,255,255,0.92)", "width": width, "dash": dash},
            layer="below",
        )

    # Five- and fifteen-metre guides measured from each touchline.
    for y_value in [5, 15, 55, 65]:
        figure.add_shape(
            type="line",
            x0=0,
            y0=y_value,
            x1=100,
            y1=y_value,
            line={"color": PLOT_GRID, "width": 1, "dash": "dot"},
            layer="below",
        )

    annotation_font = {"size": 11, "color": PLOT_TEXT}
    figure.add_annotation(
        x=22, y=72.5, text="22 m", showarrow=False, font=annotation_font
    )
    figure.add_annotation(
        x=50, y=72.5, text="Halfway", showarrow=False, font=annotation_font
    )
    figure.add_annotation(
        x=78, y=72.5, text="22 m", showarrow=False, font=annotation_font
    )

    figure.update_layout(
        title=title,
        height=600,
        margin={"l": 45, "r": 25, "t": 65, "b": 45},
        plot_bgcolor=PLOT_BACKGROUND,
        paper_bgcolor=PLOT_BACKGROUND,
        font={"color": PLOT_TEXT},
        title_font={"color": PLOT_TEXT},
        legend_title_text="Event",
        legend={
            "bgcolor": "rgba(14,17,23,0.82)",
            "bordercolor": "rgba(255,255,255,0.22)",
            "borderwidth": 1,
            "font": {"color": PLOT_TEXT},
        },
    )
    figure.update_xaxes(
        title="Source x coordinate",
        range=[-5, 115],
        fixedrange=True,
        showgrid=False,
        zeroline=False,
        constrain="domain",
        color=PLOT_TEXT,
        linecolor="rgba(255,255,255,0.38)",
        tickcolor="rgba(255,255,255,0.55)",
    )
    figure.update_yaxes(
        title="Source y coordinate",
        range=[-5, 75],
        fixedrange=True,
        showgrid=False,
        zeroline=False,
        scaleanchor="x",
        scaleratio=1,
        color=PLOT_TEXT,
        linecolor="rgba(255,255,255,0.38)",
        tickcolor="rgba(255,255,255,0.55)",
    )
    return figure


def plot_events_on_rugby_pitch(
    events: pd.DataFrame,
    title: str,
    colour_by: str = "event_type",
) -> go.Figure:
    """Place source-provided event coordinates over the reusable pitch."""
    figure = create_rugby_pitch(title)
    if events.empty:
        return figure

    group_column = colour_by if colour_by in events.columns else "event_type"
    grouped = list(events.groupby(group_column, dropna=False, sort=False))
    for index, (group_value, group) in enumerate(grouped):
        display_name = (
            friendly_label(str(group_value))
            if group_column == "event_type"
            else str(group_value)
        )
        hover_values = group[["team", "event_type", "match_clock", "x", "y"]].copy()
        hover_values["team"] = hover_values["team"].fillna("Not provided")
        hover_values["match_clock"] = hover_values["match_clock"].fillna("Not provided")
        figure.add_trace(
            go.Scatter(
                x=group["x"],
                y=group["y"],
                mode="markers",
                name=display_name,
                customdata=hover_values.to_numpy(),
                marker={
                    "size": 10,
                    "opacity": 0.78,
                    "color": EVENT_COLOURS[index % len(EVENT_COLOURS)],
                    "line": {"color": "white", "width": 0.7},
                },
                hovertemplate=(
                    "Team: %{customdata[0]}<br>"
                    "Event type: %{customdata[1]}<br>"
                    "Match clock: %{customdata[2]}<br>"
                    "x: %{customdata[3]}<br>"
                    "y: %{customdata[4]}<extra></extra>"
                ),
            )
        )
    figure.update_layout(showlegend=len(grouped) > 1)
    return figure


def create_scoring_timeline(
    scores: pd.DataFrame, home_team: str, away_team: str
) -> go.Figure:
    """Plot cumulative home and away scores from score_change records."""
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=scores["match_time_minute"],
            y=scores["home_score"],
            mode="lines+markers",
            name=home_team,
            line={"color": TEAM_COLOURS[0], "width": 3},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=scores["match_time_minute"],
            y=scores["away_score"],
            mode="lines+markers",
            name=away_team,
            line={"color": TEAM_COLOURS[1], "width": 3},
        )
    )
    figure.update_layout(
        title="Recorded scoring timeline",
        xaxis_title="Recorded match minute",
        yaxis_title="Score",
        hovermode="x unified",
        legend_title_text="Team",
    )
    return figure


def create_player_leaderboard(
    leaderboard: pd.DataFrame, metric: str, title: str
) -> go.Figure:
    """Create a horizontal bar chart for one selected player metric."""
    chart_data = leaderboard.sort_values(metric, ascending=True)
    figure = px.bar(
        chart_data,
        x=metric,
        y="player_name",
        orientation="h",
        title=title,
        text_auto=True,
        labels={metric: friendly_label(metric), "player_name": "Player"},
        color_discrete_sequence=[TEAM_COLOURS[0]],
    )
    figure.update_layout(showlegend=False, yaxis_title="Player")
    return figure
