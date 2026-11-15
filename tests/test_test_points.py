import csv
import json

from core.test_points import extract_test_points, write_test_points
from core.gaps import count_test_points
from core.units import bar_to_atm, mmhg_to_atm


def _write(path, content):
    path.write_text(content, encoding="utf-8")


def test_extract_test_points_converts_supported_units_and_keeps_outcomes(tmp_path):
    _write(
        tmp_path / "FLEX_PSI-69.csv",
        "FLEX Test #,Fuel,Ambient pressure; mmHg,O initial ambient composition; mole fraction,"
        "Burn time; s,Test end\n1,Methanol,760,0.21,4.3,Extinction\n",
    )
    _write(
        tmp_path / "CFI-G_Normal_Flames_PSI-159.csv",
        "Test,Fuel,XO2 before test,approx p (bar),Hot ignition\nA,ethane,0.4,1,Yes\n",
    )
    _write(
        tmp_path / "CFI_PSI-39.csv",
        "Flex Number,Fuel,Pressure,Oxygen\n1,C12H26,1 atm,0.21\n",
    )

    points = extract_test_points(tmp_path)

    flex = next(point for point in points if point["psi_id"] == "PSI-69")
    normal = next(point for point in points if point["source_file"].startswith("CFI-G"))
    cfi = next(point for point in points if point["psi_id"] == "PSI-39")
    assert flex["pressure_atm"] == mmhg_to_atm(760)
    assert flex["o2_chamber_pct"] == 21.0
    assert json.loads(flex["outcomes"]) == {"Burn time; s": "4.3", "Test end": "Extinction"}
    assert normal["o2_chamber_pct"] == 40.0
    assert normal["pressure_atm"] == bar_to_atm(1)
    assert cfi["pressure_atm"] == 1.0


def test_extract_test_points_keeps_stream_oxygen_separate(tmp_path):
    _write(
        tmp_path / "CFI-G_Inverse_Flames_PSI-159.csv",
        "Test,Fuel,XO2,approx p (bar)\nA,ethane,0.85,1\n",
    )

    point = extract_test_points(tmp_path)[0]

    assert point["o2_stream_pct"] == 85.0
    assert point["o2_chamber_pct"] is None


def test_extract_test_points_flags_invalid_values_and_preserves_source_text(tmp_path):
    _write(
        tmp_path / "ACME_BRE_PSI-20.csv",
        "Date,Fuel Bottle,Oxygen Conc (percent)\n"
        "1,50% C2H4,3400%\n"
        "2,50% C2H4,21\n",
    )
    _write(
        tmp_path / "Spice_PSI-107.csv",
        "GMT date,Fuel,Air Rate (cm/s)\n1,Ethylene,-1\n",
    )
    _write(
        tmp_path / "FLEX_PSI-69.csv",
        "FLEX Test #,Fuel,Ambient pressure; mmHg,O initial ambient composition; mole fraction\n"
        "1,Methanol,0,0.21\n",
    )

    points = extract_test_points(tmp_path)

    acme_bad = next(point for point in points if point["source_file"] == "ACME_BRE_PSI-20.csv" and point["source_value"])
    spice_bad = next(point for point in points if point["source_file"] == "Spice_PSI-107.csv")
    flex_bad = next(point for point in points if point["source_file"] == "FLEX_PSI-69.csv")
    assert json.loads(acme_bad["flags"]) == ["out_of_range"]
    assert acme_bad["source_value"] == "3400%"
    assert json.loads(spice_bad["flags"]) == ["out_of_range"]
    assert spice_bad["source_value"] == "-1"
    assert json.loads(flex_bad["flags"]) == ["placeholder"]
    assert flex_bad["source_value"] == "0"


def test_write_test_points_writes_only_flagged_rows_to_review_file(tmp_path):
    source = tmp_path / "FLEX_PSI-69.csv"
    _write(
        source,
        "FLEX Test #,Fuel,Ambient pressure; mmHg,O initial ambient composition; mole fraction\n"
        "1,Methanol,0,0.21\n",
    )

    points_path, flags_path = write_test_points(tmp_path / "processed", tmp_path)

    with points_path.open(newline="", encoding="utf-8") as file:
        assert len(list(csv.DictReader(file))) == 1
    with flags_path.open(newline="", encoding="utf-8") as file:
        flagged = list(csv.DictReader(file))
    assert len(flagged) == 1
    assert count_test_points("flex", tmp_path / "processed") == 1
