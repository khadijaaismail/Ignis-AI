"""Build searchable documents and chunks from NASA and challenge sources."""

from __future__ import annotations

import csv
import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from .chunking import chunk_text
from .schema import Chunk, Document, Experiment
from .store import read_experiments

LOGGER = logging.getLogger(__name__)
DOC_TEXT_FIELDS = (
    "objective",
    "approach",
    "hypothesis",
    "research_impacts",
    "publication_titles",
)


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


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ValueError(f"Unable to read source {path}: {error}") from error


def _not_reported(value: Any) -> str:
    if value is None or value == "" or value == []:
        return "Not reported"
    if isinstance(value, list):
        values = [item for item in value if item is not None and item != ""]
        return "; ".join(str(item) for item in values) or "Not reported"
    return str(value)


def _experiment_card(record: Experiment) -> str:
    values = record.model_dump()
    planned = values["conditions_status"] == "planned_not_confirmed"
    qualifier = " (planned, not confirmed as flown)" if planned else ""
    investigation_type = (
        "ground-based modelling study, not a flight experiment"
        if values["investigation_type"] == "ground"
        else values["investigation_type"]
    )
    fields = (
        ("Name", values["name"]),
        ("Category", values["category"]),
        ("Safety focus", values["safety_focus"]),
        ("Gravity regime", values["gravity_regime"]),
        (f"Chamber O2 (%){qualifier}", values["o2_chamber_values_pct"] or
         [values["o2_chamber_min_pct"], values["o2_chamber_max_pct"]]),
        (f"Burner-stream O2 (%){qualifier}", values["o2_stream_values_pct"] or
         [values["o2_stream_min_pct"], values["o2_stream_max_pct"]]),
        (f"Pressure (atm){qualifier}", values["pressure_original"]),
        (f"Pressure (psi){qualifier}", values["pressure_values_psi"] or
         [values["pressure_min_psi"], values["pressure_max_psi"]]),
        ("Airflow (cm/s)", [values["flow_velocity_min_cm_s"], values["flow_velocity_max_cm_s"]]),
        ("Fuels or materials", values["fuels"] or values["materials"]),
        ("Conditions status", values["conditions_status"]),
        ("Conditions basis", values["conditions_basis"]),
        ("Investigation type", investigation_type),
        ("Notes", values["notes"]),
    )
    lines = [f"{label}: {_not_reported(value)}" for label, value in fields]
    review_values: list[str] = []
    for source_name in ("extra_conditions", "provenance"):
        parsed = json.loads(values[source_name] or "{}")
        for key in ("text_stated_range", "update_log"):
            if key in parsed:
                review_values.append(f"{key}: {parsed[key]}")
    lines.append(
        "Values under review: "
        + ("; ".join(review_values) if review_values else "Not reported")
    )
    return "\n".join(lines)


def _manifest_slug(text: str, records: list[Experiment]) -> str | None:
    matches = {
        record.slug
        for record in records
        if any(
            alias and alias.casefold() in text.casefold()
            for alias in (record.name, record.psi_ref or "")
        )
    }
    return next(iter(matches)) if len(matches) == 1 else None


def _source_document(
    content: str,
    *,
    title: str,
    doc_type: str,
    experiment_slug: str | None = None,
    source_url: str | None = None,
    local_path: str | None = None,
    metadata: dict[str, Any] | None = None,
    pages: list[tuple[int | None, str]] | None = None,
) -> tuple[Document, list[Chunk]]:
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    document_id = f"doc-{content_hash[:16]}"
    document = Document(
        id=document_id,
        experiment_slug=experiment_slug,
        title=title,
        doc_type=doc_type,
        source_url=source_url,
        content_hash=content_hash,
        local_path=local_path,
    )
    chunks: list[Chunk] = []
    for page, page_text in pages or [(None, content)]:
        for part in chunk_text(page_text, page=page, meta=metadata):
            chunks.append(
                Chunk(
                    chunk_id=f"{document_id}-{len(chunks)}",
                    document_id=document_id,
                    experiment_slug=experiment_slug,
                    chunk_index=len(chunks),
                    content=part["text"],
                    page=part["page"],
                    meta=json.dumps(part["meta"], separators=(",", ":")),
                )
            )
    return document, chunks


