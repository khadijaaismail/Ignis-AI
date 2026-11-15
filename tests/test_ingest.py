import csv
import json
from pathlib import Path

import pytest

from core.config import ROOT_DIR
from core.ingest import _condition_status, _merge_record, _read_seed, ingest
from core.ranking import is_ranking_eligible
from core.schema import Experiment
from core.store import read_experiments, read_scenarios


def _write_seed(path, **overrides):
    row = {
        "id": "flex-2",
        "slug": "flex-2",
        "name": "FLEX-2",
        "psi_ref": "psi-68",
        "category": "suppression",
        "gravity_regime": "unknown",
        "full_name": "Seed full name",
        "notes": "Seed notes",
        "extra_conditions": json.dumps({"seed": "kept"}),
        "provenance": json.dumps({"seed": {"source": "synthetic"}}),
    }
    row.update(overrides)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=row)
        writer.writeheader()
        writer.writerow(row)


def _write_scenarios(path, content="- key: earth\n  name: Earth\n"):
    path.write_text(content, encoding="utf-8")


def test_ingest_merges_psi_into_seed_without_overwriting_seed(tmp_path, caplog):
    _write_seed(tmp_path / "seed_experiments.csv", ambient_gas="seed gas")
    _write_scenarios(tmp_path / "scenarios.yaml")
    psi_dir = tmp_path / "raw" / "psi_tables"
    psi_dir.mkdir(parents=True)
    (psi_dir / "PSI-68_Experimental table_Flex2.csv").write_text(
        "Sample (Fuel Type),Ambient Gas Mixture,Oxygen Mole Fraction\n"
        "methane,air,0.21\n",
        encoding="utf-8",
    )

    records = ingest(tmp_path)

    assert len([record for record in records if record.slug == "flex-2"]) == 1
    record = read_experiments(tmp_path)[0]
    assert record.id == "flex-2"
    assert record.name == "FLEX-2"
    assert record.full_name == "Seed full name"
    assert record.notes == "Seed notes"
    assert record.gravity_regime == "unknown"
    assert record.ambient_gas == "seed gas"
    assert record.o2_chamber_values_pct == [21.0]
    assert record.data_status == "from_psi"
    assert json.loads(record.extra_conditions)["seed"] == "kept"
    assert json.loads(record.provenance)["seed"]["source"] == "synthetic"
    assert "conflict" in caplog.text.lower()
    assert not any(
        field in message.lower()
        for message in caplog.messages
        for field in ("id", "slug", "name")
    )


def test_ingest_keeps_seed_identity_and_merges_discrete_conditions_without_warnings(
    tmp_path, caplog
):
    _write_seed(tmp_path / "seed_experiments.csv")
    _write_scenarios(tmp_path / "scenarios.yaml")
    psi_dir = tmp_path / "raw" / "psi_tables"
    psi_dir.mkdir(parents=True)
    (psi_dir / "PSI-68_Experimental table_Flex2.csv").write_text(
        "Sample (Fuel Type),Ambient Gas Mixture,Oxygen Mole Fraction\n"
        "methane,air,0.17; 0.21\n",
        encoding="utf-8",
    )

    records = ingest(tmp_path)

    assert len(records) == 1
    record = records[0]
    assert record.conditions_discrete is True
    assert record.id == "flex-2"
    assert record.slug == "flex-2"
    assert record.name == "FLEX-2"
    provenance = json.loads(record.provenance)
    assert not any(field in provenance for field in ("id", "slug", "name"))
    assert not any(
        field in message
        for message in caplog.messages
        for field in ("id", "slug", "name", "conditions_discrete")
    )


def test_merge_record_keeps_true_conditions_discrete_when_psi_is_false():
    seed = Experiment(
        id="seed",
        slug="seed",
        name="Seed",
        conditions_discrete=True,
    )
    psi = Experiment(
        id="psi",
        slug="psi",
        name="PSI",
        conditions_discrete=False,
    )

    merged = _merge_record(seed, psi)

    assert merged.conditions_discrete is True


