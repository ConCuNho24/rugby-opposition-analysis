"""Profile the selected real public dataset before analysis."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rugby_analysis.adapters.rugby_data import (  # noqa: E402
    RugbyDataJsonAdapter,
    match_id_from_record,
    numeric_value,
)
from rugby_analysis.analysis.event_frequency import available_teams, event_counts  # noqa: E402
from rugby_analysis.core.pipeline import events_to_dataframe  # noqa: E402


def main() -> int:
    raw_root = PROJECT_ROOT / "data" / "raw" / "rugby_data_premiership_2024_2025" / "matches"
    adapter = RugbyDataJsonAdapter(raw_root)
    files = adapter.discover_files(raw_root)
    all_events = []
    raw_match_samples: list[dict[str, object]] = []
    source_score_types: Counter[str] = Counter()
    source_player_count = 0
    source_coordinate_fields_found = False
    matches_without_timeline: list[str] = []
    score_value_mismatches: list[dict[str, object]] = []

    for file_path in files:
        record = json.loads(file_path.read_text(encoding="utf-8"))
        if len(raw_match_samples) < 3:
            raw_match_samples.append(
                {
                    "file": file_path.name,
                    "top_level_fields": sorted(record.keys()),
                    "home_team": record.get("home", {}).get("team"),
                    "away_team": record.get("away", {}).get("team"),
                    "date": record.get("date"),
                }
            )
        for side in ("home", "away"):
            team = record.get(side, {})
            source_player_count += len(team.get("lineup") or {})
            for score in team.get("scores") or []:
                source_score_types[str(score.get("type") or "<missing>")] += 1
                source_coordinate_fields_found = source_coordinate_fields_found or any(
                    field in score for field in ("x", "y", "start_x", "start_y")
                )
            values = [numeric_value(score.get("value")) for score in team.get("scores") or []]
            source_total = sum(value for value in values if value is not None)
            final_score = numeric_value(team.get("score"))
            if final_score is not None and source_total != final_score:
                score_value_mismatches.append(
                    {
                        "match_id": match_id_from_record(record),
                        "team": team.get("team"),
                        "source_score_event_value_total": source_total,
                        "published_final_score": final_score,
                    }
                )
        match_events = adapter.normalize_file(file_path)
        if not match_events:
            matches_without_timeline.append(file_path.stem)
        all_events.extend(match_events)

    normalized = events_to_dataframe(all_events)
    timestamp_range = normalized["timestamp_seconds"].dropna() if not normalized.empty else []
    profile = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "dataset": "Rugby-Data Premiership 2024-2025 public JSON",
        "files_found": len(files),
        "matches_found": len(files),
        "matches_with_event_timeline": len(files) - len(matches_without_timeline),
        "matches_without_event_timeline": matches_without_timeline,
        "normalized_events": len(normalized),
        "normalized_columns": list(normalized.columns),
        "source_match_top_level_fields": ["away", "home", "round", "round_type", "stadium", "date", "attendance"],
        "source_team_fields": ["lineup", "scores", "conference", "score", "team"],
        "source_score_event_fields": ["minute", "type", "player", "value"],
        "source_score_event_types": dict(sorted(source_score_types.items())),
        "score_event_value_reconciliation": {
            "team_timelines_checked": len(files) * 2,
            "team_timelines_with_published_final_score_difference": len(score_value_mismatches),
            "mismatches": score_value_mismatches,
            "interpretation": "Source score-event values and published final scores are kept as separate metrics. "
            "For example, a penalty try may have a source event value of 5 while the published final score "
            "includes an automatic conversion.",
        },
        "canonical_event_types": event_counts(normalized).to_dict(orient="records"),
        "teams": available_teams(normalized),
        "lineup_entries": source_player_count,
        "timestamp_seconds_range": {
            "min": float(timestamp_range.min()) if len(timestamp_range) else None,
            "max": float(timestamp_range.max()) if len(timestamp_range) else None,
            "missing": int(normalized["timestamp_seconds"].isna().sum()) if not normalized.empty else 0,
        },
        "real_field_availability": {
            "match_id_generated_from_source_date_and_teams": True,
            "team_attribution": True,
            "player_for_scoring_and_lineup_events": True,
            "event_minute": True,
            "score_value": True,
            "event_coordinates": source_coordinate_fields_found,
            "possession_or_complete_play_by_play": False,
            "period": False,
            "tackle_carry_line_break_events": False,
        },
        "sample_matches": raw_match_samples,
        "notes": [
            "This is a scoring/lineup timeline, not a full Opta-style event feed.",
            "One published fixture has a final score but no event timeline or lineup records, so it is excluded from event-based rates.",
            "Canonical period remains null because the source provides minute but no explicit period boundary.",
            "No field coordinates were observed; spatial analysis is therefore unsupported.",
        ],
    }
    output_path = PROJECT_ROOT / "outputs" / "data_profile.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    print(f"[INFO] Files found: {len(files)}")
    print(f"[INFO] Normalized event records: {len(normalized)}")
    print(f"[INFO] Teams: {', '.join(profile['teams'])}")
    print(f"[INFO] Profile written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
