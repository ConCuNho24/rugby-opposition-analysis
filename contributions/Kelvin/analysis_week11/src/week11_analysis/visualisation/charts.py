"""Small, source-label-friendly Plotly chart helpers."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


REDS_RED = "#b00020"
NEUTRAL_BLUE = "#1261a0"
PAPER_DARK = "#111820"
TEXT_LIGHT = "#e9f1ed"
GRID_DARK = "#2a3940"


def count_bar_chart(
    summary: pd.DataFrame,
    label_column: str,
    title: str,
    horizontal: bool = False,
) -> go.Figure:
    """Display a count table without implying any unrecorded success measure."""

    if summary.empty:
        figure = go.Figure()
        figure.add_annotation(
            text="No source records are available for this selection.",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
        )
        figure.update_layout(
            title=title, height=340, paper_bgcolor=PAPER_DARK, plot_bgcolor=PAPER_DARK,
            font={"color": TEXT_LIGHT}, title_font={"color": TEXT_LIGHT},
        )
        return figure

    chart_data = summary.sort_values("count", ascending=horizontal, kind="stable")
    if horizontal:
        figure = px.bar(
            chart_data,
            x="count",
            y=label_column,
            orientation="h",
            text="count",
            title=title,
            color_discrete_sequence=[REDS_RED],
        )
    else:
        figure = px.bar(
            chart_data,
            x=label_column,
            y="count",
            text="count",
            title=title,
            color_discrete_sequence=[NEUTRAL_BLUE],
        )
        figure.update_xaxes(tickangle=-25)
    figure.update_layout(
        showlegend=False,
        yaxis_title="Recorded event rows" if not horizontal else None,
        xaxis_title=None if not horizontal else "Recorded event rows",
        paper_bgcolor=PAPER_DARK,
        plot_bgcolor=PAPER_DARK,
        font={"color": TEXT_LIGHT},
        title_font={"color": TEXT_LIGHT},
    )
    figure.update_xaxes(gridcolor=GRID_DARK, zerolinecolor=GRID_DARK, color=TEXT_LIGHT)
    figure.update_yaxes(gridcolor=GRID_DARK, zerolinecolor=GRID_DARK, color=TEXT_LIGHT)
    return figure
