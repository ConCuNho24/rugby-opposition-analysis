"""Tests for source-faithful Event Replay effect classification."""

from __future__ import annotations

import pandas as pd
import pytest

from week11_analysis.analysis.event_effects import (
    ADMIN,
    ATTACKING_QUALITY,
    BALL_TRAVEL,
    BREAKDOWN,
    BREAKTHROUGH,
    CONTACT,
    DECISION,
    DEFENSIVE_EVENT,
    EVASION,
    NEUTRAL,
    OUT_OF_PLAY,
    PHASE,
    PLAYER_ADVANCE,
    POSSESSION_CHANGE,
    RECEIPT,
    SCORING,
    SET_PIECE,
    STOPPAGE,
    TERRITORY_TRANSITION,
    classify_event_effect,
    event_effect_coverage,
    has_credible_motion_path,
    source_qualifiers,
)


def event(**overrides: object) -> dict[str, object]:
    """Build one synthetic canonical event without copying partner records."""

    base: dict[str, object] = {
        "action_name": "Kick",
        "action_type_name": None,
        "action_result_name": None,
        "x": 20.0,
        "y": 30.0,
        "x_end": 65.0,
        "y_end": 35.0,
    }
    base.update(overrides)
    return base


@pytest.mark.parametrize(
    ("source_event", "expected_family"),
    [
        (event(action_name="Collection"), RECEIPT),
        (event(action_name="Ruck OOA"), BREAKDOWN),
        (
            event(
                action_name="Playmaker Options",
                action_result_name="Playmaker Option - Pass",
            ),
            DECISION,
        ),
        (event(action_name="Tackle", action_result_name="Complete"), CONTACT),
        (event(action_name="Pass"), BALL_TRAVEL),
        (
            event(action_name=None, action_id=28, action_type_name="Scrum Half Pass"),
            SET_PIECE,
        ),
        (event(action_name="Carry"), PLAYER_ADVANCE),
        (event(action_name="Ruck"), BREAKDOWN),
        (event(action_name="Attacking Qualities", action_type_name="Snake"), ATTACKING_QUALITY),
        (event(action_name="Possession"), PHASE),
        (event(action_name="Sequences"), PHASE),
        (event(action_name="Kick"), BALL_TRAVEL),
        (event(action_name="Defensive Action"), DEFENSIVE_EVENT),
        (event(action_name="Missed Tackle", action_type_name="Stepped"), EVASION),
        (event(action_name="Turnover", action_type_name="Dropped Ball Unforced"), POSSESSION_CHANGE),
        (event(action_name="Lineout Throw"), SET_PIECE),
        (event(action_name="Lineout Take"), SET_PIECE),
        (event(action_name="Defensive Exits"), TERRITORY_TRANSITION),
        (event(action_name="Penalty Conceded"), STOPPAGE),
        (event(action_name="Scrum"), SET_PIECE),
        (event(action_name="Sub Out"), ADMIN),
        (event(action_name="Sub In"), ADMIN),
        (event(action_name="Attacking 22 Entry"), TERRITORY_TRANSITION),
        (event(action_name="Ref Review"), ADMIN),
        (event(action_name="Restart"), BALL_TRAVEL),
        (event(action_name="Period"), ADMIN),
        (event(action_name="Maul"), BREAKDOWN),
        (event(action_name="Counter Attack"), PLAYER_ADVANCE),
        (event(action_name="Try"), SCORING),
        (event(action_name="Goal Kick", action_result_name="Goal Kicked"), SCORING),
    ],
)
def test_current_partner_action_taxonomy_has_an_explicit_effect_family(
    source_event: dict[str, object], expected_family: str
) -> None:
    profile = classify_event_effect(source_event)

    assert profile.effect_family == expected_family
    assert profile.coverage_status == "covered"
    assert profile.visual_label


def test_unknown_or_unlabelled_event_has_a_visible_neutral_fallback() -> None:
    profile = classify_event_effect(event(action_name=None, action_id=17, action_type_name=None))

    assert profile.effect_family == NEUTRAL
    assert profile.coverage_status == "fallback"
    assert profile.marker_style == "neutral"
    assert profile.pulse_style == "neutral"
    assert profile.uses_recorded_path is False


@pytest.mark.parametrize(
    ("source_event", "expected_family"),
    [
        (event(action_name="Kick"), BALL_TRAVEL),
        (event(action_name="Pass"), BALL_TRAVEL),
        (event(action_name="Carry"), PLAYER_ADVANCE),
        (event(action_name="Restart"), BALL_TRAVEL),
        (event(action_name="Goal Kick", action_result_name="Goal Kicked"), SCORING),
    ],
)
def test_only_supported_motion_actions_can_use_a_credible_source_local_path(
    source_event: dict[str, object], expected_family: str
) -> None:
    profile = classify_event_effect(source_event)

    assert has_credible_motion_path(source_event)
    assert profile.effect_family == expected_family
    assert profile.uses_recorded_path is True
    assert profile.allows_local_interpolation is True


@pytest.mark.parametrize(
    "source_event",
    [
        event(
            action_name="Playmaker Options",
            action_result_name="Playmaker Option - Pass",
        ),
        event(action_name="Attacking Qualities", action_type_name="Initial Break"),
        event(action_name="Attacking 22 Entry"),
        event(action_name="Collection"),
        event(action_name="Counter Attack"),
    ],
)
def test_context_and_decision_events_do_not_become_invented_travel(
    source_event: dict[str, object]
) -> None:
    profile = classify_event_effect(source_event)

    assert has_credible_motion_path(source_event)
    assert profile.uses_recorded_path is False
    assert profile.allows_local_interpolation is False
    assert profile.path_style == "none"


