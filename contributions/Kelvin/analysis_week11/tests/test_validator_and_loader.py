from __future__ import annotations

from io import BytesIO

import pandas as pd
import pytest

from week11_analysis.data.loader import PartnerFileSource, load_partner_batch, load_partner_data
from week11_analysis.data.validator import validate_partner_schema


def test_schema_validation_identifies_core_and_module_gaps() -> None:
    report = validate_partner_schema(pd.DataFrame({"ID": [1], "FXID": [2]}))

    assert not report.is_valid
    assert "teamName" in report.missing_core_columns
    assert "ActionTypeName" in report.missing_module_columns["kicking"]
    assert "tackling" in " ".join(report.user_messages()).casefold()


def test_loader_reads_csv_and_transforms_partner_rows(tmp_path, partner_rows) -> None:
    source = tmp_path / "representative_events.csv"
    partner_rows.to_csv(source, index=False)

    loaded = load_partner_data(source)

    assert loaded.validation.is_valid
    assert len(loaded.events) == len(partner_rows)
    assert {"fixture_id", "action_name", "x", "match_clock"}.issubset(loaded.events.columns)
    assert loaded.source_path == source.resolve()
    assert loaded.source_file_name == source.name
    assert set(loaded.events["source_file_name"]) == {source.name}


def test_loader_reads_xlsx_path(tmp_path, partner_rows) -> None:
    source = tmp_path / "representative_events.xlsx"
    partner_rows.to_excel(source, sheet_name="in", index=False)

    loaded = load_partner_data(source)

    assert loaded.validation.is_valid
    assert loaded.source_path == source.resolve()
    assert len(loaded.events) == len(partner_rows)


def test_loader_reads_csv_bytesio_without_creating_a_local_source(partner_rows) -> None:
    upload = BytesIO(partner_rows.to_csv(index=False).encode("utf-8"))

    loaded = load_partner_data(upload, filename="uploaded_fixture.csv")

    assert loaded.source_path is None
    assert loaded.source_file_name == "uploaded_fixture.csv"
    assert set(loaded.events["source_file_name"]) == {"uploaded_fixture.csv"}


def test_loader_reads_xlsx_bytesio_without_creating_a_local_source(partner_rows) -> None:
    upload = BytesIO()
    partner_rows.to_excel(upload, sheet_name="in", index=False)

    loaded = load_partner_data(upload, filename="uploaded_fixture.xlsx")

    assert loaded.source_path is None
    assert loaded.validation.is_valid
    assert len(loaded.events) == len(partner_rows)


def test_batch_combines_valid_files_and_preserves_source_file_metadata(partner_rows) -> None:
    first_upload = partner_rows.to_csv(index=False).encode("utf-8")
    second_rows = partner_rows.assign(FXID=949232)
    second_upload = BytesIO()
    second_rows.to_excel(second_upload, sheet_name="in", index=False)

    batch = load_partner_batch(
        (
            PartnerFileSource(BytesIO(first_upload), filename="round_16.csv"),
            PartnerFileSource(BytesIO(second_upload.getvalue()), filename="round_17.xlsx"),
        )
    )

    assert not batch.issues
    assert not batch.duplicate_files
    assert len(batch.loaded_files) == 2
    assert len(batch.events) == len(partner_rows) * 2
    assert set(batch.events["source_file_name"]) == {"round_16.csv", "round_17.xlsx"}
    assert set(batch.events["fixture_id"]) == {949231, 949232}


def test_batch_returns_friendly_issue_for_schema_invalid_file() -> None:
    invalid_upload = BytesIO(b"ID,FXID\n1,949231\n")

    batch = load_partner_batch((PartnerFileSource(invalid_upload, filename="bad_schema.csv"),))

    assert not batch.loaded_files
    assert len(batch.issues) == 1
    assert batch.issues[0].source_file_name == "bad_schema.csv"
    assert "cannot be loaded" in batch.issues[0].message


def test_batch_keeps_valid_file_when_another_file_is_invalid(partner_rows) -> None:
    valid_upload = BytesIO(partner_rows.to_csv(index=False).encode("utf-8"))
    invalid_upload = BytesIO(b"ID,FXID\n1,949231\n")

    batch = load_partner_batch(
        (
            PartnerFileSource(valid_upload, filename="valid_fixture.csv"),
            PartnerFileSource(invalid_upload, filename="bad_schema.csv"),
        )
    )

    assert len(batch.loaded_files) == 1
    assert len(batch.events) == len(partner_rows)
    assert len(batch.issues) == 1
    assert set(batch.events["source_file_name"]) == {"valid_fixture.csv"}


def test_batch_skips_duplicate_filename_and_size(partner_rows) -> None:
    payload = partner_rows.to_csv(index=False).encode("utf-8")

    batch = load_partner_batch(
        (
            PartnerFileSource(BytesIO(payload), filename="same_fixture.csv"),
            PartnerFileSource(BytesIO(payload), filename="same_fixture.csv"),
        )
    )

    assert len(batch.loaded_files) == 1
    assert batch.duplicate_files == ("same_fixture.csv",)
    assert len(batch.events) == len(partner_rows)


def test_loader_rejects_unsupported_extension(tmp_path) -> None:
    source = tmp_path / "not_events.txt"
    source.write_text("not a partner event file", encoding="utf-8")

    with pytest.raises(ValueError, match="extensions"):
        load_partner_data(source)
