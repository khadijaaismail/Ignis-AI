"""Build processed NASA PSI data from curated records and source tables."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .config import ROOT_DIR, settings
from .docs_ingest import build_documents
from .psi_tables import load_psi_table
from .schema import Experiment, Scenario
from .store import (
    read_chunks,
    read_documents,
    read_experiments,
    write_chunks,
    write_documents,
    write_experiments,
    write_scenarios,
)
from .units import atm_to_psi

LOGGER = logging.getLogger(__name__)
PSI_TOKEN = re.compile(r"PSI-(?P<number>\d+)", re.IGNORECASE)
LIST_FIELDS = {
    "o2_chamber_values_pct",
    "o2_stream_values_pct",
    "pressure_values_psi",
    "materials",
    "fuels",
    "suppression_agents",
}
PRESERVED_FIELDS = {"id", "slug", "name"}
CONDITION_FIELDS = {
    "o2_chamber_values_pct",
    "o2_chamber_min_pct",
    "o2_chamber_max_pct",
    "o2_stream_values_pct",
    "o2_stream_min_pct",
    "o2_stream_max_pct",
    "pressure_values_psi",
    "pressure_min_psi",
    "pressure_max_psi",
}


def _read_seed(path: Path) -> list[Experiment]:
    """Read and validate a seed file with contextual parsing errors."""
    records: list[Experiment] = []
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        for row_number, raw_row in enumerate(reader, start=2):
            stripped = {
                key.strip(): (value or "").strip()
                for key, value in raw_row.items()
                if key is not None
            }
            slug = stripped.get("slug") or "<unknown>"
            row: dict[str, Any] = {}
            for field, text in stripped.items():
                if field in LIST_FIELDS:
                    if not text:
                        row[field] = []
                    else:
                        try:
                            row[field] = json.loads(text)
                        except json.JSONDecodeError as error:
                            raise ValueError(
                                f"{path.name} row {row_number} ({slug}): "
                                f"invalid JSON in {field}: {error.msg}"
                            ) from error
                elif text:
                    row[field] = text
            try:
                records.append(Experiment.model_validate(row))
            except ValidationError as error:
                raise ValueError(
                    f"{path.name} row {row_number} ({slug}): validation failed: {error}"
                ) from error
    return records


def _resolve_data_dir(data_dir: str | Path | None) -> Path:
    if data_dir is not None:
        return Path(data_dir)
    configured = Path(settings.data_dir)
    return configured if configured.is_absolute() else ROOT_DIR / configured


def _slug_from_filename(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _json_object(value: str, field: str) -> dict[str, Any]:
    if not value:
        return {}
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError(f"{field} must contain a JSON object")
    return parsed


def _merge_metadata(first: str, second: str, field: str) -> str:
    merged = _json_object(first, field)
    incoming = _json_object(second, field)
    for key, value in incoming.items():
        if key not in merged:
            merged[key] = value
        elif isinstance(merged[key], list) and isinstance(value, list):
            merged[key] = [
                item
                for index, item in enumerate(merged[key] + value)
                if item not in (merged[key] + value)[:index]
            ]
        elif key == "table_files":
            merged[key] = list(dict.fromkeys([*merged[key], *value]))
    return json.dumps(merged, separators=(",", ":"))


def _empty(value: Any) -> bool:
    return value is None or value == "" or value == []


def _merge_record(seed: Experiment, psi: Experiment) -> Experiment:
    """Fill missing curated values from a table without discarding provenance."""
    values = seed.model_dump()
    table_values = psi.model_dump()
    def is_empty(value: Any) -> bool:
        return value is None or value == "" or value == [] or value is False or value == "unknown"

    replaced_conditions: dict[str, Any] = {}
    for field, table_value in table_values.items():
        if field in {"data_status", "extra_conditions", "provenance"}:
            continue
        if field in PRESERVED_FIELDS:
            continue
        curated_value = values[field]
        if (
            field in CONDITION_FIELDS
            and not is_empty(table_value)
            and not is_empty(curated_value)
            and curated_value != table_value
        ):
            replaced_conditions[field] = curated_value
            values[field] = table_value
        elif field in CONDITION_FIELDS and not is_empty(table_value):
            values[field] = table_value
        elif is_empty(curated_value) and not is_empty(table_value):
            values[field] = table_value
        elif (
            field not in {"conditions_status", "include_in_ranking", "conditions_discrete"}
            and not is_empty(curated_value)
            and not is_empty(table_value)
            and curated_value != table_value
        ):
            LOGGER.warning(
                "Conflict for %s field %s: preserving curated value",
                seed.slug,
                field,
            )
        if field == "conditions_discrete":
            values[field] = values[field] or table_value
    values["data_status"] = seed.data_status if seed.data_status != "unknown" else "from_psi"
    values["extra_conditions"] = _merge_metadata(
        seed.extra_conditions, psi.extra_conditions, "extra_conditions"
    )
    if replaced_conditions:
        extra_conditions = _json_object(values["extra_conditions"], "extra_conditions")
        text_stated_range = extra_conditions.get("text_stated_range")
        if not isinstance(text_stated_range, dict):
            text_stated_range = {}
        text_stated_range.update(replaced_conditions)
        extra_conditions["text_stated_range"] = text_stated_range
        values["extra_conditions"] = json.dumps(
            extra_conditions, separators=(",", ":")
        )
    merged_provenance = _merge_metadata(
        seed.provenance, psi.provenance, "provenance"
    )
    provenance = _json_object(merged_provenance, "provenance")
    for field in PRESERVED_FIELDS:
        provenance.pop(field, None)
    table_provenance = _json_object(psi.provenance, "provenance")
    table_fields = provenance.setdefault("table_condition_fields", [])
    for field in CONDITION_FIELDS:
        if field in table_provenance and field not in table_fields:
            table_fields.append(field)
    values["provenance"] = json.dumps(provenance, separators=(",", ":"))
    return Experiment.model_validate(values)


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        return [
            {
                key.strip(): (value or "").strip()
                for key, value in row.items()
                if key is not None
            }
            for row in csv.DictReader(file)
        ]


def _split_values(value: str) -> list[str]:
    return [part.strip() for part in value.split(";") if part.strip()]


def _float_or_none(value: str, *, source_file: str, slug: str, column: str) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError as error:
        raise ValueError(
            f"Invalid number in file {source_file}, row {slug}, column {column}: {value!r}"
        ) from error


def _source_provenance(source: str, status: str = "reported") -> dict[str, str]:
    return {"status": status, "source": source, "source_file": source}


def _curated_record(row: dict[str, str], source_file: str) -> Experiment:
    psi_type = row.get("psi_type", "")
    if psi_type == "Microgravity Investigation":
        investigation_type = "flight"
    elif psi_type == "Ground Investigation":
        investigation_type = "ground"
    else:
        raise ValueError(f"Invalid psi_type for row {row.get('slug', '<unknown>')}: {psi_type!r}")
    slug = row.get("slug", "<unknown>")
    float_value = lambda column: _float_or_none(
        row.get(column, ""), source_file=source_file, slug=slug, column=column
    )
    platform = "; ".join(
        dict.fromkeys(
            value
            for value in (row.get("hardware", ""), row.get("flight_platform", ""))
            if value
        )
    )
    fuels = _split_values(row.get("fuel", ""))
    pressure_original = "; ".join(
        value
        for value in (row.get("pressure_min_atm", ""), row.get("pressure_max_atm", ""))
        if value
    ) or None
    pressure_unit = "atm" if pressure_original else None
    pressure_min_psi = float_value("pressure_min_psi")
    pressure_max_psi = float_value("pressure_max_psi")
    if pressure_min_psi is None:
        pressure_min_psi = (
            atm_to_psi(float(row["pressure_min_atm"]))
            if float_value("pressure_min_atm") is not None
            else None
        )
    if pressure_max_psi is None:
        pressure_max_psi = (
            atm_to_psi(float(row["pressure_max_atm"]))
            if float_value("pressure_max_atm") is not None
            else None
        )
    if row.get("pressure_min_psi") or row.get("pressure_max_psi"):
        pressure_unit = "psia"
    gravity = "microgravity" if investigation_type == "flight" and row.get("gravity_regime") == "microgravity" else "unknown"
    extra = {
        "curated_record": dict(row),
        "conditions_basis": row.get("conditions_basis", ""),
    }
    if row.get("conditions_basis"):
        extra["text_stated_range"] = row["conditions_basis"]
    provenance = {
        field: _source_provenance(source_file)
        for field, value in row.items()
        if value
    }
    if pressure_original and not (row.get("pressure_min_psi") or row.get("pressure_max_psi")):
        for field, value in (
            ("pressure_min_psi", pressure_min_psi),
            ("pressure_max_psi", pressure_max_psi),
        ):
            if value is not None:
                provenance[field] = {
                    "status": "derived",
                    "source": f"{source_file}; converted from curated atm",
                    "source_file": source_file,
                    "conversion": "atm times 14.696",
                }
    provenance["gravity_regime"] = {
        "status": "reported_label_not_confirmed",
        "source": (
            "reported: PSI project type label; not confirmed from science documents"
            if investigation_type == "flight"
            else f"{source_file}; ground investigation has unknown gravity"
        ),
    }
    provenance["condition_sources"] = {}
    return Experiment.model_validate(
        {
            "id": row["slug"].lower(),
            "slug": row["slug"],
            "name": row["name"],
            "full_name": row.get("full_name") or None,
            "psi_ref": row.get("psi_id") or None,
            "category": row.get("category") or None,
            "investigation_type": investigation_type,
            "conditions_basis": row.get("conditions_basis") or None,
            "safety_focus": row.get("safety_focus") or None,
            "gravity_regime": gravity,
            "partial_g_analog": row.get("partial_g_analog", "").lower() == "true",
            "include_in_ranking": investigation_type == "flight",
            "platform": platform or None,
            "o2_chamber_min_pct": float_value("o2_chamber_min_pct"),
            "o2_chamber_max_pct": float_value("o2_chamber_max_pct"),
            "o2_stream_min_pct": float_value("o2_stream_min_pct"),
            "o2_stream_max_pct": float_value("o2_stream_max_pct"),
            "pressure_min_psi": pressure_min_psi,
            "pressure_max_psi": pressure_max_psi,
            "pressure_original": pressure_original,
            "pressure_original_unit": pressure_unit,
            "flow_velocity_min_cm_s": float_value("airflow_min_cm_s"),
            "flow_velocity_max_cm_s": float_value("airflow_max_cm_s"),
            "materials": _split_values(row.get("materials", "")),
            "fuels": fuels,
            "suppression_agents": _split_values(row.get("suppression_agents", "")),
            "objective": row.get("objective") or None,
            "notes": row.get("note") or None,
            "data_status": row.get("data_status") or "unknown",
            "extra_conditions": json.dumps(extra, separators=(",", ":")),
            "provenance": json.dumps(provenance, separators=(",", ":")),
        }
    )


def _basis_kind(basis: str) -> str:
    normalized = basis.casefold()
    if re.search(r"\b(?:planned|plan|not\s+confirmed)\b", normalized):
        return "planned_not_confirmed"
    if re.search(r"\b(?:table|rows)\b", normalized):
        return "reported_table"
    if re.search(r"\b(?:stated|text|approach|matrix|velocity)\b", normalized):
        return "stated_in_text"
    return "unknown"


def _condition_status(record: Experiment) -> Experiment:
    provenance = _json_object(record.provenance, "provenance")
    sources: dict[str, Any] = {}
    chamber_fields = {
        "o2_chamber_values_pct",
        "o2_chamber_min_pct",
        "o2_chamber_max_pct",
    }
    pressure_fields = {
        "pressure_values_psi",
        "pressure_min_psi",
        "pressure_max_psi",
    }
    kinds: list[str] = []
    for field in CONDITION_FIELDS:
        if not _empty(getattr(record, field)):
            field_provenance = provenance.get(field)
            if field in provenance.get("table_condition_fields", []) or (
                isinstance(field_provenance, dict)
                and field_provenance.get("source_kind") == "table"
            ):
                kind = "reported_table"
            else:
                kind = _basis_kind(record.conditions_basis or "")
            sources[field] = {"kind": kind, "provenance": field_provenance}
            if field in chamber_fields or field in pressure_fields:
                kinds.append(kind)
    status = min(
        kinds or ["unknown"],
        key={
            "planned_not_confirmed": 0,
            "unknown": 1,
            "stated_in_text": 2,
            "reported_table": 3,
        }.get,
    )
    provenance["condition_sources"] = sources
    return record.model_copy(
        update={
            "conditions_status": status,
            "provenance": json.dumps(provenance, separators=(",", ":")),
        }
    )


def _table_records(psi_dir: Path) -> dict[str, Experiment]:
    config_path = ROOT_DIR / "core" / "psi_table_map.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    configured = {item["filename"] for item in config.get("tables", [])}
    discovered = {path.name for path in psi_dir.glob("*.csv")}
    is_production_directory = psi_dir.resolve() == (
        ROOT_DIR / "data" / "raw" / "psi_tables"
    ).resolve()
    if is_production_directory and configured != discovered:
        raise ValueError(
            f"PSI table map mismatch; missing={sorted(discovered - configured)}, "
            f"extra={sorted(configured - discovered)}"
        )
    grouped: dict[str, Experiment] = {}
    for path in sorted(psi_dir.glob("*.csv")):
        match = PSI_TOKEN.search(path.name)
        if not match:
            LOGGER.warning(
                "PSI table file %s does not match a PSI id pattern; skipping",
                path.name,
            )
            continue
        psi_ref = f"PSI-{match.group('number')}"
        suffix = path.stem[match.end() :].lstrip("_- ")
        slug = _slug_from_filename(suffix or path.stem)
        record = load_psi_table(path, slug, psi_ref)
        existing = grouped.get(psi_ref.casefold())
        if existing is None:
            grouped[psi_ref.casefold()] = record
            continue
        merged = _merge_record(existing, record)
        extra = _json_object(merged.extra_conditions, "extra_conditions")
        files = extra.setdefault("table_files", [])
        files.extend(
            [path.name]
            if path.name not in files
            else []
        )
        merged = merged.model_copy(
            update={"extra_conditions": json.dumps(extra, separators=(",", ":"))}
        )
        grouped[psi_ref.casefold()] = merged
    return grouped


def _append_discrepancies(rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    path = ROOT_DIR / "docs" / "discrepancies.md"
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Data discrepancies\n"
    lines = []
    for row in rows:
        line = (
            f"| {row['investigation']} | {row['field']} | {row['curated']} | "
            f"{row['table']} | {row['curated_source']} | {row['table_source']} |"
        )
        if line not in existing:
            lines.append(line)
    if lines:
        if "| Investigation | Field | Curated value | Table value | Curated source | Table source |" not in existing:
            existing += "\n| Investigation | Field | Curated value | Table value | Curated source | Table source |\n"
        existing += "\n".join(lines) + "\n"
        path.write_text(existing, encoding="utf-8")


def _find_conflicts(curated: Experiment, table: Experiment) -> list[dict[str, str]]:
    conflicts = []
    for field in CONDITION_FIELDS:
        left, right = getattr(curated, field), getattr(table, field)
        if not _empty(left) and not _empty(right) and left != right:
            conflicts.append(
                {
                    "investigation": curated.psi_ref or curated.slug,
                    "field": field,
                    "curated": json.dumps(left, sort_keys=True),
                    "table": json.dumps(right, sort_keys=True),
                    "curated_source": "data/raw/curated/investigations.csv",
                    "table_source": json.loads(table.provenance).get(field, {}).get("source", "PSI table"),
                }
            )
    return conflicts


def _apply_update_log(records: list[Experiment], path: Path) -> None:
    if not path.exists():
        return
    rows = _read_csv_rows(path)
    by_ref = {record.psi_ref.casefold(): record for record in records if record.psi_ref}
    for row in rows:
        record = by_ref.get(row.get("psi_id", "").casefold())
        if record is None:
            continue
        provenance = _json_object(record.provenance, "provenance")
        field = row.get("column", "")
        entry = provenance.setdefault(field, {"status": "logged"})
        if not isinstance(entry, dict):
            entry = {"status": "logged", "value": entry}
            provenance[field] = entry
        updates = entry.setdefault("update_log", [])
        update = {"value": row.get("value", ""), "source_file": row.get("source_file", "")}
        if update not in updates:
            updates.append(update)
        index = records.index(record)
        records[index] = record.model_copy(
            update={"provenance": json.dumps(provenance, separators=(",", ":"))}
        )
        by_ref[record.psi_ref.casefold()] = records[index]


def _copy_update_log(root: Path) -> None:
    source = root / "raw" / "curated" / "update_log.csv"
    target = root / "processed" / "curated_update_log.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.exists():
        target.write_bytes(source.read_bytes())


def _report_scenario_differences(root: Path, scenarios: list[Scenario]) -> None:
    curated_path = root / "raw" / "curated" / "scenarios.csv"
    if not curated_path.exists():
        return
    curated = {
        row.get("key", ""): row
        for row in _read_csv_rows(curated_path)
        if row.get("key")
    }
    configured = {scenario.key: scenario for scenario in scenarios}
    differences: list[str] = []
    for key in sorted(set(curated) | set(configured)):
        if key not in curated:
            differences.append(f"- Scenario `{key}` exists only in data/scenarios.yaml.")
            continue
        if key not in configured:
            differences.append(f"- Scenario `{key}` exists only in curated scenarios.csv.")
            continue
        curated_name = curated[key].get("name", "")
        if curated_name != configured[key].name:
            differences.append(
                f"- Scenario `{key}` name differs: curated `{curated_name}`; "
                f"configured `{configured[key].name}`."
            )
    if not differences:
        return
    path = ROOT_DIR / "docs" / "discrepancies.md"
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Data discrepancies\n"
    section = "\n## Scenario configuration differences\n"
    additions = "\n".join(differences) + "\n"
    if additions not in existing:
        path.write_text(existing + section + additions, encoding="utf-8")


def _scenario_records(path: Path) -> list[Scenario]:
    if not path.exists():
        raise ValueError(f"{path} is missing")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        if not all(isinstance(value, dict) for value in raw.values()):
            raise ValueError(f"{path}: scenario values must be mappings")
        raw = [{**value, "key": key} for key, value in raw.items()]
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{path} must contain a non-empty list or mapping")
    return [Scenario.model_validate(item) for item in raw]


def ingest(data_dir: str | Path | None = None) -> list[Experiment]:
    """Build processed experiments without duplicate records or source mutation."""
    root = _resolve_data_dir(data_dir)
    curated_path = root / "raw" / "curated" / "investigations.csv"
    if curated_path.exists():
        curated_rows = _read_csv_rows(curated_path)
        records = [_curated_record(row, curated_path.as_posix()) for row in curated_rows]
    else:
        records = _read_seed(root / "seed_experiments.csv")
    if len({record.slug.casefold() for record in records}) != len(records):
        raise ValueError("Curated investigations contain duplicate slugs")
    if len({record.psi_ref.casefold() for record in records if record.psi_ref}) != len(
        [record for record in records if record.psi_ref]
    ):
        raise ValueError("Curated investigations contain duplicate PSI identifiers")

    discrepancies: list[dict[str, str]] = []
    table_records = _table_records(root / "raw" / "psi_tables")
    by_ref = {record.psi_ref.casefold(): record for record in records if record.psi_ref}
    by_slug = {record.slug.casefold(): record for record in records}
    for psi_key, table in table_records.items():
        curated = by_ref.get(psi_key) or by_slug.get(table.slug.casefold())
        if curated is None:
            LOGGER.warning("PSI record %s has no seed row matches; appending", table.psi_ref)
            records.append(table)
            continue
        discrepancies.extend(_find_conflicts(curated, table))
        merged = _merge_record(curated, table)
        merged = _condition_status(merged)
        index = records.index(curated)
        records[index] = merged
        by_ref = {record.psi_ref.casefold(): record for record in records if record.psi_ref}
        by_slug = {record.slug.casefold(): record for record in records}

    records = [_condition_status(record) for record in records]
    _apply_update_log(records, root / "raw" / "curated" / "update_log.csv")
    _copy_update_log(root)
    _append_discrepancies(discrepancies)

    scenarios_path = root / "scenarios.yaml"
    scenarios = _scenario_records(scenarios_path)
    _report_scenario_differences(root, scenarios)
    write_scenarios(scenarios, root)
    write_experiments(records, root)
    LOGGER.info("Wrote %d experiments from curated and PSI sources", len(records))
    return records


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Build processed NASA PSI data.")
    parser.add_argument("command", choices=["seed", "docs"])
    parser.add_argument("--data-dir", default=None)
    args = parser.parse_args()
    if args.command == "seed":
        ingest(args.data_dir)
    elif args.command == "docs":
        data_root = _resolve_data_dir(args.data_dir)
        documents, chunks = build_documents(data_root)
        existing_documents = read_documents(data_root)
        existing_hashes = {document.content_hash for document in existing_documents}
        new_documents = [
            document for document in documents if document.content_hash not in existing_hashes
        ]
        new_document_ids = {document.id for document in new_documents}
        new_chunks = [
            chunk for chunk in chunks if chunk.document_id in new_document_ids
        ]
        write_documents([*existing_documents, *new_documents], data_root)
        write_chunks([*read_chunks(data_root), *new_chunks], data_root)
        counts: dict[str, int] = {}
        for document in new_documents:
            counts[document.doc_type] = counts.get(document.doc_type, 0) + 1
        print(f"Documents: {len(new_documents)}")
        print(f"Chunks: {len(new_chunks)}")
        for doc_type, count in sorted(counts.items()):
            print(f"{doc_type}: {count}")


if __name__ == "__main__":
    main()
