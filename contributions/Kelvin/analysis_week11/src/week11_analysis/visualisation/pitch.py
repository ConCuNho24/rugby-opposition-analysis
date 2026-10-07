"""A reusable Plotly rugby pitch for partner-relative event coordinates."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from week11_analysis.analysis.event_effects import EventEffectProfile, classify_event_effect


PITCH_GREEN = "#123f35"
PITCH_LINE = "rgba(232, 244, 239, 0.82)"
PAPER_DARK = "#111820"
PLOT_DARK = "#111820"
TEXT_LIGHT = "#e9f1ed"
MUTED_TEXT = "#b8c7c0"
ACCENT_COLOURS = ("#ef6351", "#5bc0eb", "#f6bd60", "#a78bfa", "#48ca9a")
EFFECT_COLOURS = {
    "ball_travel": "#f6bd60",
    "player_advance": "#5bc0eb",
    "contact": "#ef6351",
    "evasion": "#a78bfa",
    "breakdown": "#48ca9a",
    "decision": "#7dd3fc",
    "breakthrough": "#fb923c",
    "possession_change": "#2dd4bf",
    "set_piece": "#60a5fa",
    "scoring": "#facc15",
    "stoppage": "#fb923c",
    "receipt": "#38bdf8",
    "out_of_play": "#94a3b8",
    "admin": "#cbd5e1",
    "territory_transition": "#fb7185",
    "defensive_event": "#a3e635",
    "phase": "#94a3b8",
    "attacking_quality": "#f97316",
    "neutral": "#cbd5e1",
}
EFFECT_SYMBOLS = {
    "ball": "circle",
    "player": "diamond",
    "impact": "x",
    "open": "circle-open",
    "cluster": "square",
    "decision": "diamond-open",
    "burst": "triangle-right",
    "swap": "cross",
    "set": "square-open",
    "star": "star",
    "warning": "triangle-up",
    "catch": "circle-dot",
    "boundary": "x",
    "badge": "square-open",
    "entry": "triangle-right",
    "shield": "hexagon",
    "phase": "circle-open",
    "attack": "triangle-up",
    "circle": "circle",
    "pass": "triangle-right",
    "carry": "diamond",
    "kick": "circle",
    "goal": "star",
}


def create_rugby_pitch(title: str) -> go.Figure:
    """Draw the 100-by-70 source coordinate area with standard field markings."""

    figure = go.Figure()
    figure.add_shape(
        type="rect",
        x0=0,
        y0=0,
        x1=100,
        y1=70,
        fillcolor=PITCH_GREEN,
        line={"color": PITCH_LINE, "width": 2},
        layer="below",
    )
    for x_value, dash, width in ((0, "solid", 2), (22, "dash", 1), (50, "solid", 1.5), (78, "dash", 1), (100, "solid", 2)):
        figure.add_shape(
            type="line",
            x0=x_value,
            y0=0,
            x1=x_value,
            y1=70,
            line={"color": PITCH_LINE, "width": width, "dash": dash},
            layer="below",
        )
    for y_value in (5, 15, 55, 65):
        figure.add_shape(
            type="line",
            x0=0,
            y0=y_value,
            x1=100,
            y1=y_value,
            line={"color": "rgba(255,255,255,0.42)", "width": 1, "dash": "dot"},
            layer="below",
        )

    figure.update_layout(
        title={"text": title, "font": {"color": TEXT_LIGHT}},
        height=590,
        margin={"l": 45, "r": 25, "t": 60, "b": 45},
        plot_bgcolor=PLOT_DARK,
        paper_bgcolor=PAPER_DARK,
        font={"color": TEXT_LIGHT},
        legend={"title": "Category", "bgcolor": "rgba(17,24,32,0.90)", "font": {"color": TEXT_LIGHT}},
    )
    figure.update_xaxes(
        title="Relative x: own tryline (0) to opposition tryline (100)",
        range=[-3, 103],
        fixedrange=True,
        showgrid=False,
        zeroline=False,
        color=MUTED_TEXT,
    )
    figure.update_yaxes(
        title="Source y coordinate",
        range=[-3, 73],
        fixedrange=True,
        showgrid=False,
        zeroline=False,
        scaleanchor="x",
        scaleratio=1,
        color=MUTED_TEXT,
    )
    return figure


def plot_event_locations(
    events: pd.DataFrame,
    title: str,
    category_column: str,
) -> go.Figure:
    """Plot source locations by a source label, preserving all recorded values."""

    figure = create_rugby_pitch(title)
    if events.empty:
        figure.add_annotation(
            text="No recorded locations are available for this selection.",
            x=50,
            y=35,
            showarrow=False,
            font={"color": TEXT_LIGHT, "size": 15},
        )
        return figure

    grouping = category_column if category_column in events.columns else "action_name"
    for index, (name, group) in enumerate(events.groupby(grouping, dropna=False, sort=False)):
        display_name = "Not specified" if pd.isna(name) else str(name)
        hover = group.reindex(
            columns=["team_name", "player_name", "action_name", "action_type_name", "action_result_name", "match_clock"]
        ).fillna("Not provided")
        figure.add_trace(
            go.Scatter(
                x=group["x"],
                y=group["y"],
                mode="markers",
                name=display_name,
                marker={
                    "size": 10,
                    "opacity": 0.82,
                    "color": ACCENT_COLOURS[index % len(ACCENT_COLOURS)],
                    "line": {"color": "#f4faf7", "width": 0.8},
                },
                customdata=hover.to_numpy(),
                hovertemplate=(
                    "Team: %{customdata[0]}<br>Player: %{customdata[1]}<br>"
                    "Action: %{customdata[2]}<br>Type: %{customdata[3]}<br>"
                    "Result: %{customdata[4]}<br>Match clock: %{customdata[5]}"
                    "<br>x: %{x}<br>y: %{y}<extra></extra>"
                ),
            )
        )
    figure.update_layout(showlegend=events[grouping].nunique(dropna=False) > 1)
    return figure


def _event_label_value(value: object) -> str | None:
    """Return a compact display value while leaving source values unchanged."""

    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _effect_colour(effect_profile: EventEffectProfile) -> str:
    """Return one muted analytics colour for a semantic effect family."""

    return EFFECT_COLOURS.get(effect_profile.effect_family, EFFECT_COLOURS["neutral"])


def _effect_symbol(effect_profile: EventEffectProfile) -> str:
    """Translate a renderer-neutral symbol into a supported Plotly marker."""

    return EFFECT_SYMBOLS.get(effect_profile.marker_symbol, "circle")


def _add_ring(
    figure: go.Figure,
    x_value: float,
    y_value: float,
    radius: float,
    colour: str,
    *,
    width: float = 1.5,
    dash: str = "solid",
) -> None:
    """Add a stationary analytical ring centred on one recorded coordinate."""

    figure.add_shape(
        type="circle",
        xref="x",
        yref="y",
        x0=x_value - radius,
        y0=y_value - radius,
        x1=x_value + radius,
        y1=y_value + radius,
        line={"color": colour, "width": width, "dash": dash},
        fillcolor="rgba(0, 0, 0, 0)",
        layer="above",
    )


def _add_effect_cue(
    figure: go.Figure,
    x_value: float,
    y_value: float,
    effect_profile: EventEffectProfile,
) -> None:
    """Draw a source-anchored cue without placing unrecorded players or paths."""

    family = effect_profile.effect_family
    colour = _effect_colour(effect_profile)

    if family == "contact":
        radius = {"soft": 2.3, "strong": 4.4, "possession_change": 4.8}.get(
            effect_profile.impact_style, 3.3
        )
        _add_ring(figure, x_value, y_value, radius, colour, width=2.2)
        if effect_profile.impact_style in {"strong", "possession_change"}:
            _add_ring(figure, x_value, y_value, radius * 0.56, "#f4faf7", width=1.1)
    elif family == "evasion":
        if effect_profile.variant == "bumped_off":
            _add_ring(figure, x_value, y_value, 3.8, colour, width=2.2)
            _add_ring(figure, x_value, y_value, 2.0, "#f4faf7", width=1.0)
        elif effect_profile.variant == "outpaced":
            _add_ring(figure, x_value, y_value, 4.7, colour, width=2.0, dash="dash")
        elif effect_profile.variant == "positional":
            _add_ring(figure, x_value, y_value, 2.8, colour, width=1.4, dash="dot")
        else:
            _add_ring(figure, x_value, y_value, 3.6, colour, width=2.0, dash="dash")
        figure.add_annotation(
            x=x_value,
            y=y_value,
            text=f"Evasion: {effect_profile.variant.replace('_', ' ')}",
            showarrow=False,
            yshift=-25,
            font={"color": colour, "size": 11},
        )
    elif family == "breakdown":
        for radius, dash in ((1.6, "solid"), (3.1, "dot"), (4.7, "dot")):
            _add_ring(figure, x_value, y_value, radius, colour, width=1.3, dash=dash)
        if effect_profile.impact_style == "contested":
            _add_ring(figure, x_value, y_value, 5.8, "#f6bd60", width=1.2, dash="dash")
    elif family == "decision":
        _add_ring(figure, x_value, y_value, 2.8, colour, width=1.7, dash="dot")
    elif family == "breakthrough":
        _add_ring(figure, x_value, y_value, 3.8, colour, width=2.0)
        figure.add_annotation(
            x=x_value,
            y=y_value,
            text="Break",
            showarrow=False,
            yshift=-25,
            font={"color": colour, "size": 11},
        )
    elif family == "possession_change":
        _add_ring(figure, x_value, y_value, 4.0, colour, width=2.1)
        _add_ring(figure, x_value, y_value, 2.0, "#f6bd60", width=1.3, dash="dash")
    elif family == "set_piece":
        if effect_profile.variant == "scrum":
            for x0, x1 in ((x_value - 4.0, x_value - 0.7), (x_value + 0.7, x_value + 4.0)):
                figure.add_shape(
                    type="rect",
                    xref="x",
                    yref="y",
                    x0=x0,
                    x1=x1,
                    y0=y_value - 2.0,
                    y1=y_value + 2.0,
                    line={"color": colour, "width": 1.7},
                    fillcolor="rgba(0, 0, 0, 0)",
                    layer="above",
                )
        elif effect_profile.variant in {"lineout_throw", "lineout_take"}:
            figure.add_shape(
                type="line",
                xref="x",
                yref="y",
                x0=x_value,
                x1=x_value,
                y0=y_value - 4.0,
                y1=y_value + 4.0,
                line={"color": colour, "width": 2.4, "dash": "dot"},
                layer="above",
            )
            _add_ring(figure, x_value, y_value, 2.1, "#f4faf7", width=1.0)
        else:
            _add_ring(figure, x_value, y_value, 3.6, colour, width=1.8)
            _add_ring(figure, x_value, y_value, 1.8, "#f4faf7", width=1.0)
    elif family == "scoring":
        _add_ring(figure, x_value, y_value, 4.6, colour, width=2.2)
        _add_ring(figure, x_value, y_value, 2.5, "#f4faf7", width=1.1, dash="dot")
    elif family == "stoppage":
        _add_ring(figure, x_value, y_value, 3.5, colour, width=1.9, dash="dash")
    elif family == "receipt":
        _add_ring(
            figure,
            x_value,
            y_value,
            3.8 if effect_profile.variant == "contested" else 2.7,
            colour,
            width=1.8,
        )
        if effect_profile.variant == "contested":
            _add_ring(figure, x_value, y_value, 2.0, "#f4faf7", width=1.0)
    elif family == "out_of_play":
        _add_ring(figure, x_value, y_value, 3.4, colour, width=1.8, dash="dash")
    elif family == "admin":
        _add_ring(figure, x_value, y_value, 2.5, colour, width=1.4, dash="dot")
    elif family in {"territory_transition", "attacking_quality"}:
        _add_ring(figure, x_value, y_value, 3.2, colour, width=1.7)
    elif family == "defensive_event":
        _add_ring(figure, x_value, y_value, 3.0, colour, width=1.6)
    elif family == "phase":
        _add_ring(figure, x_value, y_value, 2.6, colour, width=1.3, dash="dot")
    elif family == "neutral":
        _add_ring(figure, x_value, y_value, 2.5, colour, width=1.2, dash="dot")

    if effect_profile.secondary_cue == "possession_change":
        _add_ring(figure, x_value, y_value, 5.4, "#2dd4bf", width=1.1, dash="dot")
    elif effect_profile.secondary_cue == "out_of_play":
        _add_ring(figure, x_value, y_value, 5.0, "#94a3b8", width=1.1, dash="dash")


def _add_recorded_route(
    figure: go.Figure,
    recorded_path: pd.DataFrame,
    effect_profile: EventEffectProfile,
    animate_event: bool,
) -> None:
    """Draw one source event's route and optional current-event-only frames."""

    start = recorded_path.iloc[0]
    end = recorded_path.iloc[-1]
    colour = _effect_colour(effect_profile)
    line_dash = "dash" if effect_profile.path_style == "dashed_arrow" else "solid"
    if effect_profile.variant == "bomb":
        line_dash = "dash"
    elif effect_profile.variant == "chip":
        line_dash = "dot"
    figure.add_trace(
        go.Scatter(
            x=recorded_path["x"],
            y=recorded_path["y"],
            mode="lines+markers+text",
            text=["Source start", "Source end"],
            textposition="bottom center",
            name="Recorded source route",
            line={"color": colour, "width": 3.5, "dash": line_dash},
            marker={
                "size": 10,
                "symbol": ["circle", "diamond"],
                "color": colour,
                "line": {"color": "#f4faf7", "width": 1},
            },
            hovertemplate="%{text}<br>x: %{x}<br>y: %{y}<extra></extra>",
        )
    )
    figure.add_annotation(
        x=float(end["x"]),
        y=float(end["y"]),
        ax=float(start["x"]),
        ay=float(start["y"]),
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        text="",
        showarrow=True,
        arrowhead=3,
        arrowsize=1.1,
        arrowwidth=1.7,
        arrowcolor=colour,
    )

    if effect_profile.endpoint_emphasis in {"score", "boundary", "faded"}:
        emphasis_colour = {
            "score": "#facc15",
            "boundary": "#94a3b8",
            "faded": "#94a3b8",
        }[effect_profile.endpoint_emphasis]
        _add_ring(
            figure,
            float(end["x"]),
            float(end["y"]),
            3.5,
            emphasis_colour,
            width=1.2 if effect_profile.endpoint_emphasis == "faded" else 2.0,
            dash="dot" if effect_profile.endpoint_emphasis == "faded" else "solid",
        )

    if not (animate_event and effect_profile.allows_local_interpolation):
        return

    motion_trace_index = len(figure.data)
    motion_symbol = "circle" if effect_profile.motion_style == "ball" else "diamond"
    figure.add_trace(
        go.Scatter(
            x=[float(start["x"])],
            y=[float(start["y"])],
            mode="markers",
            name="Local event motion",
            marker={"size": 13, "symbol": motion_symbol, "color": "#ffffff", "line": {"color": colour, "width": 3}},
            hovertemplate="Local source-event cue only<extra></extra>",
        )
    )
    frame_count = 7
    frames: list[go.Frame] = []
    for step in range(frame_count):
        progress = step / (frame_count - 1)
        x_position = float(start["x"]) + (float(end["x"]) - float(start["x"])) * progress
        y_position = float(start["y"]) + (float(end["y"]) - float(start["y"])) * progress
        frames.append(
            go.Frame(
                name=f"event-motion-{step}",
                traces=[motion_trace_index],
                data=[go.Scatter(x=[x_position], y=[y_position])],
            )
        )
    figure.frames = tuple(frames)
    figure.update_layout(
        updatemenus=[
            {
                "type": "buttons",
                "direction": "left",
                "x": 0.01,
                "y": 1.12,
                "xanchor": "left",
                "yanchor": "top",
                "buttons": [
                    {
                        "label": "Play event movement",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {"duration": 130, "redraw": False},
                                "transition": {"duration": 0},
                                "fromcurrent": True,
                            },
                        ],
                    },
                    {
                        "label": "Pause",
                        "method": "animate",
                        "args": [[None], {"mode": "immediate", "frame": {"duration": 0}, "transition": {"duration": 0}}],
                    },
                ],
            }
        ]
    )


