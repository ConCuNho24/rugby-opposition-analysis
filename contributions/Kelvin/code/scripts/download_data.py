"""Reproducibly download and split the selected public Rugby Union dataset.

Selected source: Rugby-Data's public Premiership 2024--25 JSON. The repository
does not declare a licence, so this PoC does not commit or redistribute its raw
data. The source is used with attribution for non-production Capstone research;
obtain permission before any redistribution or commercial use.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rugby_analysis.adapters.rugby_data import SOURCE_REPOSITORY, match_id_from_record  # noqa: E402


SOURCE_COMMIT = "90923144567e1613a3d941ba72a54a10a3866194"
SEASON_FILE = "premiership-2024-2025.json"
SOURCE_URL = f"https://raw.githubusercontent.com/transientlunatic/Rugby-Data/{SOURCE_COMMIT}/json/{SEASON_FILE}"


def fetch_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "rugby-opposition-analysis-poc/0.1"})
    with urlopen(request, timeout=60) as response:  # noqa: S310 - pinned GitHub raw URL
        return response.read()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Rewrite downloaded season and per-match files.")
    args = parser.parse_args()

    raw_root = PROJECT_ROOT / "data" / "raw" / "rugby_data_premiership_2024_2025"
    source_root = raw_root / "source"
    matches_root = raw_root / "matches"
    source_root.mkdir(parents=True, exist_ok=True)
    matches_root.mkdir(parents=True, exist_ok=True)

    raw_payload = fetch_bytes(SOURCE_URL)
    source_path = source_root / SEASON_FILE
    if args.force or not source_path.exists() or source_path.read_bytes() != raw_payload:
        source_path.write_bytes(raw_payload)
        print(f"[INFO] Downloaded pinned season source to {source_path}")
    else:
        print(f"[INFO] Existing pinned season source retained: {source_path}")

    matches = json.loads(raw_payload.decode("utf-8"))
    if not isinstance(matches, list):
        raise ValueError("Expected the source season JSON to be an array of match records.")

    manifest_matches: list[dict[str, object]] = []
    written = 0
    for index, match_record in enumerate(matches):
        match_id = match_id_from_record(match_record)
        serialized = json.dumps(match_record, indent=2, sort_keys=True).encode("utf-8")
        filename = f"{match_id}.json"
        target = matches_root / filename
        if args.force or not target.exists() or target.read_bytes() != serialized:
            target.write_bytes(serialized)
            written += 1
        home = match_record.get("home", {})
        away = match_record.get("away", {})
        manifest_matches.append(
            {
                "match_id": match_id,
                "source_match_index": index,
                "filename": filename,
                "sha256": sha256_bytes(serialized),
                "date": match_record.get("date"),
                "round": match_record.get("round"),
                "home_team": home.get("team"),
                "away_team": away.get("team"),
                "home_final_score": home.get("score"),
                "away_final_score": away.get("score"),
            }
        )

    manifest = {
        "dataset_name": "Rugby-Data Premiership 2024-2025 public JSON",
        "source_repository": SOURCE_REPOSITORY,
        "pinned_commit": SOURCE_COMMIT,
        "source_url": SOURCE_URL,
        "source_file_sha256": sha256_bytes(raw_payload),
        "licence_status": "No explicit repository licence found during research; attribution-only non-production Capstone PoC. Do not redistribute raw data.",
        "downloaded_at_utc": datetime.now(UTC).isoformat(),
        "matches": manifest_matches,
    }
    (raw_root / "source_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[INFO] Source matches available: {len(manifest_matches)}")
    print(f"[INFO] Per-match raw records written/updated: {written}")
    print("[INFO] Each source match is now an independent raw file for incremental processing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
