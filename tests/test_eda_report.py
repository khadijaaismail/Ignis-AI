import csv
from pathlib import Path

import pytest

import scripts.eda_report as eda_report
from scripts.eda_report import (
    TableData,
    column_flags,
    column_unit,
    discover_csv_paths,
    numeric_values,
    outcome_columns,
    profile_tables,
    read_csv_table,
)


def test_numeric_values_supports_scientific_notation_and_zero():
    values, missing = numeric_values(["0", "-2.5e-3", "1E+2", "", "not reported"])

    assert values == [0.0, -0.0025, 100.0]
    assert missing == 2


def test_numeric_values_does_not_parse_unstated_units():
    values, missing = numeric_values(["20 cm/s", "1 atm"])

    assert values == [20.0, 1.0]
    assert missing == 0


def test_flags_require_manual_review_and_do_not_reject_values():
    flags = column_flags("Ambient Pressure (atm)", [0.0], "atm")
    flags += column_flags("Air Flow (cm/s)", [-1.0], "cm/s")

    assert "manual review: zero pressure" in flags
    assert "manual review: negative airflow" in flags


def test_units_are_not_inferred_from_ranges():
    assert column_unit("Pressure") == "not stated"
    assert column_unit("Ambient Pressure (atm)") == "atm"


def test_outcome_detection_avoids_broad_co_substring():
    table = TableData(
        Path("PSI-1.csv"),
        ["Camera", "CO concentration", "Fuel", "Flame Type"],
        [{"Camera": "A", "CO concentration": "1", "Fuel": "methane", "Flame Type": "diffusion"}],
        "PSI-1",
    )

    assert outcome_columns([table])["PSI-1.csv"] == {"CO concentration", "Flame Type"}


def test_profile_reports_missing_percentage_and_zero_as_present():
    table = TableData(
        Path("PSI-2.csv"),
        ["Pressure (atm)"],
        [{"Pressure (atm)": "0"}, {"Pressure (atm)": ""}, {"Pressure (atm)": "1e0"}],
        "PSI-2",
    )

    profile = profile_tables([table])[0]

    assert profile.count == 2
    assert profile.missing == 1
    assert profile.missing_pct == pytest.approx(33.33)
    assert profile.unparseable == 0
    assert profile.minimum == 0.0
    assert profile.psi_ref == "PSI-2"
    assert profile.table == "PSI-2.csv"


def test_profile_separates_unparseable_cells_from_missing_values():
    table = TableData(
        Path("PSI-2_bad.csv"),
        ["Pressure (atm)"],
        [{"Pressure (atm)": "1"}, {"Pressure (atm)": "unknown"}],
        "PSI-2",
    )

    profile = profile_tables([table])[0]

    assert profile.missing == 0
    assert profile.missing_pct == 0
    assert profile.unparseable == 1


def test_profile_includes_categorical_boolean_and_text_columns():
    table = TableData(
        Path("PSI-5.csv"),
        ["Fuel", "Ignition", "Notes"],
        [
            {"Fuel": "methane", "Ignition": "yes", "Notes": "short"},
            {"Fuel": "propane", "Ignition": "no", "Notes": "a longer note"},
            {"Fuel": "", "Ignition": "yes", "Notes": "short"},
        ],
        "PSI-5",
    )

    profiles = {profile.column: profile for profile in profile_tables([table])}

    assert profiles["Fuel"].data_type == "categorical"
    assert profiles["Fuel"].missing == 1
    assert profiles["Fuel"].unique_count == 2
    assert profiles["Ignition"].data_type == "boolean-like"
    assert profiles["Notes"].data_type == "text"
    assert profiles["Notes"].minimum is None


def test_source_ids_keep_identical_filenames_distinct(tmp_path):
    first = tmp_path / "first" / "PSI-6.csv"
    second = tmp_path / "second" / "PSI-6.csv"
    first.parent.mkdir()
    second.parent.mkdir()
    for path, column in ((first, "Flame"), (second, "Smoke")):
        path.write_text(f"{column}\nreported\n", encoding="utf-8")

    tables = [read_csv_table(first), read_csv_table(second)]
    outcomes = outcome_columns(tables, tmp_path)
    profiles = profile_tables(tables, tmp_path)

    assert set(outcomes) == {"first/PSI-6.csv", "second/PSI-6.csv"}
    assert {profile.table for profile in profiles} == {
        "first/PSI-6.csv",
        "second/PSI-6.csv",
    }


def test_csv_parser_preserves_quoted_multiline_fields(tmp_path):
    path = tmp_path / "PSI-7.csv"
    path.write_text('Notes,Value\n"line one\nline two",1\n', encoding="utf-8")

    table = read_csv_table(path)

    assert table.rows == [{"Notes": "line one\nline two", "Value": "1"}]
    assert not any("malformed" in issue for issue in table.issues)


def test_required_experiment_columns_are_validated(tmp_path, monkeypatch):
    path = tmp_path / "experiments.csv"
    path.write_text("slug,psi_ref\nexample,PSI-8\n", encoding="utf-8")
    monkeypatch.setattr(eda_report, "EXPERIMENTS_PATH", path)

    with pytest.raises(ValueError, match="missing required columns"):
        eda_report._required_experiments()


def test_first_display_value_skips_explicit_missing_markers():
    from scripts.eda_report import first_display_value

    assert first_display_value({"a": "NA", "b": "reported"}, ("a", "b")) == "reported"


