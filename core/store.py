"""Validated, atomic storage for the processed NASA PSI data files."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import tempfile
import warnings
from pathlib import Path
from typing import Any, Iterable, TypeVar

import numpy as np
import pandas as pd
import yaml
from pydantic import BaseModel, ValidationError

from .config import ROOT_DIR, settings
from .schema import (
    CHUNK_COLUMNS,
    DOCUMENT_COLUMNS,
    EXPERIMENT_COLUMNS,
    Chunk,
    Document,
    EmbeddingsMeta,
    Experiment,
    Insight,
    Scenario,
)

ModelT = TypeVar("ModelT", bound=BaseModel)
LIST_COLUMNS = {
    "o2_chamber_values_pct",
    "o2_stream_values_pct",
    "pressure_values_psi",
    "materials",
    "fuels",
    "suppression_agents",
}


def _resolve_data_dir(data_dir: str | Path | None = None) -> Path:
    """Resolve the configured default against the project root."""
    if data_dir is not None:
        return Path(data_dir)
    configured = Path(settings.data_dir)
    return configured if configured.is_absolute() else ROOT_DIR / configured


def processed_dir(data_dir: str | Path | None = None, create: bool = False) -> Path:
    """Return the processed-data directory, optionally creating it."""
    path = _resolve_data_dir(data_dir) / "processed"
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def _path(data_dir: str | Path | None, filename: str, create: bool = False) -> Path:
    """Return a processed-data file path without creating it by default."""
    return processed_dir(data_dir, create=create) / filename


def _temporary_path(path: Path) -> Path:
    """Create an empty, extension-preserving temporary file next to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(
        prefix=".tmp-", suffix=path.suffix, dir=path.parent
    )
    os.close(handle)
    return Path(temporary)


def _atomic_write(path: Path, writer: Any) -> None:
    """Write through an extension-preserving temporary file and replace atomically."""
    temporary_path = _temporary_path(path)
    try:
        writer(temporary_path)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _validated_records(
    records: Iterable[Any], model: type[ModelT]
) -> list[ModelT]:
    """Validate every record with its Pydantic model."""
    return [model.model_validate(record) for record in records]


def _ensure_unique(records: list[BaseModel], fields: tuple[str, ...]) -> None:
    """Raise a named error when a record identifier is duplicated."""
    for field in fields:
        seen: set[Any] = set()
        for record in records:
            value = getattr(record, field)
            if value in seen:
                raise ValueError(f"Duplicate {field}: {value}")
            seen.add(value)


def _set_csv_field_size_limit() -> None:
    """Set the largest CSV field limit supported by the current platform."""
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit //= 2


def _read_csv(path: Path, model: type[ModelT], columns: list[str]) -> list[ModelT]:
    """Read validated CSV records without creating a missing parent directory."""
    if not path.exists():
        return []
    _set_csv_field_size_limit()
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames or []
        required = [
            column for column in columns if model.model_fields[column].is_required()
        ]
        missing = [column for column in required if column not in fieldnames]
        if missing:
            raise ValueError(f"{path} is missing required columns: {missing}")
        missing_optional = [
            column for column in columns
            if column not in fieldnames and column not in required
        ]
        if missing_optional:
            warnings.warn(
                f"{path} is missing optional columns that will use defaults: "
                f"{missing_optional}",
                UserWarning,
                stacklevel=2,
            )
        extra = [column for column in fieldnames if column not in columns]
        if extra:
            warnings.warn(
                f"{path} contains extra columns that will be ignored: {extra}",
                UserWarning,
                stacklevel=2,
            )
        records: list[ModelT] = []
        for row_number, row in enumerate(reader, start=2):
            identifier = row.get("slug") or row.get("id") or "<unknown>"
            values: dict[str, Any] = {}
            for key in columns:
                value = row.get(key, "")
                if value == "":
                    if key in LIST_COLUMNS:
                        values[key] = []
                    continue
                values[key] = value
            for key in LIST_COLUMNS.intersection(values):
                if isinstance(values[key], str):
                    try:
                        values[key] = json.loads(values[key])
                    except json.JSONDecodeError as error:
                        raise ValueError(
                            f"{path.name} row {row_number} ({identifier}): "
                            f"invalid JSON in {key}: {error.msg}"
                        ) from error
            try:
                records.append(model.model_validate(values))
            except ValidationError as error:
                raise ValueError(
                    f"{path.name} row {row_number} ({identifier}): "
                    f"validation failed: {error}"
                ) from error
        return records


