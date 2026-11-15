import csv
import json

from core.docs_ingest import build_documents
from core.schema import Experiment
from core.store import write_experiments


def test_build_documents_skips_out_of_scope_rows_and_marks_missing_card_values(tmp_path):
    write_experiments(
        [Experiment(
            id="e1",
            slug="demo",
            name="Demo",
            psi_ref="PSI-1",
            investigation_type="ground",
            conditions_status="planned_not_confirmed",
            conditions_basis="Planned conditions; not confirmed.",
            o2_chamber_values_pct=[30.0],
            pressure_original="10.2",
        )],
        tmp_path,
    )
    docs_dir = tmp_path / "raw" / "docs"
    docs_dir.mkdir(parents=True)
    with (docs_dir / "psi_isa_text_fields.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["psi_id", "title", "objective", "approach", "hypothesis",
                        "research_impacts", "publication_titles"],
        )
        writer.writeheader()
        writer.writerow({
            "psi_id": "PSI-1",
            "title": "In scope",
            "objective": "Objective text.",
        })
        writer.writerow({
            "psi_id": "PSI-999",
            "title": "Out of scope",
            "objective": "Should not be included.",
        })
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "spec.md").write_text("Challenge specification.", encoding="utf-8")

    documents, chunks = build_documents(tmp_path)

    assert len(documents) == 3
    assert all("Should not be included." not in chunk.content for chunk in chunks)
    objective_chunks = [
        chunk for chunk in chunks
        if json.loads(chunk.meta).get("section") == "objective"
    ]
    assert len(objective_chunks) == 1
    assert objective_chunks[0].content.startswith("Demo - objective:")
    card = next(document for document in documents if document.title == "Demo")
    card_chunk = next(chunk for chunk in chunks if chunk.document_id == card.id)
    assert "Category: Not reported" in card_chunk.content
    assert "planned, not confirmed as flown" in card_chunk.content
    assert "Chamber O2" in card_chunk.content
    assert "30" in card_chunk.content
    assert "Pressure (atm) (planned, not confirmed as flown): 10.2" in card_chunk.content
    assert "Pressure (psi) (planned, not confirmed as flown): Not reported" in card_chunk.content
    assert "Conditions status: planned_not_confirmed" in card_chunk.content
    assert "Conditions basis: Planned conditions; not confirmed." in card_chunk.content
    assert "Investigation type: ground-based modelling study, not a flight experiment" in card_chunk.content