def plot_event_replay(
    current_event: pd.Series,
    recent_events: pd.DataFrame,
    recorded_path: pd.DataFrame | None,
    title: str = "Event Replay: recorded event location",
    effect_profile: EventEffectProfile | None = None,
    show_event_effect: bool = True,
    animate_event: bool = False,
) -> go.Figure:
    """Show one recorded event, its trail, and a source-faithful effect cue.

    The plot never joins separate event rows into a movement path.  It only
    depicts a route or local animation when the current event's semantic
    effect profile permits its own credible source start/end pair.
    """

    effect = effect_profile or classify_event_effect(current_event)
    figure = create_rugby_pitch(f"{title} · {effect.visual_label}")
    trail_locations = recent_events.dropna(subset=["x", "y"]) if not recent_events.empty else recent_events
    if not trail_locations.empty:
        figure.add_trace(
            go.Scatter(
                x=trail_locations["x"],
                y=trail_locations["y"],
                mode="markers",
                name="Recent recorded events",
                marker={
                    "size": 8,
                    "color": "rgba(184, 199, 192, 0.45)",
                    "line": {"color": "rgba(232, 244, 239, 0.55)", "width": 0.5},
                },
                hovertemplate="Earlier recorded event<br>x: %{x}<br>y: %{y}<extra></extra>",
            )
        )

    if (
        show_event_effect
        and effect.uses_recorded_path
        and recorded_path is not None
        and len(recorded_path) >= 2
    ):
        _add_recorded_route(figure, recorded_path, effect, animate_event)

    x_value = current_event.get("x")
    y_value = current_event.get("y")
    if pd.isna(x_value) or pd.isna(y_value):
        figure.add_annotation(
            text=f"{effect.visual_label}<br>No field location recorded for this event.",
            x=50,
            y=35,
            showarrow=False,
            font={"color": TEXT_LIGHT, "size": 15},
        )
        return figure

    player = _event_label_value(current_event.get("player_name"))
    action = _event_label_value(current_event.get("action_name"))
    label = " · ".join(value for value in (player, action) if value) or "Recorded event"
    team = _event_label_value(current_event.get("team_name")) or "Not recorded"
    event_type = _event_label_value(current_event.get("action_type_name")) or "Not recorded"
    result = _event_label_value(current_event.get("action_result_name")) or "Not recorded"
    clock = _event_label_value(current_event.get("match_clock")) or "Not recorded"
    marker_colour = _effect_colour(effect) if show_event_effect else "#ef6351"
    marker_symbol = _effect_symbol(effect) if show_event_effect else "circle"
    if show_event_effect:
        _add_effect_cue(figure, float(x_value), float(y_value), effect)
    figure.add_trace(
        go.Scatter(
            x=[x_value],
            y=[y_value],
            mode="markers+text",
            text=[label],
            textposition="top center",
            name="Current event",
            marker={
                "size": 19,
                "symbol": marker_symbol,
                "color": marker_colour,
                "line": {"color": "#ffffff", "width": 2},
            },
            customdata=[[team, action or "Not recorded", event_type, result, clock, effect.visual_label]],
            hovertemplate=(
                "Team: %{customdata[0]}<br>Action: %{customdata[1]}<br>"
                "Type: %{customdata[2]}<br>Result: %{customdata[3]}<br>"
                "Match clock: %{customdata[4]}<br>Visual effect: %{customdata[5]}"
                "<br>x: %{x}<br>y: %{y}<extra></extra>"
            ),
        )
    )
    figure.update_layout(showlegend=True)
    return figure