def _write_csv(path: Path, records: Iterable[BaseModel], columns: list[str]) -> None:
    """Serialize validated records as UTF-8 CSV with JSON list cells."""
    rows = []
    for record in records:
        row = record.model_dump(mode="json")
        for key in LIST_COLUMNS.intersection(row):
            row[key] = json.dumps(row[key], separators=(",", ":"))
        rows.append(row)

    def write(target: Path) -> None:
        with target.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)

    _atomic_write(path, write)


def read_experiments(data_dir: str | Path | None = None) -> list[Experiment]:
    """Read experiments from CSV."""
    return _read_csv(_path(data_dir, "experiments.csv"), Experiment, EXPERIMENT_COLUMNS)


def read_experiments_csv(path: str | Path) -> list[Experiment]:
    """Read experiments from an explicitly provided CSV path."""
    return _read_csv(Path(path), Experiment, EXPERIMENT_COLUMNS)


def write_experiments(
    records: Iterable[Experiment], data_dir: str | Path | None = None
) -> None:
    """Validate and atomically write experiments to CSV."""
    validated = _validated_records(records, Experiment)
    _ensure_unique(validated, ("id", "slug"))
    _write_csv(_path(data_dir, "experiments.csv", create=True), validated, EXPERIMENT_COLUMNS)


def read_documents(data_dir: str | Path | None = None) -> list[Document]:
    """Read documents from CSV."""
    return _read_csv(_path(data_dir, "documents.csv"), Document, DOCUMENT_COLUMNS)


def write_documents(
    records: Iterable[Document], data_dir: str | Path | None = None
) -> None:
    """Validate and atomically write documents to CSV."""
    validated = _validated_records(records, Document)
    _ensure_unique(validated, ("id",))
    _write_csv(_path(data_dir, "documents.csv", create=True), validated, DOCUMENT_COLUMNS)


def _chunk_frame(records: list[Chunk]) -> pd.DataFrame:
    """Build a Parquet frame with nullable integer chunk fields."""
    frame = pd.DataFrame([record.model_dump() for record in records], columns=CHUNK_COLUMNS)
    frame["chunk_index"] = pd.array(frame["chunk_index"], dtype="Int64")
    frame["page"] = pd.array(frame["page"], dtype="Int64")
    return frame