def test_default_zero_endpoint_does_not_turn_a_stationary_tackle_into_motion() -> None:
    source_event = event(
        action_name="Tackle",
        action_result_name="Complete",
        x=48.0,
        y=31.0,
        x_end=0.0,
        y_end=0.0,
    )

    profile = classify_event_effect(source_event)

    assert profile.effect_family == CONTACT
    assert profile.has_recorded_end_location is True
    assert has_credible_motion_path(source_event) is False
    assert profile.uses_recorded_path is False
    assert profile.path_style == "none"


def test_tackle_result_and_qualifier_create_distinct_contact_or_evasion_profiles() -> None:
    dominant = classify_event_effect(
        event(
            action_name="Tackle",
            action_result_name="Complete",
            qualifier_4_name="Dominant Tackle",
        )
    )
    missed = classify_event_effect(
        event(action_name="Tackle", action_result_name="Missed", action_type_name="Line")
    )

    assert (dominant.effect_family, dominant.variant, dominant.impact_style) == (
        CONTACT,
        "dominant",
        "strong",
    )
    assert (missed.effect_family, missed.variant) == (EVASION, "missed")


def test_missed_tackle_variants_and_associated_player_use_only_recorded_context() -> None:
    stepped = classify_event_effect(
        event(
            action_name="Missed Tackle",
            action_type_name="Stepped",
            associated_player_name="Recorded attacking player",
            x_end=0.0,
            y_end=0.0,
        )
    )
    outpaced = classify_event_effect(
        event(action_name="Missed Tackle", action_type_name="Outpaced")
    )

    assert (stepped.effect_family, stepped.variant, stepped.show_associated_player) == (
        EVASION,
        "stepped",
        True,
    )
    assert (outpaced.effect_family, outpaced.variant) == (EVASION, "outpaced")
    assert stepped.uses_recorded_path is False


def test_breakdown_decision_breakthrough_scoring_and_boundary_use_source_semantics() -> None:
    ruck = classify_event_effect(
        event(action_name="Ruck OOA", action_type_name="Cleaned Out", x_end=0.0, y_end=0.0)
    )
    playmaker = classify_event_effect(
        event(
            action_name="Playmaker Options",
            action_type_name="First Receiver",
            action_result_name="Playmaker Option - Carry",
            x_end=0.0,
            y_end=0.0,
        )
    )
    initial_break = classify_event_effect(
        event(action_name="Attacking Qualities", action_type_name="Initial Break", x_end=0.0, y_end=0.0)
    )
    try_scored = classify_event_effect(
        event(action_name="Carry", action_result_name="Try Scored", x_end=0.0, y_end=0.0)
    )
    carried_in_touch = classify_event_effect(
        event(action_name="Turnover", action_type_name="Carried in Touch", x_end=0.0, y_end=0.0)
    )

    assert (ruck.effect_family, ruck.variant) == (BREAKDOWN, "cleaned_out")
    assert (playmaker.effect_family, playmaker.variant, playmaker.motion_style) == (
        DECISION,
        "carry",
        "player",
    )
    assert initial_break.effect_family == BREAKTHROUGH
    assert try_scored.effect_family == SCORING
    assert carried_in_touch.effect_family == OUT_OF_PLAY


def test_raw_partner_qualifier_aliases_include_qualifiers_eight_to_ten() -> None:
    raw_event = {
        "action": 11,
        "actionName": "Possession",
        "qualifier8Name": "Initial Break",
        "x_coord": 40.0,
        "y_coord": 20.0,
    }

    # Raw semantic aliases are read for taxonomy profiling; lack of canonical
    # coordinate keys simply prevents visual path rendering.
    profile = classify_event_effect(raw_event)

    assert source_qualifiers(raw_event) == ("Initial Break",)
    assert profile.effect_family == BREAKTHROUGH
    assert profile.has_recorded_location is True
    assert profile.uses_recorded_path is False


def test_raw_partner_coordinate_aliases_can_support_a_source_local_kick_path() -> None:
    raw_kick = {
        "action": 4,
        "actionName": "Kick",
        "x_coord": 25.0,
        "y_coord": 20.0,
        "x_coord_end": 75.0,
        "y_coord_end": 30.0,
    }

    profile = classify_event_effect(raw_kick)

    assert has_credible_motion_path(raw_kick)
    assert profile.uses_recorded_path is True


def test_coverage_audit_has_an_explicit_status_and_preserves_record_counts() -> None:
    events = pd.DataFrame(
        [
            event(action_name="Kick"),
            event(action_name="Kick"),
            event(action_name="Ruck OOA", action_type_name="Cleaned Out", x_end=0.0, y_end=0.0),
            event(action_name=None, action_id=17, x_end=0.0, y_end=0.0),
        ]
    )

    coverage = event_effect_coverage(events)

    assert coverage["record_count"].sum() == len(events)
    assert set(coverage["coverage_status"]) == {"covered", "fallback"}
    assert coverage.loc[coverage["action_name"].eq("Not recorded"), "effect_family"].tolist() == [
        NEUTRAL
    ]