def test_ingest_warns_on_unmatched_filename_and_appends_new_record(tmp_path, caplog):
    _write_seed(tmp_path / "seed_experiments.csv")
    _write_scenarios(tmp_path / "scenarios.yaml")
    psi_dir = tmp_path / "raw" / "psi_tables"
    psi_dir.mkdir(parents=True)
    (psi_dir / "not-a-psi-table.csv").write_text("anything\nvalue\n", encoding="utf-8")
    (psi_dir / "PSI-7_My Table.csv").write_text(
        "Sample (Fuel Type),Ambient Gas Mixture\nfuel,air\n", encoding="utf-8"
    )

    records = ingest(tmp_path)

    assert any(record.psi_ref == "PSI-7" and record.slug == "my-table" for record in records)
    assert "does not match" in caplog.text
    assert "no seed row matches" in caplog.text


def test_ingest_accepts_mapping_scenarios(tmp_path):
    _write_seed(tmp_path / "seed_experiments.csv")
    _write_scenarios(tmp_path / "scenarios.yaml", "earth:\n  name: Earth\n")

    ingest(tmp_path)

    assert read_scenarios(tmp_path)[0].key == "earth"


def test_ingest_validates_scenarios_before_writing_experiments(tmp_path):
    _write_seed(tmp_path / "seed_experiments.csv")
    _write_scenarios(tmp_path / "scenarios.yaml", "not-a-list: true\n")

    with pytest.raises(ValueError, match="scenario"):
        ingest(tmp_path)

    assert not (tmp_path / "processed" / "experiments.csv").exists()


def test_read_seed_parses_all_lists_and_reports_field_and_slug(tmp_path):
    path = tmp_path / "seed.csv"
    _write_seed(
        path,
        **{
            " slug ": "synthetic",
            " o2_chamber_values_pct ": "[17, 21]",
            "pressure_values_psi": "[4.3, 10.2]",
        },
    )
    records = _read_seed(path)
    assert records[0].slug == "synthetic"
    assert records[0].o2_chamber_values_pct == [17, 21]
    assert records[0].pressure_values_psi == [4.3, 10.2]

    _write_seed(path, **{"o2_chamber_values_pct": "[bad]"})
    with pytest.raises(ValueError, match=r"flex-2.*o2_chamber_values_pct"):
        _read_seed(path)


def test_condition_status_uses_measured_field_provenance_over_planned_basis():
    record = Experiment(
        id="x",
        slug="x",
        name="X",
        investigation_type="flight",
        conditions_basis="Planned atmospheres; not confirmed.",
        o2_chamber_min_pct=21,
        provenance=json.dumps(
            {
                "o2_chamber_min_pct": {
                    "status": "reported",
                    "source_kind": "table",
                    "source": "table.csv",
                }
            }
        ),
    )
    assert _condition_status(record).conditions_status == "reported_table"


def test_curated_real_records_preserve_count_and_ground_invariants():
    curated = Path(ROOT_DIR / "data" / "raw" / "curated" / "investigations.csv")
    with curated.open(newline="", encoding="utf-8-sig") as file:
        expected = sum(1 for _ in csv.DictReader(file))
    records = ingest()
    assert len(records) == expected
    assert all(
        not record.include_in_ranking
        for record in records
        if record.investigation_type == "ground"
    )
    assert sum(record.partial_g_analog for record in records) == 1
    assert sum(record.gravity_regime == "partial" for record in records) == 0


def test_real_special_cases_and_ranking_eligibility():
    records = {record.slug: record for record in ingest()}
    cfi_g = records["cfi-g"]
    assert cfi_g.o2_stream_min_pct is not None
    assert cfi_g.o2_chamber_values_pct == []
    assert not is_ranking_eligible(cfi_g)
    assert records["bre"].conditions_status == "planned_not_confirmed"
    assert not is_ranking_eligible(records["bre"])
