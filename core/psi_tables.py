"""Load NASA PSI tables using explicit, source-specific column mappings."""

from __future__ import annotations

import csv
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import yaml

from .config import ROOT_DIR
from .schema import Experiment
from .units import (
    atm_to_psi,
    bar_to_psi,
    mmhg_to_psi,
    oxygen_mole_fraction_to_pct,
)

LOGGER = logging.getLogger(__name__)
_NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)"
_RANGE = re.compile(rf"^\s*({_NUMBER})\s*-\s*({_NUMBER})\s*$")


@dataclass(frozen=True)
class ParsedCondition:
    """A condition cell while retaining its source representation."""

    kind: str
    original: str
    values: tuple[float, ...] = ()
    minimum: float | None = None
    maximum: float | None = None


def parse_condition_cell(text: str) -> ParsedCondition:
    """Parse a condition cell as a list, range, or single value."""
    original = text.strip().rstrip(";,").strip()
    if not original:
        raise ValueError("Condition cell cannot be empty")
    parts = [
        part.strip()
        for part in re.split(r";|\bor\b", original, flags=re.IGNORECASE)
        if part.strip()
    ]
    if len(parts) > 1:
        try:
            values = tuple(float(part) for part in parts)
        except ValueError as exc:
            raise ValueError(f"Invalid condition list: {text!r}") from exc
        return ParsedCondition("list", original, values=values)
    match = _RANGE.match(original)
    if match:
        minimum, maximum = (float(value) for value in match.groups())
        if minimum > maximum:
            raise ValueError(f"Condition range is reversed: {text!r}")
        return ParsedCondition("range", original, minimum=minimum, maximum=maximum)
    try:
        return ParsedCondition("single", original, values=(float(original),))
    except ValueError as exc:
        raise ValueError(f"Invalid condition value: {text!r}") from exc


def _column_map(row: dict[str, str]) -> dict[str, str]:
    return {key.strip(): (value or "").strip() for key, value in row.items() if key is not None}


def _read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        headers = [header.strip() for header in (reader.fieldnames or [])]
        rows = []
        for raw_row in reader:
            if raw_row.get(None):
                LOGGER.warning("Row has more cells than headers in %s", path.name)
            rows.append(_column_map(raw_row))
    if not rows:
        raise ValueError(f"{path} contains no experimental rows")
    return headers, rows


def _mapping_for(path: Path) -> dict[str, Any]:
    config_path = ROOT_DIR / "core" / "psi_table_map.yaml"
    if config_path.exists():
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        for mapping in raw.get("tables", []):
            if mapping.get("filename") == path.name:
                return {**mapping, "_configured": True}
    return {
        "_configured": False,
        "oxygen_columns": ["Oxygen Mole Fraction"],
        "oxygen_unit": "fraction",
        "pressure_column": "Ambient Pressure (atm)",
        "pressure_unit": "atm",
        "flow_column": "Flow Velocity (cm/s)",
    }


def _provenance(
    filename: str,
    psi_ref: str,
    *,
    conversion: str | None = None,
    source_kind: str = "table",
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "reported",
        "source": f"{filename}; PSI id {psi_ref}",
        "source_kind": source_kind,
    }
    if conversion:
        result["conversion"] = conversion
    return result


def _derived_provenance(filename: str, psi_ref: str) -> dict[str, str]:
    return {
        "status": "derived",
        "source": f"{filename}; derived from file name; PSI id {psi_ref}",
    }


def _partial_provenance(
    filename: str,
    psi_ref: str,
    invalid: list[str],
    conversion: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "partial",
        "source": f"{filename}; PSI id {psi_ref}; unparsed cells: {invalid}",
        "source_kind": "table",
    }
    if conversion:
        result["conversion"] = conversion
    return result


def _unique(values: list[Any]) -> list[Any]:
    return list(dict.fromkeys(values))


def _condition_values(condition: ParsedCondition) -> list[float]:
    return list(condition.values) if condition.kind in {"list", "single"} else []


