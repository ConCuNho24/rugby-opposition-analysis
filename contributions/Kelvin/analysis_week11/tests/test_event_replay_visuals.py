"""Focused checks for the current-event-only replay renderer."""

from __future__ import annotations

import pandas as pd

from week11_analysis.analysis.event_effects import classify_event_effect
from week11_analysis.analysis.event_replay import event_path
from week11_analysis.visualisation.pitch import plot_event_replay


def replay_event(**overrides: object) -> pd.Series:
    """Return a synthetic event without using private partner rows in tests."""

    values: dict[str, object] = {
        "team_name": "Team A",
        "player_name": "Recorded player",
        "match_clock": "12:34",
        "action_name": "Kick",
        "action_type_name": "Box",
        "action_result_name": "Caught Full",
        "x": 20.0,
        "y": 30.0,
        "x_end": 80.0,
        "y_end": 38.0,
    }
    values.update(overrides)
    return pd.Series(values)


def trace_names(figure) -> list[str]:
    """Expose the renderer's named layers without tying tests to trace order."""

    return [str(trace.name) for trace in figure.data]


def test_kick_uses_its_own_source_route_and_only_current_event_animation() -> None:
    current = replay_event()
    profile = classify_event_effect(current)

    figure = plot_event_replay(
        current,
        pd.DataFrame(),
        event_path(current),
        effect_profile=profile,
        animate_event=True,
    )

    assert profile.uses_recorded_path is True
    assert "Recorded source route" in trace_names(figure)
    assert "Local event motion" in trace_names(figure)
    assert len(figure.frames) == 7
    assert list(figure.frames[0].data[0].x) == [20.0]
    assert list(figure.frames[-1].data[0].x) == [80.0]


def test_stationary_contact_never_draws_default_zero_endpoint_as_a_route() -> None:
    current = replay_event(
        action_name="Tackle",
        action_type_name="Line",
        action_result_name="Complete",
        x=48.0,
        y=31.0,
        x_end=0.0,
        y_end=0.0,
    )
    profile = classify_event_effect(current)

    figure = plot_event_replay(
        current,
        pd.DataFrame(),
        event_path(current),
        effect_profile=profile,
        animate_event=True,
    )

    assert profile.effect_family == "contact"
    assert profile.uses_recorded_path is False
    assert "Recorded source route" not in trace_names(figure)
    assert len(figure.frames) == 0


def test_decision_event_with_endpoints_is_not_rendered_as_completed_travel() -> None:
    current = replay_event(
        action_name="Playmaker Options",
        action_type_name="First Receiver",
        action_result_name="Playmaker Option - Pass",
    )
    profile = classify_event_effect(current)

    figure = plot_event_replay(
        current,
        pd.DataFrame(),
        event_path(current),
        effect_profile=profile,
        animate_event=True,
    )

    assert profile.effect_family == "decision"
    assert profile.uses_recorded_path is False
    assert "Recorded source route" not in trace_names(figure)
    assert len(figure.frames) == 0


def test_event_without_end_coordinates_cannot_create_a_route_or_animation() -> None:
    current = replay_event(x_end=pd.NA, y_end=pd.NA)
    profile = classify_event_effect(current)

    figure = plot_event_replay(
        current,
        pd.DataFrame(),
        event_path(current),
        effect_profile=profile,
        animate_event=True,
    )

    assert event_path(current) is None
    assert profile.uses_recorded_path is False
    assert "Recorded source route" not in trace_names(figure)
    assert len(figure.frames) == 0