def test_csv_discovery_and_malformed_rows_are_reported(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()
    path = nested / "PSI-3_bad.csv"
    path.write_text("A,B\n1,2,3\n", encoding="utf-8")

    assert discover_csv_paths(tmp_path) == [path]
    table = read_csv_table(path)

    assert table.rows == [{"A": "1", "B": "2"}]
    assert any("extra fields" in issue for issue in table.issues)


def test_empty_and_header_only_csvs_are_handled(tmp_path):
    empty = tmp_path / "empty.csv"
    header_only = tmp_path / "PSI-4_header.csv"
    empty.write_text("", encoding="utf-8")
    header_only.write_text("A,B\n", encoding="utf-8")

    assert "empty CSV file" in read_csv_table(empty).issues
    assert "header-only CSV with no data rows" in read_csv_table(header_only).issues


def test_csv_field_size_limit_retries_after_windows_overflow(monkeypatch):
    calls = []

    def field_size_limit(limit):
        calls.append(limit)
        if limit > 2**31:
            raise OverflowError
        return limit

    monkeypatch.setattr(eda_report.csv, "field_size_limit", field_size_limit)

    eda_report._set_csv_field_size_limit()

    assert len(calls) > 1
    assert calls[-1] <= 2**31


def test_duplicate_and_blank_headers_are_reported_without_losing_values(tmp_path):
    path = tmp_path / "PSI-9_headers.csv"
    path.write_text(" A ,A,,Value\nfirst,second,blank,3\n", encoding="utf-8")

    table = read_csv_table(path)

    assert any("blank header" in issue for issue in table.issues)
    assert any("duplicate header after whitespace normalization" in issue for issue in table.issues)
    assert table.rows[0]["A"] == "first"
    assert table.rows[0]["A [duplicate 2]"] == "second"
    assert table.rows[0]["[blank header 3]"] == "blank"


def test_mixed_cell_units_withhold_descriptive_statistics():
    table = TableData(
        Path("PSI-10_units.csv"),
        ["Pressure"],
        [{"Pressure": "1 psi"}, {"Pressure": "2 atm"}],
        "PSI-10",
    )

    profile = profile_tables([table])[0]

    assert profile.minimum is None
    assert profile.mean is None
    assert "mixed explicit cell units" in profile.flags
    assert "descriptive statistics withheld" in profile.flags


def test_declared_unit_mismatch_is_flagged_and_original_values_remain():
    table = TableData(
        Path("PSI-11_units.csv"),
        ["Pressure (psi)"],
        [{"Pressure (psi)": "1 atm"}, {"Pressure (psi)": "2 atm"}],
        "PSI-11",
    )

    profile = profile_tables([table])[0]

    assert profile.minimum is None
    assert "inconsistent with declared unit psi" in profile.flags


def test_identifiers_are_not_numeric_measurements():
    table = TableData(
        Path("PSI-12_ids.csv"),
        ["experiment_id", "Reference URL", "Measured"],
        [{"experiment_id": "1", "Reference URL": "https://example.test/1", "Measured": "2"}],
        "PSI-12",
    )

    profiles = {profile.column: profile for profile in profile_tables([table])}

    assert profiles["experiment_id"].data_type == "identifier"
    assert profiles["experiment_id"].minimum is None
    assert profiles["Reference URL"].data_type == "reference"
    assert profiles["Measured"].data_type == "numeric"


def test_discrepancy_file_access_errors_are_reported_as_empty(monkeypatch):
    class UnreadablePath:
        def read_text(self, **_):
            raise OSError("denied")

    monkeypatch.setattr(eda_report, "DISCREPANCIES_PATH", UnreadablePath())

    assert eda_report.discrepancy_refs() == set()


def test_unavailable_chunks_do_not_mark_every_investigation_missing(monkeypatch, tmp_path):
    experiments = tmp_path / "experiments.csv"
    experiments.write_text(
        "slug,psi_ref,investigation_type,include_in_ranking,gravity_regime,conditions_status\n"
        "example,PSI-13,type,yes,unknown,reported\n",
        encoding="utf-8",
    )
    tables = tmp_path / "tables"
    tables.mkdir()
    (tables / "PSI-13.csv").write_text("Value\n1\n", encoding="utf-8")
    monkeypatch.setattr(eda_report, "EXPERIMENTS_PATH", experiments)
    monkeypatch.setattr(eda_report, "TABLES_DIR", tables)
    monkeypatch.setattr(eda_report, "DISCREPANCIES_PATH", tmp_path / "missing.md")
    monkeypatch.setattr(
        eda_report,
        "CHUNKS_PATH",
        tmp_path / "missing.parquet",
    )

    report = eda_report.build_report()

    assert "not assessed; optional chunks file unavailable" in report
    assert "- Investigations with no chunks: example" not in report


def test_available_empty_chunks_marks_investigations_missing(monkeypatch, tmp_path):
    experiments = tmp_path / "experiments.csv"
    experiments.write_text(
        "slug,psi_ref,investigation_type,include_in_ranking,gravity_regime,conditions_status\n"
        "example,PSI-13,type,yes,unknown,reported\n",
        encoding="utf-8",
    )
    tables = tmp_path / "tables"
    tables.mkdir()
    (tables / "PSI-13.csv").write_text("Value\n1\n", encoding="utf-8")
    monkeypatch.setattr(eda_report, "EXPERIMENTS_PATH", experiments)
    monkeypatch.setattr(eda_report, "TABLES_DIR", tables)
    monkeypatch.setattr(eda_report, "DISCREPANCIES_PATH", tmp_path / "missing.md")
    monkeypatch.setattr(eda_report, "chunk_counts", lambda: ({}, None))

    report = eda_report.build_report()

    assert "- Investigations with no chunks: example" in report