def _converter(unit: str | None) -> tuple[Callable[[float], float] | None, str | None]:
    if unit == "fraction":
        return oxygen_mole_fraction_to_pct, "mole fraction times 100"
    if unit == "percent":
        return None, "source already in percent; no conversion"
    if unit == "atm":
        return atm_to_psi, "atm times 14.696"
    if unit == "mmHg":
        return mmhg_to_psi, "mmHg times 14.696/760"
    if unit == "bar":
        return bar_to_psi, "bar times 14.5037738"
    return None, None


def _cells(rows: list[dict[str, str]], columns: list[str]) -> list[str]:
    return _unique(
        [
            row[column]
            for column in columns
            for row in rows
            if row.get(column, "")
        ]
    )


def _record_numeric(
    cells: list[str],
    converter: Callable[[float], float] | None,
    record: dict[str, Any],
    provenance: dict[str, Any],
    extra: dict[str, Any],
    path: Path,
    psi_ref: str,
    values_field: str | None,
    minimum_field: str,
    maximum_field: str,
    original_key: str,
    conversion: str | None,
    source_kind: str,
) -> list[ParsedCondition]:
    parsed: list[ParsedCondition] = []
    invalid: list[str] = []
    for cell in cells:
        normalized_cell = re.sub(
            r"\s*(?:atm|bar|mmhg|cm/s)\s*$", "", cell, flags=re.IGNORECASE
        ).strip()
        try:
            condition = parse_condition_cell(normalized_cell)
            endpoints = (
                condition.values
                if condition.kind in {"list", "single"}
                else (condition.minimum, condition.maximum)
            )
            if minimum_field.startswith("flow_velocity") and any(
                value is not None and value < 0 for value in endpoints
            ):
                invalid.append(cell)
            else:
                parsed.append(condition)
        except ValueError:
            invalid.append(cell)
    if invalid:
        extra[original_key] = invalid if len(invalid) > 1 else invalid[0]
        aliases = {
            "o2_chamber_original": "Oxygen Mole Fraction",
            "pressure_original": "Ambient Pressure (atm)",
        }
        if original_key in aliases:
            extra[aliases[original_key]] = extra[original_key]
        LOGGER.warning(
            "Could not parse %s value(s) %r in %s",
            aliases.get(original_key, original_key),
            invalid,
            path.name,
        )
    endpoints = [
        endpoint
        for condition in parsed
        for endpoint in (
            condition.values
            if condition.kind in {"list", "single"}
            else (condition.minimum, condition.maximum)
        )
    ]
    values = [
        value
        for condition in parsed
        for value in _condition_values(condition)
    ]
    if values and values_field:
        record[values_field] = _unique(
            [converter(value) if converter else value for value in values]
        )
        provenance[values_field] = (
            _partial_provenance(path.name, psi_ref, invalid, conversion)
            if invalid
            else _provenance(
                path.name, psi_ref, conversion=conversion, source_kind=source_kind
            )
        )
    if endpoints:
        record[minimum_field] = converter(min(endpoints)) if converter else min(endpoints)
        record[maximum_field] = converter(max(endpoints)) if converter else max(endpoints)
        for field in (minimum_field, maximum_field):
            provenance[field] = (
                _partial_provenance(path.name, psi_ref, invalid, conversion)
                if invalid
                else _provenance(
                    path.name, psi_ref, conversion=conversion, source_kind=source_kind
                )
            )
    if cells:
        provenance[original_key] = (
            _partial_provenance(path.name, psi_ref, invalid, conversion)
            if invalid
            else _provenance(path.name, psi_ref, source_kind=source_kind)
        )
        if original_key == "pressure_original":
            record[original_key] = "; ".join(cells)
    return parsed


