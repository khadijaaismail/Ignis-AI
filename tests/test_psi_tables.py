import csv
import json
from pathlib import Path

import pytest

from core.psi_tables import load_psi_table, parse_condition_cell


@pytest.mark.parametrize(
    ("text", "kind", "values", "minimum", "maximum"),
    [
        ("0.17; 0.21;0.25; 0.3", "list", (0.17, 0.21, 0.25, 0.3), None, None),
        ("0.5; 1.0; 1.5; 2.0; or 3.0 ", "list", (0.5, 1.0, 1.5, 2.0, 3.0), None, None),
        ("0.1 - 5", "range", (), 0.1, 5.0),
        ("25", "single", (25.0,), None, None),
    ],
)
def test_parse_condition_cell(text, kind, values, minimum, maximum):
    parsed = parse_condition_cell(text)
    assert parsed.kind == kind
    assert parsed.values == values
    assert parsed.minimum == minimum
    assert parsed.maximum == maximum
    assert parsed.original == text.strip()


def test_load_psi_table_maps_units_and_preserves_outcomes(tmp_path):
    source = Path(__file__).parent / "fixtures" / "psi_conditions.csv"
    target = tmp_path / "PSI-68_fixture.csv"
    target.write_bytes(source.read_bytes().replace(b"\n", b"\r\n"))

    record = load_psi_table(target, "fixture", "PSI-68")

    assert record.fuels == ["heptane/air mixture"]
    assert record.o2_chamber_values_pct == [17.0, 21.0, 25.0, 30.0]
    assert record.pressure_min_psi == pytest.approx(1.47)
    assert record.pressure_max_psi == pytest.approx(73.48)
    assert record.flow_velocity_min_cm_s == 0.5
    assert record.flow_velocity_max_cm_s == 3.0
    assert record.conditions_discrete is True
    extra = json.loads(record.extra_conditions)
    assert extra["Extinction"] == "yes"
    assert extra["Unmapped Column"] == "kept"
    provenance = json.loads(record.provenance)
    assert provenance["o2_chamber_values_pct"]["conversion"] == "mole fraction times 100"
    assert provenance["pressure_min_psi"]["conversion"] == "atm times 14.696"


def test_load_psi_table_strips_whitespace_from_headers(tmp_path, caplog):
    source = tmp_path / "PSI-103_whitespace.csv"
    source.write_text(
        " Sample (Fuel Type) , Initial Droplet Diameter (mm) , Ambient Gas Mixture ,"
        " Oxygen Mole Fraction , Ambient Pressure (atm) , Ambient Temperature (C) ,"
        " Flow Velocity (cm/s) \n"
        "fuel,1.0,air,0.2,1,20,1\n",
        encoding="utf-8",
    )

    record = load_psi_table(source, "whitespace", "PSI-103")

    assert record.ambient_gas == "air"
    assert record.ambient_temp_c == 20.0
    assert "Expected mapped column" not in caplog.text


def test_real_psi_tables_have_exact_unit_conversions():
    paths = sorted(Path("data/raw/psi_tables").glob("PSI-*.csv"))
    if not paths:
        pytest.skip("No real PSI tables checked into this checkout")
    for path in paths:
        with path.open(newline="", encoding="utf-8-sig") as file:
            row = {key.strip(): value.strip() for key, value in next(csv.DictReader(file)).items()}
        record = load_psi_table(path, path.stem.split("_", 1)[1], path.stem.split("_", 1)[0])
        if row.get("Oxygen Mole Fraction"):
            original = parse_condition_cell(row["Oxygen Mole Fraction"])
            expected = [round(value * 100, 2) for value in original.values]
            assert [round(value, 2) for value in record.o2_chamber_values_pct] == expected
        if row.get("Ambient Pressure (atm)"):
            original = parse_condition_cell(row["Ambient Pressure (atm)"])
            if original.kind == "list":
                expected = [round(value * 14.696, 2) for value in original.values]
                assert record.pressure_values_psi == expected


def test_load_psi_table_deduplicates_values_and_preserves_rows(tmp_path):
    source = tmp_path / "PSI-99_rows.csv"
    source.write_text(
        "Sample (Fuel Type),Initial Droplet Diameter (mm),Ambient Gas Mixture,"
        "Oxygen Mole Fraction,Ambient Pressure (atm),Ambient Temperature (C),"
        "Flow Velocity (cm/s),Extinction\n"
        "fuel,1.0,air,0.2; 0.3,1; 2,20,1,yes\n"
        "fuel,1.0; 2.0,air,0.3; 0.4,2; 3,21,2,no\n",
        encoding="utf-8",
    )

    record = load_psi_table(source, "rows", "PSI-99")
    extra = json.loads(record.extra_conditions)

    assert record.o2_chamber_values_pct == [20.0, 30.0, 40.0]
    assert record.o2_chamber_min_pct == 20.0
    assert record.o2_chamber_max_pct == 40.0
    assert record.pressure_values_psi == [14.7, 29.39, 44.09]
    assert record.pressure_min_psi == pytest.approx(14.7)
    assert record.pressure_max_psi == pytest.approx(44.09)
    assert extra["initial_droplet_diameter_mm"] == ["1.0", "2.0"]
    assert extra["ambient_gas"] == ["air"]
    assert extra["ambient_temp_c"] == ["20", "21"]
    assert extra["rows"] == [
        {
            "fuel": "fuel",
            "droplet_diameter_mm": "1.0",
            "ambient_gas": "air",
            "o2_chamber_original": "0.2; 0.3",
            "pressure_original": "1; 2",
            "ambient_temp_c": "20",
            "flow_velocity_original": "1",
            "extinction": "yes",
        },
        {
            "fuel": "fuel",
            "droplet_diameter_mm": "1.0; 2.0",
            "ambient_gas": "air",
            "o2_chamber_original": "0.3; 0.4",
            "pressure_original": "2; 3",
            "ambient_temp_c": "21",
            "flow_velocity_original": "2",
            "extinction": "no",
        },
    ]
    assert record.conditions_discrete is True


