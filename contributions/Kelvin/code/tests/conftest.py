"""Shared, source-shaped fixtures for the public Rugby-Data adapter tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def public_match_record() -> dict[str, object]:
    """Return a compact record with the fields used by the selected public source."""
    return {
        "date": "2024-09-20",
        "round": "Round 1",
        "round_type": "Regular season",
        "stadium": "Example Ground",
        "attendance": 12000,
        "home": {
            "team": "Alpha RFC",
            "score": 12,
            "scores": [
                {"minute": 5, "type": "Try", "player": "Alice Flyhalf", "value": 5},
                {"minute": 7, "type": "Conversion", "player": "Alice Flyhalf", "value": 2},
                {"minute": 49, "type": "Penalty", "player": "Alice Flyhalf", "value": 3},
                {"minute": 67, "type": "Missed penalty", "player": "Alice Flyhalf", "value": 0},
            ],
            "lineup": {
                "1": {
                    "name": "Alpha Prop",
                    "on": [0],
                    "off": [55],
                    "yellows": [42],
                    "reds": [],
                },
                "16": {
                    "name": "Alpha Replacement",
                    "on": [55],
                    "off": [],
                    "yellows": [],
                    "reds": [],
                },
            },
        },
        "away": {
            "team": "Beta RFC",
            "score": 5,
            "scores": [{"minute": 34, "type": "Try", "player": "Bea Centre", "value": 5}],
            "lineup": {
                "13": {
                    "name": "Bea Centre",
                    "on": [0],
                    "off": [],
                    "yellows": [],
                    "reds": [],
                }
            },
        },
    }


@pytest.fixture
def rugby_raw_root(tmp_path: Path) -> Path:
    """Create a single-match raw directory matching the acquisition layout."""
    raw_root = tmp_path / "data" / "raw" / "rugby_data_premiership_2024_2025" / "matches"
    raw_root.mkdir(parents=True)
    (raw_root / "fixture.json").write_text(json.dumps(public_match_record()), encoding="utf-8")
    return raw_root