def _scalar_fields(
    rows: list[dict[str, str]],
    mapping: dict[str, Any],
    record: dict[str, Any],
    provenance: dict[str, Any],
    extra: dict[str, Any],
    path: Path,
    psi_ref: str,
) -> None:
    fuel_values = _cells(rows, ["Sample (Fuel Type)", "Fuel"])
    if fuel_values:
        record["fuels"] = fuel_values
        provenance["fuels"] = _provenance(path.name, psi_ref)
    ambient_values = _cells(rows, ["Ambient Gas Mixture"])
    if ambient_values:
        record["ambient_gas"] = "; ".join(ambient_values)
        extra["ambient_gas"] = ambient_values
        provenance["ambient_gas"] = _provenance(path.name, psi_ref)
    temperature_values = _cells(rows, ["Ambient Temperature (C)"])
    if temperature_values:
        if len(temperature_values) > 1:
            extra["ambient_temp_c"] = temperature_values
        else:
            try:
                record["ambient_temp_c"] = float(temperature_values[0])
                provenance["ambient_temp_c"] = _provenance(path.name, psi_ref)
            except ValueError:
                extra["ambient_temp_c"] = temperature_values[0]
    flow_column = mapping.get("flow_column")
    if flow_column:
        flow_cells = _cells(rows, [flow_column])
        _record_numeric(
            flow_cells,
            None,
            record,
            provenance,
            extra,
            path,
            psi_ref,
            None,
            "flow_velocity_min_cm_s",
            "flow_velocity_max_cm_s",
            "flow_velocity_original",
            None,
            "table",
        )


def _extra_columns(
    headers: list[str],
    rows: list[dict[str, str]],
    mapping: dict[str, Any],
    extra: dict[str, Any],
    provenance: dict[str, Any],
    path: Path,
    psi_ref: str,
) -> None:
    mapped = set(mapping.get("oxygen_columns", []))
    mapped.update(
        {
            "Sample (Fuel Type)",
            "Fuel",
            "Ambient Gas Mixture",
            "Ambient Temperature (C)",
            mapping.get("pressure_column"),
            mapping.get("flow_column"),
        }
    )
    mapped.discard(None)
    outcome_columns = [
        column
        for column in headers
        if any(
            token in column.lower()
            for token in (
                "burn",
                "burning rate",
                "extinction",
                "flame",
                "spread",
                "co",
                "co2",
                "smoke",
            )
        )
    ]
    if outcome_columns:
        extra["outcome_columns"] = outcome_columns
        provenance["outcome_columns"] = _provenance(path.name, psi_ref)
    for column in headers:
        values = _unique([row.get(column, "") for row in rows if row.get(column, "")])
        if values and column not in mapped:
            extra[column] = values if len(values) > 1 else values[0]
            provenance[f"extra_conditions.{column}"] = _provenance(path.name, psi_ref)
    if not mapping.get("_configured") and "Oxygen Mole Fraction" not in headers:
        LOGGER.warning("Expected mapped column %r is missing from %s", "Oxygen Mole Fraction", path.name)
    if not mapping.get("_configured") and "Ambient Pressure (atm)" not in headers:
        LOGGER.warning("Expected mapped column %r is missing from %s", "Ambient Pressure (atm)", path.name)
    if not mapping.get("_configured") and "Flow Velocity (cm/s)" not in headers:
        LOGGER.warning("Expected mapped column %r is missing from %s", "Flow Velocity (cm/s)", path.name)
    aliases = {
        "Sample (Fuel Type)": "fuel",
        "Initial Droplet Diameter (mm)": "droplet_diameter_mm",
        "Ambient Gas Mixture": "ambient_gas",
        "Oxygen Mole Fraction": "o2_chamber_original",
        "Ambient Pressure (atm)": "pressure_original",
        "Ambient Temperature (C)": "ambient_temp_c",
        "Flow Velocity (cm/s)": "flow_velocity_original",
    }
    extra["rows"] = [
        {
            aliases.get(column, re.sub(r"[^a-z0-9]+", "_", column.lower()).strip("_")): value
            for column, value in row.items()
            if value
        }
        for row in rows
        if any(row.values())
    ]
    provenance["rows"] = _provenance(path.name, psi_ref)


def _droplet_conditions(
    rows: list[dict[str, str]],
    extra: dict[str, Any],
    provenance: dict[str, Any],
    path: Path,
    psi_ref: str,
) -> None:
    cells = _unique(
        [
            row["Initial Droplet Diameter (mm)"]
            for row in rows
            if row.get("Initial Droplet Diameter (mm)")
        ]
    )
    values: list[str] = []
    for cell in cells:
        try:
            condition = parse_condition_cell(cell)
        except ValueError:
            values.append(cell)
        else:
            if condition.kind in {"list", "single"}:
                values.extend(str(value) for value in condition.values)
            else:
                values.append(cell)
    if values:
        extra["initial_droplet_diameter_mm"] = _unique(values)
        provenance["initial_droplet_diameter_mm"] = _provenance(path.name, psi_ref)


