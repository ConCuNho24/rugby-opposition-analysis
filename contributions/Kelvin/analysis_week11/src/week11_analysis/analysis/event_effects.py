"""Classify recorded partner events into source-faithful replay effects.

The partner feed records individual event observations, not continuous player
tracking.  This module therefore describes the visual treatment of one source
event at a time.  A source path is available only when an event is both
semantically a movement event and contains a credible, distinct endpoint.
In particular, the feed's common ``(0, 0)`` end-coordinate placeholder is not
treated as motion.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from typing import Any

import pandas as pd


BALL_TRAVEL = "ball_travel"
PLAYER_ADVANCE = "player_advance"
CONTACT = "contact"
EVASION = "evasion"
BREAKDOWN = "breakdown"
DECISION = "decision"
BREAKTHROUGH = "breakthrough"
POSSESSION_CHANGE = "possession_change"
SET_PIECE = "set_piece"
SCORING = "scoring"
STOPPAGE = "stoppage"
RECEIPT = "receipt"
OUT_OF_PLAY = "out_of_play"
ADMIN = "admin"
TERRITORY_TRANSITION = "territory_transition"
DEFENSIVE_EVENT = "defensive_event"
PHASE = "phase"
ATTACKING_QUALITY = "attacking_quality"
NEUTRAL = "neutral"


@dataclass(frozen=True)
class EventEffectProfile:
    """A renderer-neutral description of one recorded event's visual cue.

    ``uses_recorded_path`` and ``allows_local_interpolation`` are true only
    for a source-local start/end movement that is safe to depict.  They never
    authorise a renderer to link one source event to the next.
    """

    effect_family: str
    variant: str
    visual_label: str
    marker_style: str
    marker_symbol: str
    path_style: str
    motion_style: str
    impact_style: str
    pulse_style: str
    endpoint_emphasis: str
    secondary_cue: str | None
    has_recorded_location: bool
    has_recorded_end_location: bool
    uses_recorded_path: bool
    allows_local_interpolation: bool
    show_associated_player: bool
    coverage_status: str


@dataclass(frozen=True)
class _EffectStyle:
    marker_style: str
    marker_symbol: str
    path_style: str
    motion_style: str
    impact_style: str
    pulse_style: str
    endpoint_emphasis: str


@dataclass(frozen=True)
class _EventTerms:
    action: str | None
    action_type: str | None
    result: str | None
    qualifiers: tuple[str, ...]

    @property
    def combined(self) -> str:
        return " ".join(
            value.casefold()
            for value in (self.action, self.action_type, self.result, *self.qualifiers)
            if value
        )


_FAMILY_STYLES: dict[str, _EffectStyle] = {
    BALL_TRAVEL: _EffectStyle("ball", "ball", "arrow", "ball", "none", "none", "arrival"),
    PLAYER_ADVANCE: _EffectStyle(
        "player", "player", "arrow", "player", "none", "none", "arrival"
    ),
    CONTACT: _EffectStyle("impact", "impact", "none", "none", "solid", "impact", "none"),
    EVASION: _EffectStyle("evasion", "open", "dashed", "evasion_cue", "broken", "evasion", "none"),
    BREAKDOWN: _EffectStyle("breakdown", "cluster", "none", "none", "cluster", "cluster", "none"),
    DECISION: _EffectStyle("decision", "decision", "dashed", "none", "none", "decision", "none"),
    BREAKTHROUGH: _EffectStyle("breakthrough", "burst", "arrow", "player", "none", "breakthrough", "arrival"),
    POSSESSION_CHANGE: _EffectStyle(
        "possession", "swap", "none", "none", "possession_change", "possession", "none"
    ),
    SET_PIECE: _EffectStyle("set_piece", "set", "none", "none", "set_piece", "set_piece", "none"),
    SCORING: _EffectStyle("score", "star", "none", "none", "score", "score", "score"),
    STOPPAGE: _EffectStyle("stoppage", "warning", "none", "none", "warning", "warning", "none"),
    RECEIPT: _EffectStyle("receipt", "catch", "none", "none", "receipt", "receipt", "arrival"),
    OUT_OF_PLAY: _EffectStyle("boundary", "boundary", "none", "none", "boundary", "fade", "boundary"),
    ADMIN: _EffectStyle("admin", "badge", "none", "none", "none", "none", "none"),
    TERRITORY_TRANSITION: _EffectStyle(
        "territory", "entry", "arrow", "burst", "none", "territory", "arrival"
    ),
    DEFENSIVE_EVENT: _EffectStyle(
        "defence", "shield", "none", "none", "defence", "defence", "none"
    ),
    PHASE: _EffectStyle("phase", "phase", "none", "none", "phase", "phase", "none"),
    ATTACKING_QUALITY: _EffectStyle(
        "attack", "attack", "none", "none", "attack", "attack", "none"
    ),
    NEUTRAL: _EffectStyle("neutral", "circle", "none", "none", "none", "neutral", "none"),
}

_FIELD_ALIASES = {
    "action_id": ("action_id", "action"),
    "action": ("action_name", "actionName"),
    "action_type": ("action_type_name", "ActionTypeName"),
    "result": ("action_result_name", "ActionResultName"),
    "associated_player": ("associated_player_name", "assoc_playerName"),
}
_QUALIFIER_ALIASES = tuple(
    (f"qualifier_{number}_name", f"qualifier{number}Name") for number in range(3, 11)
)
_COORDINATE_ALIASES = {
    "x": ("x", "x_coord"),
    "y": ("y", "y_coord"),
    "x_end": ("x_end", "x_coord_end"),
    "y_end": ("y_end", "y_coord_end"),
}
_BREAKDOWN_ACTIONS = frozenset({"ruck", "ruck ooa", "maul"})
_ADMIN_ACTIONS = frozenset({"sub in", "sub out", "ref review", "period"})
_SET_PIECE_ACTIONS = frozenset({"lineout throw", "lineout take", "scrum"})
_BALL_TRAVEL_ACTIONS = frozenset({"kick", "pass", "restart"})
_CARRY_ACTIONS = frozenset({"carry", "counter attack"})


def _optional_text(value: object) -> str | None:
    """Return a trimmed scalar text value while preserving missing values."""

    if value is None:
        return None
    try:
        if bool(pd.isna(value)):
            return None
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return text or None


def _first_text(event: Mapping[str, object], aliases: tuple[str, ...]) -> str | None:
    for alias in aliases:
        value = _optional_text(event.get(alias))
        if value is not None:
            return value
    return None


def source_qualifiers(event: Mapping[str, object]) -> tuple[str, ...]:
    """Return unique partner qualifier labels from canonical or raw columns.

    The current transformation exposes qualifier 3--10 when present.  Raw
    partner rows are supported too, making the classifier useful during data
    profiling without relying on a Streamlit-specific representation.
    """

    qualifiers: list[str] = []
    for aliases in _QUALIFIER_ALIASES:
        value = _first_text(event, aliases)
        if value is not None and value not in qualifiers:
            qualifiers.append(value)
    return tuple(qualifiers)


def _event_terms(event: Mapping[str, object]) -> _EventTerms:
    return _EventTerms(
        action=_first_text(event, _FIELD_ALIASES["action"]),
        action_type=_first_text(event, _FIELD_ALIASES["action_type"]),
        result=_first_text(event, _FIELD_ALIASES["result"]),
        qualifiers=source_qualifiers(event),
    )


def _normalise(value: str | None) -> str:
    return value.casefold() if value else ""


def _contains(terms: _EventTerms, *needles: str) -> bool:
    combined = terms.combined
    return any(needle.casefold() in combined for needle in needles)


def _coordinate_value(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        if bool(pd.isna(value)):
            return None
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if isfinite(numeric) else None


def _first_coordinate(event: Mapping[str, object], aliases: tuple[str, ...]) -> float | None:
    for alias in aliases:
        coordinate = _coordinate_value(event.get(alias))
        if coordinate is not None:
            return coordinate
    return None


def _coordinates(event: Mapping[str, object], x_column: str, y_column: str) -> tuple[float, float] | None:
    x = _first_coordinate(event, _COORDINATE_ALIASES.get(x_column, (x_column,)))
    y = _first_coordinate(event, _COORDINATE_ALIASES.get(y_column, (y_column,)))
    if x is None or y is None:
        return None
    return (x, y)


def has_credible_motion_path(event: Mapping[str, object]) -> bool:
    """Whether one event has a conservative, source-local movement path.

    A finite endpoint by itself is not enough: Partner summary events commonly
    contain ``(0, 0)`` even when they are stationary.  A caller must still use
    this only for an effect family that represents recorded movement.
    """

    start = _coordinates(event, "x", "y")
    end = _coordinates(event, "x_end", "y_end")
    return start is not None and end is not None and end != (0.0, 0.0) and end != start


def _associated_player_available(event: Mapping[str, object]) -> bool:
    return _first_text(event, _FIELD_ALIASES["associated_player"]) is not None


def _profile(
    event: Mapping[str, object],
    family: str,
    variant: str,
    visual_label: str,
    *,
    allow_source_path: bool = False,
    marker_style: str | None = None,
    marker_symbol: str | None = None,
    path_style: str | None = None,
    motion_style: str | None = None,
    impact_style: str | None = None,
    pulse_style: str | None = None,
    endpoint_emphasis: str | None = None,
    secondary_cue: str | None = None,
    show_associated_player: bool = False,
) -> EventEffectProfile:
    """Build a profile and gate all depicted movement on source evidence."""

    style = _FAMILY_STYLES[family]
    start = _coordinates(event, "x", "y")
    end = _coordinates(event, "x_end", "y_end")
    uses_path = allow_source_path and has_credible_motion_path(event)
    applied_motion_style = motion_style if motion_style is not None else style.motion_style
    configured_path_style = path_style if path_style is not None else style.path_style
    return EventEffectProfile(
        effect_family=family,
        variant=variant,
        visual_label=visual_label,
        marker_style=marker_style if marker_style is not None else style.marker_style,
        marker_symbol=marker_symbol if marker_symbol is not None else style.marker_symbol,
        # A renderer can safely honour this field directly: an unavailable or
        # semantically unsupported path is never styled as a drawable route.
        path_style=configured_path_style if uses_path else "none",
        motion_style=applied_motion_style,
        impact_style=impact_style if impact_style is not None else style.impact_style,
        pulse_style=pulse_style if pulse_style is not None else style.pulse_style,
        endpoint_emphasis=(
            endpoint_emphasis if endpoint_emphasis is not None else style.endpoint_emphasis
        ),
        secondary_cue=secondary_cue,
        has_recorded_location=start is not None,
        has_recorded_end_location=end is not None,
        uses_recorded_path=uses_path,
        allows_local_interpolation=uses_path and applied_motion_style in {"ball", "player", "burst"},
        show_associated_player=show_associated_player and _associated_player_available(event),
        coverage_status="fallback" if family == NEUTRAL else "covered",
    )


def _kick_variant(terms: _EventTerms) -> tuple[str, str, str]:
    if _contains(terms, "touch", "out of play", "in touch"):
        return ("touch_kick", "Kick to touch", "boundary")
    if _contains(terms, "bomb"):
        return ("bomb", "Bomb kick", "arrival")
    if _contains(terms, "box"):
        return ("box_kick", "Box kick", "arrival")
    if _contains(terms, "chip"):
        return ("chip", "Chip kick", "arrival")
    if _contains(terms, "penalty kick"):
        return ("penalty_kick", "Penalty kick", "arrival")
    return ("kick", "Kick travel", "arrival")


def _tackle_profile(event: Mapping[str, object], terms: _EventTerms) -> EventEffectProfile:
    if _contains(terms, "missed"):
        return _missed_tackle_profile(event, terms)
    if _contains(terms, "turnover"):
        return _profile(
            event,
            CONTACT,
            "turnover_won",
            "Tackle impact — turnover won",
            impact_style="possession_change",
            pulse_style="impact",
            secondary_cue="possession_change",
        )
    if _contains(terms, "dominant"):
        return _profile(
            event, CONTACT, "dominant", "Tackle impact — dominant", impact_style="strong"
        )
    if _contains(terms, "passive", "ineffective"):
        return _profile(
            event, CONTACT, "passive", "Tackle impact — passive", impact_style="soft"
        )
    if _contains(terms, "sack"):
        return _profile(event, CONTACT, "sack", "Tackle impact — sack")
    if _contains(terms, "forced in touch"):
        return _profile(
            event,
            CONTACT,
            "forced_in_touch",
            "Tackle impact — forced in touch",
            endpoint_emphasis="boundary",
            secondary_cue="out_of_play",
        )
    if _contains(terms, "try saver"):
        return _profile(event, CONTACT, "try_saver", "Tackle impact — try saver")
    return _profile(event, CONTACT, "complete", "Tackle impact — complete")


def _missed_tackle_profile(event: Mapping[str, object], terms: _EventTerms) -> EventEffectProfile:
    if _contains(terms, "stepped"):
        variant, label = "stepped", "Missed tackle — stepped"
    elif _contains(terms, "bumped off"):
        variant, label = "bumped_off", "Missed tackle — bumped off"
    elif _contains(terms, "outpaced"):
        variant, label = "outpaced", "Missed tackle — outpaced"
    elif _contains(terms, "positional"):
        variant, label = "positional", "Missed tackle — positional"
    else:
        variant, label = "missed", "Missed tackle — evasion"
    return _profile(
        event,
        EVASION,
        variant,
        label,
        show_associated_player=True,
    )


def _breakdown_profile(event: Mapping[str, object], terms: _EventTerms) -> EventEffectProfile:
    if _contains(terms, "cleaned out"):
        variant, label = "cleaned_out", "Breakdown — cleaned out"
    elif _contains(terms, "failed clearout"):
        variant, label = "failed_clearout", "Breakdown — failed clearout"
    elif _contains(terms, "secured", "won outright"):
        variant, label = "secured", "Breakdown — secured"
    elif _contains(terms, "jackal", "ball steal", "turnover"):
        variant, label = "turnover", "Breakdown — turnover"
    elif _contains(terms, "maul"):
        variant, label = "maul", "Maul breakdown"
    else:
        variant, label = "breakdown", "Breakdown event"
    is_turnover = _contains(terms, "jackal", "ball steal", "turnover")
    return _profile(
        event,
        BREAKDOWN,
        variant,
        label,
        impact_style="contested" if is_turnover or variant == "failed_clearout" else None,
        secondary_cue="possession_change" if is_turnover else None,
    )


def _playmaker_profile(event: Mapping[str, object], terms: _EventTerms) -> EventEffectProfile:
    if _contains(terms, "playmaker option - pass"):
        return _profile(
            event,
            DECISION,
            "pass",
            "Playmaker decision — pass",
            marker_symbol="pass",
            motion_style="ball",
            path_style="dashed_arrow",
        )
    if _contains(terms, "playmaker option - carry"):
        return _profile(
            event,
            DECISION,
            "carry",
            "Playmaker decision — carry",
            marker_symbol="carry",
            motion_style="player",
            path_style="dashed_arrow",
        )
    if _contains(terms, "playmaker option - kick"):
        return _profile(
            event,
            DECISION,
            "kick",
            "Playmaker decision — kick",
            marker_symbol="kick",
            motion_style="ball",
            path_style="dashed_arrow",
        )
    return _profile(event, DECISION, "recorded_option", "Playmaker decision")


def _scoring_profile(event: Mapping[str, object], terms: _EventTerms) -> EventEffectProfile:
    action = _normalise(terms.action)
    if action == "goal kick":
        if _contains(terms, "goal kicked", "success"):
            variant, label, emphasis = "goal_made", "Goal kick — made", "score"
        elif _contains(terms, "goal missed", "fail"):
            variant, label, emphasis = "goal_missed", "Goal kick — missed", "faded"
        else:
            variant, label, emphasis = "goal_attempt", "Goal kick attempt", "score"
        return _profile(
            event,
            SCORING,
            variant,
            label,
            allow_source_path=True,
            marker_symbol="goal",
            path_style="arrow",
            motion_style="ball",
            endpoint_emphasis=emphasis,
        )
    if _contains(terms, "try"):
        return _profile(event, SCORING, "try", "Try scoring event")
    return _profile(event, SCORING, "score", "Scoring event")


def _has_scoring_result(terms: _EventTerms) -> bool:
    """Recognise an explicit scoring result without mistaking a try assist for a try."""

    result = _normalise(terms.result)
    return "try" in result or "goal kicked" in result or "goal missed" in result


def _collection_profile(event: Mapping[str, object], terms: _EventTerms) -> EventEffectProfile:
    if _contains(terms, "contested"):
        variant, label, impact = "contested", "Contested receipt", "double_ring"
    elif _contains(terms, "clean", "caught", "collected"):
        variant, label, impact = "clean", "Ball receipt", "receipt"
    else:
        variant, label, impact = "collection", "Ball collection", "receipt"
    return _profile(
        event,
        RECEIPT,
        variant,
        label,
        impact_style=impact,
    )


def _defensive_exit_profile(event: Mapping[str, object], terms: _EventTerms) -> EventEffectProfile:
    if _contains(terms, "kicked"):
        return _profile(
            event,
            BALL_TRAVEL,
            "defensive_exit_kick",
            "Defensive exit — kick",
            endpoint_emphasis="boundary" if _contains(terms, "out") else "arrival",
        )
    if _contains(terms, "carried"):
        return _profile(
            event,
            PLAYER_ADVANCE,
            "defensive_exit_carry",
            "Defensive exit — carry",
        )
    return _profile(event, TERRITORY_TRANSITION, "defensive_exit", "Defensive exit")


def _carry_profile(event: Mapping[str, object], terms: _EventTerms) -> EventEffectProfile:
    action = _normalise(terms.action)
    if action == "counter attack":
        variant, label = "counter_attack", "Counter-attack advance"
    elif _contains(terms, "pick and go"):
        variant, label = "pick_and_go", "Carry — pick and go"
    elif _contains(terms, "one out"):
        variant, label = "one_out_drive", "Carry — one-out drive"
    elif _contains(terms, "support carry"):
        variant, label = "support_carry", "Carry — support"
    else:
        variant, label = "carry", "Player advance"
    return _profile(
        event,
        PLAYER_ADVANCE,
        variant,
        label,
        allow_source_path=action == "carry",
    )


def _set_piece_profile(event: Mapping[str, object], terms: _EventTerms) -> EventEffectProfile:
    action = _normalise(terms.action)
    if action == "scrum":
        return _profile(event, SET_PIECE, "scrum", "Scrum set piece")
    if action == "lineout throw":
        return _profile(event, SET_PIECE, "lineout_throw", "Lineout throw")
    if action == "lineout take":
        return _profile(event, SET_PIECE, "lineout_take", "Lineout take")
    return _profile(event, SET_PIECE, "set_piece", "Set piece")


def _out_of_play_profile(event: Mapping[str, object], terms: _EventTerms) -> EventEffectProfile:
    if _contains(terms, "forced in touch"):
        variant, label = "forced_in_touch", "Forced in touch"
    elif _contains(terms, "carried in touch", "carried over"):
        variant, label = "carried_in_touch", "Carried out of play"
    else:
        variant, label = "out_of_play", "Out of play"
    return _profile(event, OUT_OF_PLAY, variant, label)


def _defensive_action_profile(event: Mapping[str, object], terms: _EventTerms) -> EventEffectProfile:
    if _contains(terms, "tackle arrival"):
        return _profile(event, CONTACT, "tackle_arrival", "Defensive tackle arrival")
    if _contains(terms, "aerial kick contest"):
        return _profile(
            event,
            RECEIPT,
            "aerial_contest",
            "Contested aerial receipt",
            impact_style="double_ring",
        )
    if _contains(terms, "ball steal maul"):
        return _profile(
            event,
            BREAKDOWN,
            "ball_steal",
            "Breakdown — ball steal",
            impact_style="contested",
            secondary_cue="possession_change",
        )
    return _profile(event, DEFENSIVE_EVENT, "defensive_action", "Defensive action")


def _missing_action_profile(event: Mapping[str, object], terms: _EventTerms) -> EventEffectProfile | None:
    """Use only explicit source type labels when the action label is absent."""

    if _contains(terms, "scrum half pass"):
        return _profile(event, SET_PIECE, "scrum_half_pass", "Scrum-half set-piece context")
    if _contains(terms, "no 8 pick up"):
        return _profile(event, SET_PIECE, "number_8_pickup", "No. 8 set-piece pickup")
    source_action_id = _first_text(event, _FIELD_ALIASES["action_id"])
    if source_action_id in {"28", "28.0", "29", "29.0"}:
        return _profile(event, SET_PIECE, "unlabelled_set_piece", "Set-piece outcome")
    return None


def classify_event_effect(event: Mapping[str, object]) -> EventEffectProfile:
    """Return an effect profile for every source event, with a safe fallback.

    The classification favours the concrete event action and then uses action
    type, result, and qualifiers for source-supported variants.  The returned
    profile is deliberately visualisation-agnostic so the Streamlit page and
    pitch renderer do not contain a growing taxonomy of conditional logic.
    """

    terms = _event_terms(event)
    action = _normalise(terms.action)

    if action in _ADMIN_ACTIONS:
        label = {
            "sub in": "Player substitution — in",
            "sub out": "Player substitution — out",
            "ref review": "Referee review",
            "period": "Period event",
        }[action]
        return _profile(event, ADMIN, action.replace(" ", "_"), label)

    if action == "missed tackle":
        return _missed_tackle_profile(event, terms)
    if action == "tackle":
        return _tackle_profile(event, terms)
    if action in _BREAKDOWN_ACTIONS:
        return _breakdown_profile(event, terms)
    if action == "playmaker options":
        return _playmaker_profile(event, terms)

    if _contains(
        terms,
        "initial break",
        "line break",
        "clean break",
        "defender beaten",
        "break assist",
        "supported break",
    ):
        return _profile(
            event,
            BREAKTHROUGH,
            "initial_break",
            "Breakthrough event",
        )

    if action == "try" or action == "goal kick" or _has_scoring_result(terms):
        return _scoring_profile(event, terms)

    if action in _BALL_TRAVEL_ACTIONS:
        if action == "pass":
            return _profile(event, BALL_TRAVEL, "pass", "Pass travel", allow_source_path=True)
        if action == "restart":
            return _profile(event, BALL_TRAVEL, "restart", "Restart launch", allow_source_path=True)
        variant, label, endpoint_emphasis = _kick_variant(terms)
        return _profile(
            event,
            BALL_TRAVEL,
            variant,
            label,
            allow_source_path=True,
            endpoint_emphasis=endpoint_emphasis,
        )

    if action == "defensive exits":
        return _defensive_exit_profile(event, terms)

    if _contains(terms, "out of play", "in touch", "carried in touch", "carried over"):
        return _out_of_play_profile(event, terms)

    if action in _CARRY_ACTIONS:
        return _carry_profile(event, terms)

    if action == "collection":
        return _collection_profile(event, terms)

    if action in _SET_PIECE_ACTIONS:
        return _set_piece_profile(event, terms)

    if action == "defensive action":
        return _defensive_action_profile(event, terms)

    if not action:
        missing_action_profile = _missing_action_profile(event, terms)
        if missing_action_profile is not None:
            return missing_action_profile

    if action == "turnover" or _contains(terms, "turnover", "interception"):
        return _profile(event, POSSESSION_CHANGE, "turnover", "Possession change")

    if action == "penalty conceded" or _contains(
        terms,
        "penalty conceded",
        "pen conceded",
        "free kick",
        "offside",
        "not releasing",
        "not rolling away",
        "dissent",
    ):
        return _profile(event, STOPPAGE, "penalty", "Penalty or stoppage")

    if action == "attacking 22 entry":
        return _profile(
            event,
            TERRITORY_TRANSITION,
            "attacking_22_entry",
            "Attacking 22 entry",
        )
    if action == "possession":
        return _profile(event, PHASE, "possession", "Possession phase")
    if action == "sequences":
        return _profile(event, PHASE, "sequence", "Phase sequence")
    if action == "attacking qualities":
        return _profile(event, ATTACKING_QUALITY, "attacking_quality", "Attacking quality")

    return _profile(event, NEUTRAL, "recorded_event", "Recorded event")


def event_effect_coverage(events: pd.DataFrame) -> pd.DataFrame:
    """Summarise event-effect coverage without exposing replay implementation.

    The table keeps source action/type/result/qualifier context beside the
    assigned family.  It is useful for a development audit and intentionally
    reports missing source labels as ``Not recorded`` rather than leaving an
    ambiguous blank category.
    """

    columns = [
        "action_name",
        "action_type_name",
        "action_result_name",
        "qualifiers",
        "effect_family",
        "variant",
        "coverage_status",
        "record_count",
    ]
    if events.empty:
        return pd.DataFrame(columns=columns)

    rows: list[dict[str, Any]] = []
    for _, event in events.iterrows():
        terms = _event_terms(event)
        profile = classify_event_effect(event)
        rows.append(
            {
                "action_name": terms.action or "Not recorded",
                "action_type_name": terms.action_type or "Not recorded",
                "action_result_name": terms.result or "Not recorded",
                "qualifiers": "; ".join(terms.qualifiers) if terms.qualifiers else "Not recorded",
                "effect_family": profile.effect_family,
                "variant": profile.variant,
                "coverage_status": profile.coverage_status,
            }
        )

    return (
        pd.DataFrame(rows)
        .groupby(columns[:-1], as_index=False, dropna=False)
        .size()
        .rename(columns={"size": "record_count"})
        .loc[:, columns]
        .sort_values(
            ["action_name", "record_count", "action_type_name", "action_result_name"],
            ascending=[True, False, True, True],
            kind="stable",
        )
        .reset_index(drop=True)
    )