def test_load_psi_table_keeps_unparseable_cells_and_derived_provenance(tmp_path, caplog):
    source = tmp_path / "PSI-100_bad.csv"
    source.write_text(
        "Sample (Fuel Type),Ambient Gas Mixture,Oxygen Mole Fraction,"
        "Ambient Pressure (atm),Ambient Temperature (C),Flame Size\n"
        "fuel,air,not reported;,bad or 2,20 C,large\n",
        encoding="utf-8",
    )

    record = load_psi_table(source, "bad", "PSI-100")
    extra = json.loads(record.extra_conditions)
    provenance = json.loads(record.provenance)

    assert extra["Oxygen Mole Fraction"] == "not reported;"
    assert extra["Ambient Pressure (atm)"] == "bad or 2"
    assert extra["ambient_temp_c"] == "20 C"
    assert "Oxygen Mole Fraction" in caplog.text
    assert provenance["id"]["status"] == "derived"
    assert provenance["slug"]["status"] == "derived"
    assert provenance["name"]["status"] == "derived"


def test_parse_condition_cell_accepts_trailing_semicolon_and_case_insensitive_or():
    assert parse_condition_cell("1; 2; OR 3;").values == (1.0, 2.0, 3.0)


def test_load_psi_table_marks_partial_condition_provenance_and_builds_clean_rows(tmp_path, caplog):
    source = tmp_path / "PSI-101_partial.csv"
    source.write_text(
        "Sample (Fuel Type),Initial Droplet Diameter (mm),Ambient Gas Mixture,"
        "Oxygen Mole Fraction,Ambient Pressure (atm),Ambient Temperature (C),"
        "Flow Velocity (cm/s),Extinction\n"
        "fuel,1.0,air,0.2; bad,1; bad,20,1; bad,yes\n"
        "fuel,,nitrogen,0.3,2,21,2,no\n"
        ",,,,,,,\n",
        encoding="utf-8",
    )

    record = load_psi_table(source, "partial", "PSI-101")
    extra = json.loads(record.extra_conditions)
    provenance = json.loads(record.provenance)

    assert record.ambient_gas == "air; nitrogen"
    assert provenance["o2_chamber_values_pct"]["status"] == "partial"
    assert "bad" in provenance["o2_chamber_values_pct"]["source"]
    assert provenance["pressure_values_psi"]["status"] == "partial"
    assert provenance["flow_velocity_min_cm_s"]["status"] == "partial"
    assert extra["rows"] == [
        {
            "fuel": "fuel",
            "droplet_diameter_mm": "1.0",
            "ambient_gas": "air",
            "o2_chamber_original": "0.2; bad",
            "pressure_original": "1; bad",
            "ambient_temp_c": "20",
            "flow_velocity_original": "1; bad",
            "extinction": "yes",
        },
        {
            "fuel": "fuel",
            "ambient_gas": "nitrogen",
            "o2_chamber_original": "0.3",
            "pressure_original": "2",
            "ambient_temp_c": "21",
            "flow_velocity_original": "2",
            "extinction": "no",
        },
    ]
    assert "more cells than headers" not in caplog.text
    assert provenance["o2_chamber_original"]["status"] == "partial"
    assert provenance["flow_velocity_original"]["status"] == "partial"
    assert provenance["rows"]["status"] == "reported"


def test_load_psi_table_warns_for_missing_mapped_columns_and_extra_cells(tmp_path, caplog):
    source = tmp_path / "PSI-102_missing.csv"
    source.write_text(
        "Sample (Fuel Type),Ambient Gas Mixture,Oxygen Mole Fraction\n"
        "fuel,air,0.2,unexpected\n",
        encoding="utf-8",
    )

    load_psi_table(source, "missing", "PSI-102")

    assert "more cells than headers" in caplog.text
    assert "Ambient Pressure (atm)" in caplog.text
    assert "Flow Velocity (cm/s)" in caplog.text
    assert "Expected outcome column" not in caplog.text


def test_parse_condition_cell_strips_trailing_comma():
    assert parse_condition_cell("1,").values == (1.0,)


def test_real_tables_use_declared_pressure_units():
    flex = load_psi_table(
        Path("data/raw/psi_tables/FLEX_PSI-69.csv"), "flex", "PSI-69"
    )
    cfi_g = load_psi_table(
        Path("data/raw/psi_tables/CFI-G_Normal_Flames_PSI-159.csv"),
        "cfi-g",
        "PSI-159",
    )
    assert flex.pressure_original_unit == "mmHg"
    assert flex.pressure_values_psi
    assert cfi_g.pressure_original_unit == "bar"
    assert cfi_g.pressure_values_psi
    assert cfi_g.o2_chamber_values_pct == []
    assert cfi_g.o2_stream_min_pct is not None
