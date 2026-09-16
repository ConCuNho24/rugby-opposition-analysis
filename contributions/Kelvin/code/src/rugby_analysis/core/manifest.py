"""Small JSON manifest used for incremental raw-match processing."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class ProcessingManifest:
    """Tracks exactly which raw file version produced each normalized match."""

    adapter: str
    entries: dict[str, dict[str, Any]] = field(default_factory=dict)
    schema_version: int = 1

    @classmethod
    def load(cls, path: Path, adapter: str) -> "ProcessingManifest":
        if not path.exists():
            return cls(adapter=adapter)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls(adapter=adapter)
        if payload.get("adapter") != adapter:
            return cls(adapter=adapter)
        return cls(
            adapter=adapter,
            entries=dict(payload.get("entries", {})),
            schema_version=int(payload.get("schema_version", 1)),
        )

    def is_current(self, raw_file: Path, content_hash: str, output_file: Path) -> bool:
        entry = self.entries.get(str(raw_file.resolve()))
        return bool(entry and entry.get("sha256") == content_hash and output_file.exists())

    def record(self, raw_file: Path, content_hash: str, match_id: str, output_file: Path, event_count: int) -> None:
        self.entries[str(raw_file.resolve())] = {
            "sha256": content_hash,
            "match_id": match_id,
            "output_file": str(output_file.resolve()),
            "event_count": event_count,
            "processed_at_utc": datetime.now(UTC).isoformat(),
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": self.schema_version,
            "adapter": self.adapter,
            "entries": self.entries,
            "saved_at_utc": datetime.now(UTC).isoformat(),
        }
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(path)
