"""Extract row-level test points from the source PSI tables."""

from __future__ import annotations

import csv
import json
import logging
import re
from pathlib import Path
from typing import Any

from .config import ROOT_DIR
from .units import bar_to_atm, mmhg_to_atm, oxygen_mole_fraction_to_pct, atm_to_psi

LOGGER = logging.getLogger(__name__)

OUTPUT_COLUMNS = [
    "slug",
    "psi_id",
    "test_id",
    "o2_chamber_pct",
    "o2_stream_pct",
    "pressure_atm",
    "pressure_psi",
    "airflow_cm_s",
    "fuel_or_material",
    "source_file",
    "source_value",
    "outcomes",
    "flags",
]


def _mapping(
    *,
    psi_id: str,
    oxygen: str | None = None,
    oxygen_unit: str | None = None,
    oxygen_role: str = "chamber",
    pressure: str | None = None,
    pressure_unit: str | None = None,
    airflow: str | None = None,
    fuel: str | None = None,
    test_id: str | None = None,
) -> dict[str, str | None]:
    return {
        "psi_id": psi_id,
        "oxygen": oxygen,
        "oxygen_unit": oxygen_unit,
        "oxygen_role": oxygen_role,
        "pressure": pressure,
        "pressure_unit": pressure_unit,
        "airflow": airflow,
        "fuel": fuel,
        "test_id": test_id,
    }


# Keep this table explicit: each supported source file has one source-specific mapping.
TABLE_MAPPINGS: dict[str, dict[str, str | None]] = {
    "FLEX_PSI-69.csv": _mapping(
        psi_id="PSI-69",
        oxygen="O initial ambient composition; mole fraction",
        oxygen_unit="fraction",
        pressure="Ambient pressure; mmHg",
        pressure_unit="mmHg",
        fuel="Fuel",
        test_id="FLEX Test #",
    ),
    "CFI_PSI-39.csv": _mapping(
        psi_id="PSI-39",
        oxygen="Oxygen",
        oxygen_unit="fraction",
        pressure="Pressure",
        pressure_unit="atm",
        fuel="Fuel",
        test_id="Flex Number",
    ),
    "CFI-G_Normal_Flames_PSI-159.csv": _mapping(
        psi_id="PSI-159",
        oxygen="XO2 before test",
        oxygen_unit="fraction",
        pressure="approx p (bar)",
        pressure_unit="bar",
        fuel="Fuel",
        test_id="Test",
    ),
    "CFI-G_Inverse_Flames_PSI-159.csv": _mapping(
        psi_id="PSI-159",
        oxygen="XO2",
        oxygen_unit="fraction",
        oxygen_role="stream",
        pressure="approx p (bar)",
        pressure_unit="bar",
        fuel="Fuel",
        test_id="Test",
    ),
    "ACME_BRE_PSI-20.csv": _mapping(
        psi_id="PSI-20",
        oxygen="Oxygen Conc (percent)",
        oxygen_unit="percent",
        fuel="Fuel Bottle",
        test_id="Date",
    ),
    "BASS-II_PSI-25.csv": _mapping(
        psi_id="PSI-25",
        oxygen="Calibrated initial O2 % by vol",
        oxygen_unit="percent",
        fuel="Fuel Sample Material",
        test_id="Test #",
    ),
    "Saffire-I_PSI-98.csv": _mapping(
        psi_id="PSI-98",
        oxygen="Percent O2",
        oxygen_unit="percent",
        airflow="Air Flow (cm/s)",
        fuel="Material",
        test_id="Sample Number",
    ),
    "Saffire-II_PSI-99.csv": _mapping(
        psi_id="PSI-99",
        oxygen="Percent O2 (Note 1)",
        oxygen_unit="percent",
        airflow="Air Flow (cm/s)",
        fuel="Material",
        test_id="Sample Number",
    ),
    "Spice_PSI-107.csv": _mapping(
        psi_id="PSI-107",
        airflow="Air Rate (cm/s)",
        fuel="Fuel",
        test_id="GMT date",
    ),
    "SAME-R_PSI-101.csv": _mapping(
        psi_id="PSI-101",
        airflow="Inlet velocity (cm/s)",
        fuel="Sample Type",
        test_id="SAME Test #",
    ),
    "SAME_PSI-102.csv": _mapping(
        psi_id="PSI-102",
        airflow="Air Flow (cm/s)",
        fuel="Sample Material",
        test_id="Sample #",
    ),
    "Flex2_PSI-68.csv": _mapping(
        psi_id="PSI-68",
        oxygen="Oxygen Mole Fraction",
        oxygen_unit="fraction",
        pressure="Ambient Pressure (atm)",
        pressure_unit="atm",
        airflow="Flow Velocity (cm/s)",
        fuel="Sample (Fuel Type)",
        test_id="Sample (Fuel Type)",
    ),
}

_NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
_RANGE = re.compile(r"\s+-\s+")
_OUTCOME_WORDS = (
    "burn",
    "flame",
    "extinction",
    "ignition",
    "spread",
    "test end",
    "burning rate",
    "hot ignition",
)


def _headers_and_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        headers = [header.strip() for header in (reader.fieldnames or [])]
        rows = [
            {key.strip(): (value or "").strip() for key, value in row.items() if key}
            for row in reader
        ]
    return headers, rows