def read_chunks(data_dir: str | Path | None = None) -> list[Chunk]:
    """Read chunks from Parquet, preserving missing pages as None."""
    path = _path(data_dir, "chunks.parquet")
    if not path.exists():
        return []
    frame = pd.read_parquet(path)
    missing = [column for column in CHUNK_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")
    rows = frame[CHUNK_COLUMNS].astype(object).where(frame[CHUNK_COLUMNS].notna(), None)
    records = rows.to_dict(orient="records")
    for row in records:
        for field in ("chunk_index", "page"):
            if row[field] is not None:
                row[field] = int(row[field])
    return [Chunk.model_validate(row) for row in records]


def write_chunks(
    records: Iterable[Chunk], data_dir: str | Path | None = None
) -> None:
    """Validate and atomically write chunks to Parquet."""
    validated = _validated_records(records, Chunk)
    _ensure_unique(validated, ("chunk_id",))
    frame = _chunk_frame(validated)
    _atomic_write(
        _path(data_dir, "chunks.parquet", create=True),
        lambda path: frame.to_parquet(path, index=False),
    )


def read_scenarios(data_dir: str | Path | None = None) -> list[Scenario]:
    """Read scenarios from YAML."""
    path = _path(data_dir, "scenarios.yaml")
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as file:
        raw = yaml.safe_load(file) or []
    if not isinstance(raw, list):
        raise ValueError(f"{path} must contain a list")
    return [Scenario.model_validate(item) for item in raw]


def write_scenarios(
    records: Iterable[Scenario], data_dir: str | Path | None = None
) -> None:
    """Validate and atomically write scenarios to YAML."""
    values = [
        record.model_dump(mode="json")
        for record in _validated_records(records, Scenario)
    ]
    _atomic_write(
        _path(data_dir, "scenarios.yaml", create=True),
        lambda path: path.write_text(
            yaml.safe_dump(values, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        ),
    )


def read_insights(data_dir: str | Path | None = None) -> list[Insight]:
    """Read cached insights from JSON."""
    path = _path(data_dir, "insights.json")
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{path} must contain a list")
    return [Insight.model_validate(item) for item in raw]


def write_insights(
    records: Iterable[Insight], data_dir: str | Path | None = None
) -> None:
    """Validate and atomically write cached insights to JSON."""
    values = [
        record.model_dump(mode="json")
        for record in _validated_records(records, Insight)
    ]
    _atomic_write(
        _path(data_dir, "insights.json", create=True),
        lambda path: path.write_text(json.dumps(values, indent=2), encoding="utf-8"),
    )


def _validate_embeddings(values: np.ndarray) -> None:
    """Validate the non-empty, normalized float32 embedding matrix."""
    if (
        values.dtype != np.float32
        or values.ndim != 2
        or values.shape[0] == 0
        or values.shape[1] == 0
    ):
        raise ValueError("Embeddings must be a non-empty two-dimensional float32 matrix")
    if not np.isfinite(values).all():
        raise ValueError("Embeddings must contain only finite values")
    if not np.allclose(np.linalg.norm(values, axis=1), 1.0, atol=1e-5):
        raise ValueError("Embedding rows must be normalized")


def read_embeddings(data_dir: str | Path | None = None) -> np.ndarray | None:
    """Read and validate the embedding matrix and matching metadata."""
    path = _path(data_dir, "embeddings.npy")
    if not path.exists():
        return None
    matrix = np.load(path, allow_pickle=False)
    _validate_embeddings(matrix)
    meta = read_embeddings_meta(data_dir)
    if meta is None:
        raise ValueError("embeddings_meta.json is required when embeddings.npy exists")
    if matrix.shape != (meta.row_count, meta.dimension):
        raise ValueError("Embedding matrix does not match embeddings metadata")
    return matrix


def read_embeddings_meta(data_dir: str | Path | None = None) -> EmbeddingsMeta | None:
    """Read embedding metadata when it exists."""
    path = _path(data_dir, "embeddings_meta.json")
    if not path.exists():
        return None
    return EmbeddingsMeta.model_validate(json.loads(path.read_text(encoding="utf-8")))


def write_embeddings_meta(
    meta: EmbeddingsMeta, data_dir: str | Path | None = None
) -> None:
    """Validate and atomically write embedding metadata."""
    validated = EmbeddingsMeta.model_validate(meta)
    _atomic_write(
        _path(data_dir, "embeddings_meta.json", create=True),
        lambda path: path.write_text(validated.model_dump_json(indent=2), encoding="utf-8"),
    )


def write_embeddings(
    matrix: np.ndarray, model: str, data_dir: str | Path | None = None
) -> None:
    """Validate and write embeddings and matching metadata as a pair.

    Both files are fully written to temporary files first, and only then
    swapped into place back to back, so the window in which they can disagree
    is as small as possible. Replacing two files is still not truly atomic: if
    the process dies between the two replacements, ``read_embeddings`` detects
    the mismatch through its shape check against the metadata and raises.
    """
    values = np.asarray(matrix)
    _validate_embeddings(values)
    meta = EmbeddingsMeta(model=model, dimension=values.shape[1], row_count=values.shape[0])

    matrix_path = _path(data_dir, "embeddings.npy", create=True)
    meta_path = _path(data_dir, "embeddings_meta.json", create=True)
    temporaries: list[Path] = []
    try:
        matrix_temporary = _temporary_path(matrix_path)
        temporaries.append(matrix_temporary)
        with matrix_temporary.open("wb") as file:
            np.save(file, values)

        meta_temporary = _temporary_path(meta_path)
        temporaries.append(meta_temporary)
        meta_temporary.write_text(meta.model_dump_json(indent=2), encoding="utf-8")

        os.replace(matrix_temporary, matrix_path)
        os.replace(meta_temporary, meta_path)
    finally:
        for temporary in temporaries:
            temporary.unlink(missing_ok=True)


def init(data_dir: str | Path | None = None) -> None:
    """Create missing processed data files without overwriting existing files."""
    directory = processed_dir(data_dir, create=True)
    files = (
        ("experiments.csv", write_experiments),
        ("documents.csv", write_documents),
        ("chunks.parquet", write_chunks),
        ("scenarios.yaml", write_scenarios),
        ("insights.json", write_insights),
    )
    for filename, writer in files:
        if not (directory / filename).exists():
            writer([], data_dir)


def main() -> None:
    """Run the store command-line interface."""
    parser = argparse.ArgumentParser(description="Initialize processed data files.")
    parser.add_argument("command", choices=["init"])
    parser.add_argument("--data-dir", default=None)
    args = parser.parse_args()
    if args.command == "init":
        init(args.data_dir)


if __name__ == "__main__":
    main()