def _data_workspace(data_root: Path) -> Path:
    return data_root.parent if data_root.name == "data" else data_root


def build_documents(data_root: str | Path) -> tuple[list[Document], list[Chunk]]:
    """Build documents and chunks without writing processed files."""
    root = Path(data_root)
    records = read_experiments(root)
    by_psi = {record.psi_ref.casefold(): record for record in records if record.psi_ref}
    sources: list[tuple[Document, list[Chunk]]] = []
    text_fields_path = root / "raw" / "docs" / "psi_isa_text_fields.csv"
    if not text_fields_path.exists():
        raise ValueError(f"Required source is unreadable or missing: {text_fields_path}")

    for row in _read_csv_rows(text_fields_path):
        psi_id = row.get("psi_id", "")
        record = by_psi.get(psi_id.casefold())
        if record is None:
            LOGGER.info("Skipping %s as out of scope (not in experiments.csv)", psi_id)
            continue
        content = "\n".join(
            f"{field}: {row.get(field, '')}"
            for field in DOC_TEXT_FIELDS
            if row.get(field, "").strip()
        )
        document, _ = _source_document(
            content,
            title=row.get("title") or record.name,
            doc_type="psi_record",
            experiment_slug=record.slug,
            local_path=text_fields_path.as_posix(),
        )
        chunks: list[Chunk] = []
        for field in DOC_TEXT_FIELDS:
            field_text = row.get(field, "").strip()
            if not field_text:
                continue
            prefix = f"{record.name} - {field}: "
            for part in chunk_text(
                prefix + field_text,
                meta={"psi_id": psi_id, "section": field},
            ):
                chunks.append(
                    Chunk(
                        chunk_id=f"{document.id}-{len(chunks)}",
                        document_id=document.id,
                        experiment_slug=record.slug,
                        chunk_index=len(chunks),
                        content=part["text"],
                        meta=json.dumps(part["meta"], separators=(",", ":")),
                    )
                )
        sources.append((document, chunks))

    for record in records:
        sources.append(
            _source_document(
                _experiment_card(record),
                title=record.name,
                doc_type="psi_record",
                experiment_slug=record.slug,
                local_path=(root / "processed" / "experiments.csv").as_posix(),
                metadata={"psi_id": record.psi_ref, "section": "experiment_card"},
            )
        )

    spec_path = _data_workspace(root) / "docs" / "spec.md"
    if not spec_path.exists():
        raise ValueError(f"Required source is unreadable or missing: {spec_path}")
    sources.append(
        _source_document(
            _read_text(spec_path),
            title="Challenge specification",
            doc_type="challenge_text",
            local_path=spec_path.as_posix(),
        )
    )

    manifest_path = root / "raw" / "docs" / "manifest.csv"
    if manifest_path.exists():
        for row in _read_csv_rows(manifest_path):
            file_path = root / "raw" / "docs" / row.get("file", "")
            if not file_path.exists():
                raise ValueError(f"Manifest source is unreadable or missing: {file_path}")
            try:
                if file_path.suffix.casefold() == ".pdf":
                    reader = PdfReader(str(file_path))
                    pages = [
                        (index + 1, page.extract_text() or "")
                        for index, page in enumerate(reader.pages)
                    ]
                    content = "\n".join(text for _, text in pages)
                else:
                    content = _read_text(file_path)
                    pages = [(None, content)]
            except (OSError, ValueError, TypeError, PdfReadError) as error:
                raise ValueError(f"Unable to extract text from source {file_path}: {error}") from error
            sources.append(
                _source_document(
                    content,
                    title=row.get("title") or file_path.name,
                    doc_type=row.get("doc_type") or "report",
                    experiment_slug=row.get("experiment_slug") or _manifest_slug(content, records),
                    source_url=row.get("source_url") or None,
                    local_path=file_path.as_posix(),
                    pages=pages,
                )
            )

    documents: list[Document] = []
    chunks: list[Chunk] = []
    for document, document_chunks in sources:
        documents.append(document)
        chunks.extend(document_chunks)
    return documents, chunks
