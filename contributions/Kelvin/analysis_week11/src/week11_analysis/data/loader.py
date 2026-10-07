"""In-memory and local-file loader for partner-provided event data.

The Streamlit interface sends browser uploads here as file-like objects.  This
module never writes those uploads to ``data/raw``; filesystem paths remain a
separate development-only input for backwards compatibility and local testing.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from io import BytesIO
from os import PathLike
from pathlib import Path
from typing import BinaryIO
from zipfile import BadZipFile

import pandas as pd

from .transformation import transform_partner_events
from .validator import SchemaValidationReport, validate_partner_schema


SUPPORTED_FILE_SUFFIXES = frozenset({".csv", ".xlsx", ".xls"})
PartnerFileInput = str | Path | PathLike[str] | BinaryIO | bytes


@dataclass(frozen=True)
class LoadedPartnerData:
    """One validated partner file and its analysis-ready event records."""

    source_path: Path | None
    source_file_name: str
    raw_events: pd.DataFrame
    events: pd.DataFrame
    validation: SchemaValidationReport


@dataclass(frozen=True)
class PartnerFileSource:
    """A path, bytes, or file-like event source with an optional display name."""

    source: PartnerFileInput
    filename: str | None = None


@dataclass(frozen=True)
class PartnerFileIssue:
    """A recoverable problem associated with one file in a batch upload."""

    source_file_name: str
    message: str


@dataclass(frozen=True)
class PartnerBatchLoadResult:
    """Successful files plus user-readable per-file batch feedback."""

    loaded_files: tuple[LoadedPartnerData, ...]
    issues: tuple[PartnerFileIssue, ...]
    duplicate_files: tuple[str, ...]

    @property
    def events(self) -> pd.DataFrame:
        """Combine valid transformed inputs without changing their source labels."""

        if not self.loaded_files:
            return pd.DataFrame()
        return pd.concat(
            [loaded.events for loaded in self.loaded_files], ignore_index=True, sort=False
        )


def _is_path_input(source: PartnerFileInput) -> bool:
    return isinstance(source, (str, PathLike))


def _source_file_name(source: PartnerFileInput, filename: str | None = None) -> str:
    """Return a safe display name used for suffix checks and provenance."""

    candidate = filename
    if candidate is None:
        candidate = Path(source).name if _is_path_input(source) else getattr(source, "name", None)
    if not candidate:
        raise ValueError("Provide a filename ending in .csv, .xlsx, or .xls for the uploaded event file.")
    name = Path(str(candidate)).name
    if not name:
        raise ValueError("Provide a filename ending in .csv, .xlsx, or .xls for the uploaded event file.")
    return name


def _validated_suffix(source_file_name: str) -> str:
    suffix = Path(source_file_name).suffix.casefold()
    if suffix not in SUPPORTED_FILE_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_FILE_SUFFIXES))
        raise ValueError(
            f"'{source_file_name}' is not a supported partner event file. "
            f"Use one of these extensions: {supported}."
        )
    return suffix


def _local_source_path(source: PartnerFileInput) -> Path | None:
    """Resolve a real path while leaving uploads entirely in memory."""

    if not _is_path_input(source):
        return None
    source_path = Path(source).expanduser().resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"Partner event file was not found: {source_path}")
    return source_path


def _as_stream(source: PartnerFileInput) -> BinaryIO:
    if isinstance(source, bytes):
        return BytesIO(source)
    if hasattr(source, "read"):
        return source
    raise TypeError("Partner event uploads must be a filesystem path, bytes, or a readable file-like object.")


def _rewind(stream: BinaryIO) -> None:
    """Use a fresh read position when an UploadedFile was inspected earlier."""

    try:
        stream.seek(0)
    except (AttributeError, OSError, ValueError):
        # pandas can still read non-seekable streams where the cursor is already at the start.
        pass


def read_partner_file(
    source: PartnerFileInput, *, filename: str | None = None
) -> pd.DataFrame:
    """Read one CSV/XLS/XLSX source without persisting browser uploads to disk."""

    source_file_name = _source_file_name(source, filename)
    suffix = _validated_suffix(source_file_name)
    source_path = _local_source_path(source)
    reader: Path | BinaryIO
    if source_path is not None:
        reader = source_path
    else:
        reader = _as_stream(source)
        _rewind(reader)

    try:
        if suffix == ".csv":
            events = pd.read_csv(reader, encoding="utf-8-sig")
        else:
            with pd.ExcelFile(reader) as workbook:
                # The representative file uses a sheet named 'in'. Defaulting
                # to the first sheet supports partner CSV-equivalent exports.
                sheet_name = "in" if "in" in workbook.sheet_names else workbook.sheet_names[0]
                events = pd.read_excel(workbook, sheet_name=sheet_name)
    except (
        BadZipFile,
        ImportError,
        OSError,
        UnicodeDecodeError,
        ValueError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
    ) as error:
        raise ValueError(
            f"Could not read '{source_file_name}'. Check that it is a valid partner {suffix} file."
        ) from error

    if events.empty:
        raise ValueError(f"'{source_file_name}' has no event rows.")
    events.columns = [str(column).strip() for column in events.columns]
    return events


def load_partner_data(
    source: PartnerFileInput, *, filename: str | None = None
) -> LoadedPartnerData:
    """Load, validate, and transform one local path or in-memory partner file."""

    source_file_name = _source_file_name(source, filename)
    source_path = _local_source_path(source)
    raw_events = read_partner_file(source, filename=source_file_name)
    validation = validate_partner_schema(raw_events)
    if not validation.is_valid:
        detail = "; ".join(validation.user_messages())
        raise ValueError(f"The partner file cannot be loaded. {detail}")
    events = transform_partner_events(raw_events)
    # This metadata lets combined uploads retain provenance without changing
    # any source-driven analysis definitions or aggregations.
    events["source_file_name"] = source_file_name
    return LoadedPartnerData(
        source_path=source_path,
        source_file_name=source_file_name,
        raw_events=raw_events,
        events=events,
        validation=validation,
    )


def _source_size(source: PartnerFileInput) -> int | None:
    """Get a cheap size for duplicate protection without saving an upload."""

    if _is_path_input(source):
        try:
            return Path(source).expanduser().stat().st_size
        except OSError:
            return None
    if isinstance(source, bytes):
        return len(source)
    declared_size = getattr(source, "size", None)
    if isinstance(declared_size, int) and declared_size >= 0:
        return declared_size
    try:
        return source.getbuffer().nbytes
    except (AttributeError, TypeError, ValueError):
        pass
    try:
        return len(source.getvalue())
    except (AttributeError, TypeError, ValueError):
        return None


def load_partner_batch(
    sources: Iterable[PartnerFileSource | PartnerFileInput],
) -> PartnerBatchLoadResult:
    """Load valid files in a batch while retaining useful file-level feedback.

    Duplicate protection deliberately uses the minimum transparent identity of
    filename plus byte size. A malformed upload does not prevent a valid file
    in the same selection from being analysed.
    """

    loaded_files: list[LoadedPartnerData] = []
    issues: list[PartnerFileIssue] = []
    duplicate_files: list[str] = []
    seen_identities: set[tuple[str, int]] = set()

    for item in sources:
        file_source = item if isinstance(item, PartnerFileSource) else PartnerFileSource(item)
        try:
            source_file_name = _source_file_name(file_source.source, file_source.filename)
            size = _source_size(file_source.source)
            identity = (source_file_name.casefold(), size) if size is not None else None
            if identity is not None and identity in seen_identities:
                duplicate_files.append(source_file_name)
                continue
            if identity is not None:
                seen_identities.add(identity)
            loaded_files.append(load_partner_data(file_source.source, filename=source_file_name))
        except (FileNotFoundError, OSError, TypeError, ValueError) as error:
            issue_name = getattr(file_source.source, "name", None) or file_source.filename or "Uploaded file"
            issues.append(PartnerFileIssue(Path(str(issue_name)).name, str(error)))
        except Exception:
            # A damaged third-party workbook parser must not discard another
            # valid file from the same browser selection or expose a traceback.
            issue_name = getattr(file_source.source, "name", None) or file_source.filename or "Uploaded file"
            issues.append(
                PartnerFileIssue(
                    Path(str(issue_name)).name,
                    "Could not load this file. Check that it is a valid partner CSV or XLSX event file.",
                )
            )

    return PartnerBatchLoadResult(
        loaded_files=tuple(loaded_files),
        issues=tuple(issues),
        duplicate_files=tuple(duplicate_files),
    )


def discover_local_partner_files(raw_directory: str | Path) -> list[Path]:
    """Return locally available, non-hidden candidate files in a raw-data folder."""

    directory = Path(raw_directory)
    if not directory.is_dir():
        return []
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file()
        and not path.name.startswith("~$")
        and path.suffix.casefold() in SUPPORTED_FILE_SUFFIXES
    )
