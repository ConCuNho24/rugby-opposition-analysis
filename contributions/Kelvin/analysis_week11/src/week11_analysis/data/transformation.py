"""Transform partner event records into a small, explicit analysis schema.

No attacking-direction inference occurs here.  The partner Q&A states that a
row's x coordinate is already relative to its associated team: 0 is that
team's own tryline and 100 is the opposition tryline.  That convention is
preserved as ``x`` for every team.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


PARTNER_TO_CANONICAL = {
    "ID": "event_id",
    "FXID": "fixture_id",
    "PLID": "player_id",
    "playerName": "player_name",
    "team_id": "team_id",
    "teamName": "team_name",
    "ps_timestamp": "start_seconds",
    "ps_endstamp": "end_seconds",
    "MatchTime": "match_time_raw",
    "period": "period",
    "x_coord": "x",
    "y_coord": "y",
    "x_coord_end": "x_end",
    "y_coord_end": "y_end",
    "action": "action_id",
    "actionName": "action_name",
    "ActionType": "action_type_id",
    "ActionTypeName": "action_type_name",
    "Actionresult": "action_result_id",
    "ActionResultName": "action_result_name",
    "qualifier3Name": "qualifier_3_name",
    "qualifier4Name": "qualifier_4_name",
    "qualifier5Name": "qualifier_5_name",
    "qualifier6Name": "qualifier_6_name",
    "qualifier7Name": "qualifier_7_name",
    "qualifier8Name": "qualifier_8_name",
    "qualifier9Name": "qualifier_9_name",
    "qualifier10Name": "qualifier_10_name",
    "playerpositionName": "player_position_name",
    "homeTeamName": "home_team_name",
    "awayTeamName": "away_team_name",
    "competitionName": "competition_name",
    "season": "season",
    "roundNumber": "round_number",
    "venueName": "venue_name",
    "assoc_player": "associated_player_id",
    "assoc_playerName": "associated_player_name",
    "assoc_playerTeam": "associated_player_team_id",
    "assoc_playerTeamName": "associated_player_team_name",
    "assoc_event_id": "associated_event_id",
}

NUMERIC_COLUMNS = (
    "event_id",
    "fixture_id",
    "player_id",
    "start_seconds",
    "end_seconds",
    "match_time_raw",
    "period",
    "x",
    "y",
    "x_end",
    "y_end",
    "associated_player_id",
    "associated_player_team_id",
    "associated_event_id",
)


def _coerce_text(values: pd.Series) -> pd.Series:
    """Preserve missing values while trimming source labels for reliable grouping."""

    result = values.astype("string").str.strip()
    return result.replace("", pd.NA)


def match_clock_from_mmss(values: pd.Series) -> pd.Series:
    """Render Q&A-defined MatchTime values such as 4328 as ``43:28``.

    The source uses mmss rather than a count of elapsed seconds.  Invalid or
    missing values remain missing instead of being guessed.
    """

    numeric = pd.to_numeric(values, errors="coerce")
    whole = numeric.where(numeric.ge(0)).round().astype("Int64")
    minutes = whole // 100
    seconds = whole % 100
    valid = seconds.lt(60)
    rendered = minutes.astype("string").str.zfill(2) + ":" + seconds.astype("string").str.zfill(2)
    return rendered.where(valid & whole.notna(), pd.NA)


def coordinate_quality(events: pd.DataFrame) -> pd.Series:
    """Flag coordinates in the expected 0-100 by 0-70 playing-area bounds.

    The flag never clamps or changes source values; small out-of-bounds values
    are still retained in the analysis data and can be examined by an analyst.
    """

    return events["x"].between(0, 100, inclusive="both") & events["y"].between(
        0, 70, inclusive="both"
    )


def transform_partner_events(raw_events: pd.DataFrame) -> pd.DataFrame:
    """Create an analysis-ready dataframe from the primary partner schema."""

    renamed = raw_events.rename(columns=PARTNER_TO_CANONICAL).copy()
    for canonical_name in PARTNER_TO_CANONICAL.values():
        if canonical_name not in renamed.columns:
            renamed[canonical_name] = pd.NA

    transformed = renamed.loc[:, list(PARTNER_TO_CANONICAL.values())].copy()
    for column in NUMERIC_COLUMNS:
        transformed[column] = pd.to_numeric(transformed[column], errors="coerce")
    for column in transformed.columns:
        if column not in NUMERIC_COLUMNS:
            transformed[column] = _coerce_text(transformed[column])

    transformed["match_clock"] = match_clock_from_mmss(transformed["match_time_raw"])
    transformed["coordinate_in_playing_area"] = coordinate_quality(transformed)
    transformed["source_order"] = range(len(transformed))
    return transformed.sort_values(
        ["fixture_id", "period", "start_seconds", "source_order"],
        kind="stable",
        na_position="last",
    ).reset_index(drop=True)


def unique_non_null(values: Iterable[object]) -> list[str]:
    """Return a stable, readable list for UI selectors and metadata labels."""

    return sorted({str(value) for value in values if pd.notna(value) and str(value).strip()})


def fixture_summary(events: pd.DataFrame) -> pd.DataFrame:
    """Create one row per fixture for a reusable match-selector control."""

    columns = [
        "fixture_id",
        "home_team_name",
        "away_team_name",
        "competition_name",
        "season",
        "round_number",
        "venue_name",
    ]
    available = [column for column in columns if column in events.columns]
    return events.loc[:, available].drop_duplicates("fixture_id").reset_index(drop=True)


def filter_fixture(events: pd.DataFrame, fixture_id: object) -> pd.DataFrame:
    """Select one fixture without imposing a single-match limitation in code."""

    return events.loc[events["fixture_id"].astype("string") == str(fixture_id)].copy()
