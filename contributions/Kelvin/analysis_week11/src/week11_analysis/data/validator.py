"""Schema validation for the Queensland Reds partner event-file structure.

The partner has advised that this event schema is generally stable, with minor
exceptions for older or lower-level competitions.  Validation therefore separates
the columns required to load a usable event timeline from the columns used by
individual analysis modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd


CORE_REQUIRED_COLUMNS = frozenset(
    {
        "ID",
        "FXID",
        "teamName",
        "MatchTime",
        "period",
        "x_coord",
        "y_coord",
        "actionName",
    }
)

MODULE_REQUIRED_COLUMNS = {
    "kicking": frozenset({"ActionTypeName", "ActionResultName", "playerName"}),
    "breakdown": frozenset({"ActionTypeName", "ActionResultName"}),
    "tackling": frozenset({"ActionResultName", "playerName"}),
}


@dataclass(frozen=True)
class SchemaValidationReport:
    """Structured validation result suitable for the UI and automated tests."""

    missing_core_columns: tuple[str, ...]
    missing_module_columns: dict[str, tuple[str, ...]]

    @property
    def is_valid(self) -> bool:
        """Whether the file supports core ingestion."""

        return not self.missing_core_columns

    def module_is_supported(self, module_name: str) -> bool:
        """Return whether a named module has all of its needed fields."""

        return not self.missing_module_columns.get(module_name, ())

    def user_messages(self) -> list[str]:
        """Create concise, actionable messages without hiding the missing fields."""

        messages: list[str] = []
        if self.missing_core_columns:
            messages.append(
                "Core event ingestion needs these columns: "
                + ", ".join(self.missing_core_columns)
                + "."
            )
        for module_name, missing in self.missing_module_columns.items():
            if missing:
                messages.append(
                    f"{module_name.title()} analysis is unavailable until these columns are supplied: "
                    + ", ".join(missing)
                    + "."
                )
        return messages


def missing_columns(
    available_columns: Iterable[object], required_columns: Iterable[str]
) -> tuple[str, ...]:
    """Return required columns absent from the supplied headers, in stable order."""

    available = {str(column).strip() for column in available_columns}
    return tuple(sorted(set(required_columns) - available))


def validate_partner_schema(events: pd.DataFrame) -> SchemaValidationReport:
    """Validate the partner event schema without changing the source dataframe."""

    return SchemaValidationReport(
        missing_core_columns=missing_columns(events.columns, CORE_REQUIRED_COLUMNS),
        missing_module_columns={
            name: missing_columns(events.columns, required)
            for name, required in MODULE_REQUIRED_COLUMNS.items()
        },
    )