def _assemble_record(
    record: dict[str, Any],
    provenance: dict[str, Any],
    extra: dict[str, Any],
    parsed_conditions: tuple[list[ParsedCondition], list[ParsedCondition]],
    path: Path,
    psi_ref: str,
) -> Experiment:
    oxygen_conditions, pressure_conditions = parsed_conditions
    record["conditions_discrete"] = any(
        any(condition.kind == "list" for condition in conditions)
        or len(
            _unique(
                [
                    value
                    for condition in conditions
                    for value in _condition_values(condition)
                ]
            )
        )
        > 1
        for conditions in (oxygen_conditions, pressure_conditions)
    )
    provenance["conditions_discrete"] = _derived_provenance(path.name, psi_ref)
    record["extra_conditions"] = json.dumps(extra, separators=(",", ":"))
    record["provenance"] = json.dumps(provenance, separators=(",", ":"))
    return Experiment.model_validate(record)


def load_psi_table(csv_path: str | Path, slug: str, psi_ref: str) -> Experiment:
    """Load one PSI CSV table into the normalized experiment schema."""
    path = Path(csv_path)
    headers, rows = _read_rows(path)
    mapping = _mapping_for(path)
    provenance: dict[str, Any] = {}
    extra: dict[str, Any] = {"table_mapping": mapping}
    record: dict[str, Any] = {
        "id": psi_ref.lower(),
        "slug": slug,
        "name": slug.replace("_", " ").replace("-", " ").title(),
        "psi_ref": psi_ref,
        "data_status": "from_psi",
    }
    for field in ("id", "slug", "name"):
        provenance[field] = _derived_provenance(path.name, psi_ref)
    provenance["psi_ref"] = _provenance(path.name, psi_ref)
    _scalar_fields(rows, mapping, record, provenance, extra, path, psi_ref)

    oxygen_columns = mapping.get("oxygen_columns", [])
    oxygen_converter, oxygen_conversion = _converter(mapping.get("oxygen_unit"))
    oxygen_role = mapping.get("oxygen_role", "chamber")
    oxygen_field = (
        "o2_stream_values_pct" if oxygen_role == "stream" else "o2_chamber_values_pct"
    )
    oxygen_min = (
        "o2_stream_min_pct" if oxygen_role == "stream" else "o2_chamber_min_pct"
    )
    oxygen_max = (
        "o2_stream_max_pct" if oxygen_role == "stream" else "o2_chamber_max_pct"
    )
    oxygen = _record_numeric(
        _cells(rows, oxygen_columns),
        oxygen_converter,
        record,
        provenance,
        extra,
        path,
        psi_ref,
        oxygen_field,
        oxygen_min,
        oxygen_max,
        "o2_stream_original" if oxygen_role == "stream" else "o2_chamber_original",
        oxygen_conversion,
        "table",
    )
    if oxygen_role == "stream":
        record["o2_stream_note"] = "Source table oxygen is a stream value, not chamber atmosphere."
        extra["oxygen_role"] = "stream"

    pressure_column = mapping.get("pressure_column")
    pressure_converter, pressure_conversion = _converter(mapping.get("pressure_unit"))
    if pressure_column and mapping.get("pressure_unit") not in {"atm", "mmHg", "bar"}:
        raise ValueError(
            f"Unknown pressure unit {mapping.get('pressure_unit')!r} in {path.name}"
        )
    pressure = _record_numeric(
        _cells(rows, [pressure_column]) if pressure_column else [],
        pressure_converter,
        record,
        provenance,
        extra,
        path,
        psi_ref,
        "pressure_values_psi",
        "pressure_min_psi",
        "pressure_max_psi",
        "pressure_original",
        pressure_conversion,
        "table",
    )
    if pressure_column and _cells(rows, [pressure_column]):
        record["pressure_original_unit"] = mapping["pressure_unit"]
        provenance["pressure_original_unit"] = _provenance(path.name, psi_ref)
    _extra_columns(headers, rows, mapping, extra, provenance, path, psi_ref)
    _droplet_conditions(rows, extra, provenance, path, psi_ref)
    return _assemble_record(record, provenance, extra, (oxygen, pressure), path, psi_ref)