def _resolve_column(column: str | None, headers: list[str]) -> str | None:
    if not column:
        return None
    if column in headers:
        return column
    normalized = " ".join(column.split())
    return next(
        (header for header in headers if " ".join(header.split()) == normalized),
        None,
    )


def _numeric(text: str) -> float | None:
    value = text.strip().replace(",", "")
    value = re.sub(r"^(?:~|approximately)\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s*(?:%|atm|bar|mmhg|cm/s)\s*$", "", value, flags=re.IGNORECASE)
    if not value or _RANGE.search(value) or not _NUMBER.fullmatch(value):
        return None
    return float(value)


def _slug(filename: str) -> str:
    stem = Path(filename).stem
    return re.split(r"_PSI-", stem, maxsplit=1, flags=re.IGNORECASE)[0].lower().replace(" ", "_")


def _outcomes(headers: list[str], row: dict[str, str], mapping: dict[str, str | None]) -> dict[str, str]:
    mapped = {value for value in mapping.values() if value}
    return {
        header: row[header]
        for header in headers
        if header not in mapped
        and row.get(header, "")
        and any(word in header.lower() for word in _OUTCOME_WORDS)
    }


def _convert_oxygen(value: float, unit: str | None) -> float:
    return oxygen_mole_fraction_to_pct(value) if unit == "fraction" else value


def _parse_value(
    raw: str,
    *,
    field: str,
    unit: str | None,
    mapping: dict[str, str | None],
) -> tuple[float | None, str | None]:
    if not raw:
        return None, None
    value = _numeric(raw)
    if value is None:
        return None, "unparsed"
    if field == "oxygen":
        value = _convert_oxygen(value, unit)
        if not 0 <= value <= 100:
            return None, "out_of_range"
    elif field == "pressure":
        if value == 0:
            return None, "placeholder"
        if value < 0:
            return None, "out_of_range"
        if unit == "mmHg":
            value = mmhg_to_atm(value)
        elif unit == "bar":
            value = bar_to_atm(value)
    elif field == "airflow" and value < 0:
        return None, "out_of_range"
    return value, None


def extract_test_points(input_dir: str | Path | None = None) -> list[dict[str, Any]]:
    """Read supported PSI tables into row-level test-point records."""
    source_dir = Path(input_dir or ROOT_DIR / "data" / "raw" / "psi_tables")
    points: list[dict[str, Any]] = []
    for path in sorted(source_dir.glob("*.csv")):
        mapping = TABLE_MAPPINGS.get(path.name)
        if mapping is None:
            continue
        headers, rows = _headers_and_rows(path)
        mapped_columns = (
            mapping["oxygen"],
            mapping["pressure"],
            mapping["airflow"],
            mapping["fuel"],
            mapping["test_id"],
        )
        resolved = {
            key: _resolve_column(value, headers)
            for key, value in mapping.items()
            if key not in {"psi_id", "oxygen_unit", "oxygen_role", "pressure_unit"}
        }
        missing = [
            value
            for value in mapped_columns
            if value and resolved.get(next(key for key, item in mapping.items() if item == value)) is None
        ]
        if missing:
            LOGGER.warning("Skipping %s; mapped columns are missing: %s", path.name, ", ".join(missing))
            continue
        for index, row in enumerate(rows, start=1):
            flags: list[str] = []
            source_values: list[str] = []
            values: dict[str, Any] = {}
            for field in ("oxygen", "pressure", "airflow"):
                column = resolved.get(field)
                if not column:
                    continue
                parsed, flag = _parse_value(
                    row.get(column, ""),
                    field=field,
                    unit=mapping.get(f"{field}_unit"),
                    mapping=mapping,
                )
                values[field] = parsed
                if flag:
                    flags.append(flag)
                    source_values.append(row.get(column, ""))
            pressure_atm = values.get("pressure")
            point = {
                "slug": _slug(path.name),
                "psi_id": mapping["psi_id"],
                "test_id": row.get(resolved.get("test_id") or "", "") or str(index),
                "o2_chamber_pct": values.get("oxygen") if mapping["oxygen_role"] == "chamber" else None,
                "o2_stream_pct": values.get("oxygen") if mapping["oxygen_role"] == "stream" else None,
                "pressure_atm": pressure_atm,
                "pressure_psi": atm_to_psi(pressure_atm) if pressure_atm is not None else None,
                "airflow_cm_s": values.get("airflow"),
                "fuel_or_material": row.get(resolved.get("fuel") or "", ""),
                "source_file": path.name,
                "source_value": "; ".join(source_values),
                "outcomes": json.dumps(_outcomes(headers, row, resolved), ensure_ascii=False),
                "flags": json.dumps(flags),
            }
            points.append(point)
    return points


def write_test_points(
    output_dir: str | Path | None = None,
    input_dir: str | Path | None = None,
) -> tuple[Path, Path]:
    """Write test points and flagged rows to the processed data directory."""
    target_dir = Path(output_dir or ROOT_DIR / "data" / "processed")
    target_dir.mkdir(parents=True, exist_ok=True)
    points = extract_test_points(input_dir)
    points_path = target_dir / "test_points.csv"
    flags_path = target_dir / "test_points_flags.csv"
    with points_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(points)
    with flags_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(point for point in points if json.loads(point["flags"]))
    return points_path, flags_path