def coordinate_diagnostics(events: pd.DataFrame) -> dict[str, object]:
    """Report, without altering, source coordinates used for a plotted subset."""

    usable = events.dropna(subset=["x", "y"]).copy()
    if usable.empty:
        return {"count": 0, "out_of_bounds": 0, "x_range": "Not recorded", "y_range": "Not recorded"}
    within = usable["x"].between(0, 100) & usable["y"].between(0, 70)
    return {
        "count": len(usable),
        "out_of_bounds": int((~within).sum()),
        "x_range": f"{usable['x'].min():g} to {usable['x'].max():g}",
        "y_range": f"{usable['y'].min():g} to {usable['y'].max():g}",
    }


def plot_field_segments(selected_label: str, labels: tuple[str, ...], edges: tuple[float, ...]) -> go.Figure:
    """Show transparent relative-coordinate bands and highlight one selection."""

    figure = go.Figure()
    for index, label in enumerate(labels):
        active = label == selected_label
        figure.add_shape(
            type="rect",
            x0=edges[index], y0=0, x1=edges[index + 1], y1=1,
            fillcolor="#ef6351" if active else "#244f43",
            line={"color": "#f6bd60" if active else "#55746a", "width": 2 if active else 1},
        )
        figure.add_annotation(
            x=(edges[index] + edges[index + 1]) / 2,
            y=0.5,
            text=label.split(":", maxsplit=1)[0],
            showarrow=False,
            font={"color": TEXT_LIGHT, "size": 12},
        )
    figure.update_layout(
        height=105,
        margin={"l": 0, "r": 0, "t": 5, "b": 5},
        paper_bgcolor=PAPER_DARK,
        plot_bgcolor=PAPER_DARK,
        showlegend=False,
    )
    figure.update_xaxes(range=[0, 100], visible=False, fixedrange=True)
    figure.update_yaxes(range=[0, 1], visible=False, fixedrange=True)
    return figure
