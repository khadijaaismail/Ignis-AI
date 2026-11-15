"""Generate a read-only exploratory data analysis report for NASA PSI data."""

from __future__ import annotations

import csv
import io
import json
import math
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS_PATH = ROOT / "data" / "processed" / "experiments.csv"
TABLES_DIR = ROOT / "data" / "raw" / "psi_tables"
CHUNKS_PATH = ROOT / "data" / "processed" / "chunks.parquet"
DISCREPANCIES_PATH = ROOT / "docs" / "discrepancies.md"
REPORT_PATH = ROOT / "docs" / "eda_report.md"
NUMBER_PATTERN = re.compile(
    r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
)
PSI_PATTERN = re.compile(r"(PSI-\d+)", re.IGNORECASE)
MISSING_MARKERS = frozenset({"", "na", "n/a", "nan", "null", "none", "not reported"})
OUTCOME_PATTERN = re.compile(
    r"\b(?:burn(?:ing)?|extinction|flame|spread|smoke|soot|emission|co2?)\b",
    re.IGNORECASE,
)
NUMERIC_CELL_PATTERN = re.compile(
    rf"^\s*(?P<number>{NUMBER_PATTERN.pattern})\s*"
    r"(?:%|atm|bar|mmhg|psi|psia|pa|kpa|cm/?s|mm/?s|mm|cm|m|ppm|"
    r"deg(?:rees?)?\s*[ck]|[ck]|s|min(?:ute)?s?|w)?\s*$",
    re.IGNORECASE,
)
CELL_UNIT_PATTERN = re.compile(
    r"^\s*" + NUMBER_PATTERN.pattern
    + r"\s*(?P<unit>%|atm|bar|mmhg|psi|psia|pa|kpa|cm/?s|mm/?s|mm|cm|m|ppm|"
    r"deg(?:rees?)?\s*[ck]|[ck]|s|min(?:ute)?s?|w)?\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TableData:
    """Raw rows and ingestion diagnostics from one PSI table."""

    path: Path
    headers: list[str]
    rows: list[dict[str, str]]
    psi_ref: str | None
    issues: tuple[str, ...] = ()
    encoding: str = "utf-8-sig"


@dataclass(frozen=True)
class NumericProfile:
    """General profile with optional descriptive statistics for one raw column."""

    table: str
    psi_ref: str
    column: str
    count: int
    missing: int
    missing_pct: float
    unparseable: int
    minimum: float | None
    maximum: float | None
    mean: float | None
    median: float | None
    std_dev: float | None
    unique_count: int
    unique_values: str
    data_type: str
    unit: str
    flags: str


def _is_missing(value: str) -> bool:
    """Treat blank and explicit missing markers as missing; zero is reported."""
    return value.strip().casefold() in MISSING_MARKERS


def _read_text(path: Path) -> tuple[str, str, str | None]:
    """Read UTF-8 CSV text, falling back to latin-1 with a visible issue."""
    try:
        return path.read_text(encoding="utf-8-sig"), "utf-8-sig", None
    except UnicodeDecodeError:
        try:
            return (
                path.read_text(encoding="latin-1"),
                "latin-1",
                "unexpected encoding; decoded with latin-1",
            )
        except (OSError, UnicodeError) as exc:
            raise ValueError(f"Unable to decode CSV {path}: {exc}") from exc


def read_csv_table(path: Path) -> TableData:
    """Read one CSV while retaining rows and reporting malformed input."""
    _set_csv_field_size_limit()
    if not path.exists():
        raise FileNotFoundError(f"Required CSV does not exist: {path}")
    text, encoding, encoding_issue = _read_text(path)
    issues = [encoding_issue] if encoding_issue else []
    if not text.strip():
        issues.append("empty CSV file")
        return TableData(path, [], [], _psi_ref(path), tuple(issues), encoding)
    try:
        reader = csv.reader(io.StringIO(text, newline=""))
        raw_headers = next(reader, [])
        headers = [header.strip() if header is not None else "" for header in raw_headers]
        normalized = [re.sub(r"\s+", " ", header).casefold() for header in headers]
        if any(not header for header in headers):
            issues.append("blank header(s) found")
        seen: dict[str, int] = {}
        output_headers: list[str] = []
        for index, (header, normalized_header) in enumerate(zip(headers, normalized), 1):
            if normalized_header:
                seen[normalized_header] = seen.get(normalized_header, 0) + 1
                occurrence = seen[normalized_header]
            else:
                occurrence = 1
            if occurrence > 1:
                issues.append(
                    f"duplicate header after whitespace normalization: {header!r}"
                )
                output_headers.append(f"{header} [duplicate {occurrence}]")
            elif not normalized_header:
                output_headers.append(f"[blank header {index}]")
            else:
                output_headers.append(header)
        headers = output_headers
        if not headers:
            issues.append("header-only CSV with no header row")
            return TableData(path, [], [], _psi_ref(path), tuple(issues), encoding)
        rows: list[dict[str, str]] = []
        for raw_values in reader:
            line_number = reader.line_num
            if len(raw_values) > len(raw_headers):
                issues.append(f"malformed row at line {line_number}: extra fields")
            if len(raw_values) < len(raw_headers):
                issues.append(f"malformed row at line {line_number}: missing fields")
            row = {}
            for index, output_key in enumerate(headers):
                row[output_key] = (
                    raw_values[index].strip() if index < len(raw_values) else ""
                )
            rows.append(row)
    except (csv.Error, UnicodeError) as exc:
        issues.append(f"malformed CSV: {exc}")
        headers, rows = [], []
    if not rows:
        issues.append("header-only CSV with no data rows")
    return TableData(path, headers, rows, _psi_ref(path), tuple(issues), encoding)


def _set_csv_field_size_limit() -> None:
    """Set the largest field limit supported by the current platform."""
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit //= 2


def _psi_ref(path: Path) -> str | None:
    match = PSI_PATTERN.search(path.name)
    return match.group(1).upper() if match else None


def discover_csv_paths(directory: Path = TABLES_DIR) -> list[Path]:
    """Discover CSV files recursively without combining source files."""
    if not directory.exists():
        raise FileNotFoundError(f"Required PSI CSV directory does not exist: {directory}")
    return sorted(path for path in directory.rglob("*.csv") if path.is_file())


def load_tables(directory: Path = TABLES_DIR) -> list[TableData]:
    """Load every discovered raw PSI CSV without writing to source directories."""
    paths = discover_csv_paths(directory)
    if not paths:
        raise FileNotFoundError(f"No PSI CSV files found under {directory}")
    return [read_csv_table(path) for path in paths]


def _source_ids(
    tables: Iterable[TableData], directory: Path = TABLES_DIR
) -> dict[Path, str]:
    """Return source IDs relative to the table directory."""
    table_list = list(tables)
    if not table_list:
        return {}
    resolved_directory = directory.resolve()
    identifiers: dict[Path, str] = {}
    unresolved: list[Path] = []
    for table in table_list:
        path = table.path
        if not path.is_absolute():
            identifiers[path] = path.as_posix()
            continue
        try:
            identifiers[path] = path.resolve().relative_to(resolved_directory).as_posix()
        except ValueError:
            unresolved.append(path)
    if unresolved:
        if len(unresolved) == 1:
            common_root = unresolved[0].resolve().parent
        else:
            common_root = Path(
                os.path.commonpath([str(path.resolve()) for path in unresolved])
            )
        for path in unresolved:
            identifiers[path] = path.resolve().relative_to(common_root).as_posix()
    return identifiers


def numeric_values(values: Iterable[str]) -> tuple[list[float], int]:
    """Return finite numbers and cell-level missing/unparseable count."""
    parsed: list[float] = []
    missing = 0
    for value in values:
        text = value.strip()
        if _is_missing(text):
            missing += 1
            continue
        match = NUMERIC_CELL_PATTERN.fullmatch(text)
        if not match:
            missing += 1
            continue
        number = float(match.group("number"))
        if math.isfinite(number):
            parsed.append(number)
        else:
            missing += 1
    return parsed, missing


def _cell_unit(value: str) -> str | None:
    match = CELL_UNIT_PATTERN.fullmatch(value)
    if not match:
        return None
    unit = match.group("unit")
    if not unit:
        return None
    lowered = unit.casefold().replace(" ", "")
    return {
        "%": "%",
        "psia": "psia",
        "psi": "psi",
        "mmhg": "mmHg",
        "kpa": "kPa",
        "atm": "atm",
        "bar": "bar",
        "pa": "Pa",
        "cm/s": "cm/s",
        "cms": "cm/s",
        "mm/s": "mm/s",
        "mms": "mm/s",
        "ppm": "ppm",
        "c": "deg C",
        "degc": "deg C",
        "degrees c": "deg C",
        "k": "K",
        "degk": "K",
        "degrees k": "K",
        "s": "s",
        "min": "min",
        "minutes": "min",
        "minute": "min",
        "m": "m",
        "cm": "cm",
        "mm": "mm",
        "w": "W",
    }.get(lowered, unit)


def _unit_validation(values: list[str], declared_unit: str) -> tuple[set[str], list[str]]:
    explicit_units = {_cell_unit(value) for value in values if _cell_unit(value)}
    flags: list[str] = []
    if len(explicit_units) > 1:
        flags.append("mixed explicit cell units")
    if declared_unit != "not stated":
        mismatched = sorted(unit for unit in explicit_units if unit != declared_unit)
        if mismatched:
            flags.append(
                f"cell units inconsistent with declared unit {declared_unit}: "
                + ", ".join(mismatched)
            )
    return {unit for unit in explicit_units if unit}, flags


def column_unit(column: str) -> str:
    """Infer a unit only when the source column explicitly names that unit."""
    lowered = column.casefold()
    explicit_units = (
        (("mole fraction",), "mole fraction"),
        (("%", "percent", "by vol"), "%"),
        (("mmhg",), "mmHg"),
        (("psia",), "psia"),
        (("psi",), "psi"),
        (("kpa",), "kPa"),
        (("atm",), "atm"),
        (("bar",), "bar"),
        (("cm/s", "cm s"), "cm/s"),
        (("mm/s", "mm s"), "mm/s"),
        (("(ppm)", "ppm"), "ppm"),
        (("(c)", "deg c", "degrees c"), "deg C"),
        (("(k)", "deg k", "degrees k"), "K"),
        (("(s)", " sec", " second", "seconds"), "s"),
        (("(min)", "minute", "minutes"), "min"),
        (("(mm)", " mm"), "mm"),
    )
    for markers, unit in explicit_units:
        if any(marker in lowered for marker in markers):
            return unit
    return "not stated"


def column_flags(column: str, values: list[float], unit: str) -> list[str]:
    """Return cautious review flags without declaring source values invalid."""
    lowered = column.casefold()
    flags: list[str] = []
    if ("o2" in lowered or "oxygen" in lowered) and unit == "%" and any(
        value > 100 for value in values
    ):
        flags.append("manual review: O2 > 100%")
    if ("air" in lowered or "flow" in lowered or "velocity" in lowered) and any(
        value < 0 for value in values
    ):
        flags.append("manual review: negative airflow")
    if "pressure" in lowered and any(value == 0 for value in values):
        flags.append("manual review: zero pressure")
    return flags


def _data_type(values: list[str], column: str = "") -> str:
    nonmissing = [value for value in values if not _is_missing(value)]
    if not nonmissing:
        return "missing"
    lowered = column.casefold().strip()
    if any(token in lowered for token in ("doi", "url", "reference", "citation")):
        return "reference"
    if lowered in {"id", "slug", "psi_ref", "experiment_id", "investigation_id"} or (
        lowered.endswith("_id") or lowered.endswith("_slug")
    ):
        return "identifier"
    parsed, _ = numeric_values(nonmissing)
    if len(parsed) == len(nonmissing):
        return "numeric"
    if all(value.casefold() in {"yes", "no", "true", "false"} for value in nonmissing):
        return "boolean-like"
    if any(marker in column.casefold() for marker in ("note", "description", "comment", "text")):
        return "text"
    unique_count = len(set(nonmissing))
    if unique_count <= 20 or unique_count <= max(1, len(nonmissing) // 5):
        return "categorical"
    return "text"


def _unique_summary(values: list[str]) -> str:
    unique = list(dict.fromkeys(value for value in values if not _is_missing(value)))
    rendered = [value.replace("|", "\\|") for value in unique[:8]]
    suffix = " ..." if len(unique) > 8 else ""
    return ", ".join(rendered) + suffix if rendered else "Not reported"


def profile_tables(
    tables: Iterable[TableData], directory: Path = TABLES_DIR
) -> list[NumericProfile]:
    """Profile every column independently for each source file."""
    table_list = list(tables)
    source_ids = _source_ids(table_list, directory)
    profiles: list[NumericProfile] = []
    for table in table_list:
        for column in table.headers:
            raw_values = [row.get(column, "") for row in table.rows]
            values, unparseable_total = numeric_values(raw_values)
            missing = sum(_is_missing(value) for value in raw_values)
            data_type = _data_type(raw_values, column)
            unit = column_unit(column)
            explicit_units, unit_flags = _unit_validation(raw_values, unit)
            incompatible_units = len(explicit_units) > 1 or any(
                explicit_unit != unit for explicit_unit in explicit_units
            ) and unit != "not stated"
            series = (
                pd.Series(values, dtype="float64")
                if data_type == "numeric" and not incompatible_units
                else None
            )
            flags = column_flags(column, values, unit) if data_type == "numeric" else []
            flags.extend(unit_flags)
            if incompatible_units:
                flags.append("descriptive statistics withheld due to unit inconsistency")
            profiles.append(
                NumericProfile(
                    table=source_ids[table.path],
                    psi_ref=table.psi_ref or "Unknown",
                    column=column,
                    count=len(raw_values) - missing,
                    missing=missing,
                    missing_pct=round(100 * missing / len(raw_values), 2)
                    if raw_values
                    else 0.0,
                    unparseable=max(0, unparseable_total - missing),
                    minimum=float(series.min()) if series is not None else None,
                    maximum=float(series.max()) if series is not None else None,
                    mean=float(series.mean()) if series is not None else None,
                    median=float(series.median()) if series is not None else None,
                    std_dev=(
                        float(series.std(ddof=1))
                        if series is not None and len(series) > 1
                        else 0.0 if series is not None else None
                    ),
                    unique_count=len(
                        {value for value in raw_values if not _is_missing(value)}
                    ),
                    unique_values=_unique_summary(raw_values),
                    data_type=data_type,
                    unit=unit,
                    flags=", ".join(flags) or "none",
                )
            )
    return profiles


def outcome_columns(
    tables: Iterable[TableData], directory: Path = TABLES_DIR
) -> dict[str, set[str]]:
    """Collect outcome columns per source file, using word-aware matching."""
    table_list = list(tables)
    source_ids = _source_ids(table_list, directory)
    outcomes: dict[str, set[str]] = defaultdict(set)
    for table in table_list:
        key = source_ids[table.path]
        for column in table.headers:
            if OUTCOME_PATTERN.search(column):
                outcomes[key].add(column)
    return outcomes


def display_value(row: dict[str, str], field: str) -> str:
    """Format a normalized experiment field while keeping empty values explicit."""
    value = row.get(field, "").strip()
    if _is_missing(value):
        return "Not reported"
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return value
    if isinstance(decoded, list):
        return ", ".join(str(item) for item in decoded) or "Not reported"
    return str(decoded)


def first_display_value(row: dict[str, str], fields: Iterable[str]) -> str:
    """Display the first reported field, or an explicit missing marker."""
    for field in fields:
        if row.get(field, "").strip() and not _is_missing(row.get(field, "")):
            return display_value(row, field)
    return "Not reported"


def _discrepancy_refs_with_issue() -> tuple[set[str], str | None]:
    """Read investigation references from the optional discrepancy log."""
    try:
        text = DISCREPANCIES_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return set(), None
    except (OSError, UnicodeError) as exc:
        return set(), f"Optional discrepancies log could not be read: {exc}"
    return {
        match.group(1).upper()
        for match in PSI_PATTERN.finditer(text)
    }, None


def discrepancy_refs() -> set[str]:
    """Read investigation references from the optional discrepancy log."""
    refs, _ = _discrepancy_refs_with_issue()
    return refs


def chunk_counts() -> tuple[dict[str, int], str | None]:
    """Count optional processed chunks, returning a reportable issue if unavailable."""
    if not CHUNKS_PATH.exists():
        return {}, f"Optional file not available: {CHUNKS_PATH}"
    try:
        frame = pd.read_parquet(CHUNKS_PATH, columns=["experiment_slug"])
        counts = frame["experiment_slug"].dropna().astype(str).value_counts()
        return {slug: int(count) for slug, count in counts.items()}, None
    except (OSError, KeyError, ImportError, ValueError) as exc:
        return {}, f"Optional chunks file could not be read: {exc}"


def markdown_table(headers: list[str], rows: Iterable[Iterable[object]]) -> str:
    """Render a markdown table with escaped cell content."""
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        values = [str(value).replace("|", "\\|").replace("\n", "<br>") for value in row]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


REQUIRED_EXPERIMENT_COLUMNS = frozenset(
    {
        "slug",
        "psi_ref",
        "investigation_type",
        "include_in_ranking",
        "gravity_regime",
        "conditions_status",
    }
)


def _required_experiments() -> list[dict[str, str]]:
    if not EXPERIMENTS_PATH.exists():
        raise FileNotFoundError(f"Required experiments file does not exist: {EXPERIMENTS_PATH}")
    try:
        _set_csv_field_size_limit()
        with EXPERIMENTS_PATH.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            missing = sorted(REQUIRED_EXPERIMENT_COLUMNS - set(reader.fieldnames or []))
            if missing:
                raise ValueError(
                    "experiments.csv is missing required columns: " + ", ".join(missing)
                )
            return list(reader)
    except (OSError, csv.Error, UnicodeError) as exc:
        raise ValueError(f"Unable to read required experiments file: {exc}") from exc


def build_report() -> str:
    """Load source data and build the complete markdown report."""
    experiments = _required_experiments()
    tables = load_tables()
    source_ids = _source_ids(tables)
    outcomes = outcome_columns(tables)
    conflicts, discrepancy_issue = _discrepancy_refs_with_issue()
    chunks, chunk_issue = chunk_counts()
    profiles = profile_tables(tables)
    tables_by_ref: dict[str, list[TableData]] = defaultdict(list)
    for table in tables:
        if table.psi_ref:
            tables_by_ref[table.psi_ref].append(table)
    duplicate_rows = {
        source_ids[table.path]: len(table.rows)
        - len({tuple(row.get(h, "") for h in table.headers) for row in table.rows})
        for table in tables
    }
    missing_chunks = (
        [
            experiment.get("slug", "")
            for experiment in experiments
            if chunks.get(experiment.get("slug", ""), 0) == 0
        ]
        if chunk_issue is None
        else []
    )
    lines = [
        "# EDA report",
        "",
        "Generated read-only from `data/processed/experiments.csv` and each discovered "
        "CSV under `data/raw/psi_tables/`. Blank cells and explicit markers "
        "(`NA`, `N/A`, `null`, `not reported`) are missing; numeric zero is never missing. "
        "Source rows are not removed or rewritten.",
        "",
        "## Source-file integrity",
        "",
        markdown_table(
            ["Source path", "Investigation reference", "Rows", "Duplicate rows", "Issues"],
            (
                (
                    source_ids[table.path],
                    table.psi_ref or "Unknown",
                    len(table.rows),
                    duplicate_rows[source_ids[table.path]],
                    "; ".join(table.issues) or "none",
                )
                for table in tables
            ),
        ),
        "",
        "## Completeness matrix",
        "",
        markdown_table(
            [
                "Investigation", "Investigation type", "Include in ranking",
                "Chamber O2", "Burner-stream O2", "Pressure", "Airflow",
                "Gravity regime", "Safety focus", "Conditions status", "Test rows",
                "Outcome column names", "Conflicts",
            ],
            (
                (
                    experiment.get("slug", ""),
                    display_value(experiment, "investigation_type"),
                    display_value(experiment, "include_in_ranking"),
                    first_display_value(
                        experiment, ("o2_chamber_values_pct", "o2_chamber_min_pct")
                    ),
                    first_display_value(
                        experiment, ("o2_stream_values_pct", "o2_stream_min_pct")
                    ),
                    first_display_value(
                        experiment, ("pressure_values_psi", "pressure_min_psi")
                    ),
                    first_display_value(experiment, ("flow_velocity_min_cm_s",)),
                    display_value(experiment, "gravity_regime"),
                    display_value(experiment, "safety_focus"),
                    display_value(experiment, "conditions_status"),
                    "; ".join(
                        f"{source_ids[table.path]}: {len(table.rows)} rows"
                        for table in tables_by_ref.get(
                            experiment.get("psi_ref", "").upper(), []
                        )
                    )
                    or "Not reported",
                    ", ".join(
                        sorted(
                            {
                                f"{source_ids[table.path]}: {column}"
                                for table in tables_by_ref.get(
                                    experiment.get("psi_ref", "").upper(), []
                                )
                                for column in outcomes.get(source_ids[table.path], set())
                            }
                        )
                    )
                    or "Not reported",
                    "yes"
                    if experiment.get("psi_ref", "").upper() in conflicts
                    else "no",
                )
                for experiment in experiments
            ),
        ),
        "",
        "## Column profiles",
        "",
        markdown_table(
            [
                "Source path", "Investigation reference", "Column", "Type", "Count",
                "Missing", "Missing %", "Unique", "Unique values",
            ],
            (
                (
                    profile.table, profile.psi_ref, profile.column, profile.data_type,
                    profile.count, profile.missing, profile.missing_pct,
                    profile.unique_count, profile.unique_values,
                )
                for profile in profiles
            ),
        ),
        "",
        "## Numeric profiles",
        "",
        markdown_table(
            [
                "Source path", "Investigation reference", "Column", "Count", "Missing",
                "Missing %", "Unparseable", "Min", "Max", "Mean", "Median", "Std dev",
                "Unit", "Flags",
            ],
            (
                (
                    profile.table, profile.psi_ref, profile.column, profile.count,
                    profile.missing, profile.missing_pct, profile.unparseable,
                    profile.minimum, profile.maximum, profile.mean, profile.median,
                    profile.std_dev, profile.unit, profile.flags,
                )
                for profile in profiles
                if profile.data_type == "numeric"
            ),
        ),
        "",
        "## Outcome columns by source file",
        "",
        markdown_table(
            ["Source path", "Investigation reference", "Outcome columns"],
            (
                (source_ids[table.path], table.psi_ref or "Unknown",
                 ", ".join(sorted(outcomes.get(source_ids[table.path], set()))) or "Not reported")
                for table in tables
            ),
        ),
        "",
        "## Optional inputs and processing notes",
        "",
        f"- {chunk_issue or 'Optional chunks.parquet loaded successfully.'}",
        f"- Optional discrepancies log: {discrepancy_issue or ('loaded.' if DISCREPANCIES_PATH.exists() else 'not available.')}",
        f"- Investigations with no chunks: {', '.join(missing_chunks) if chunk_issue is None and missing_chunks else ('none' if chunk_issue is None else 'not assessed; optional chunks file unavailable.')}",
        f"- Discrepancy references: {', '.join(sorted(conflicts)) if conflicts else 'none'}",
        "",
        "## Investigation separation",
        "",
        "Statistics are calculated per source path and PSI reference. Tables sharing "
        "a PSI reference are not pooled; measurements are never compared across files "
        "without verified unit and experimental comparability.",
        "",
        "## Things to review by hand",
        "",
        f"- Numeric flags: {sum(profile.flags != 'none' for profile in profiles)} "
        "profile(s) contain requested impossible-value or placeholder flags.",
        f"- Conflicts recorded for: {', '.join(sorted(conflicts)) if conflicts else 'none'}.",
        f"- Investigations with no chunks: {', '.join(missing_chunks) if chunk_issue is None and missing_chunks else ('none' if chunk_issue is None else 'not assessed; optional chunks file unavailable.')}.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    """Write only the generated report and print it."""
    report = build_report()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report, end="")


if __name__ == "__main__":
    main()
