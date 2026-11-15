import csv
import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from core.data import load_experiments
from core.schema import EXPERIMENT_COLUMNS, Chunk, Document, Experiment, Insight, Scenario
from core.store import (
    init,
    read_chunks,
    read_documents,
    read_embeddings,
    read_embeddings_meta,
    read_experiments,
    read_insights,
    read_scenarios,
    write_chunks,
    write_documents,
    write_embeddings,
    write_experiments,
    write_insights,
    write_scenarios,
)
from core.units import atm_to_psi, oxygen_mole_fraction_to_pct


def test_all_file_round_trips(tmp_path):
    experiment = Experiment(
        id="e1", slug="demo", name="Demo", materials=["steel"],
        fuels=["methane"], o2_chamber_values_pct=[21.0],
    )
    document = Document(
        id="d1", title="Source", doc_type="report", content_hash="hash"
    )
    chunk = Chunk(chunk_id="c1", document_id="d1", chunk_index=0, content="Evidence")
    scenario = Scenario(key="earth", name="Earth", material_priorities=["steel"])
    insight = Insight(
        category="prevention", experiment_slugs=["demo"], content="Text",
        model="test", created_at="2026-01-01T00:00:00Z",
    )

    write_experiments([experiment], tmp_path)
    write_documents([document], tmp_path)
    write_chunks([chunk], tmp_path)
    write_scenarios([scenario], tmp_path)
    write_insights([insight], tmp_path)
    embeddings = np.array([[1.0, 0.0]], dtype=np.float32)
    write_embeddings(embeddings, "test", tmp_path)

    assert read_experiments(tmp_path)[0] == experiment
    assert read_documents(tmp_path)[0] == document
    assert read_chunks(tmp_path)[0] == chunk
    assert read_scenarios(tmp_path)[0] == scenario
    assert read_insights(tmp_path)[0] == insight
    assert np.array_equal(read_embeddings(tmp_path), embeddings)


def test_init_creates_empty_files(tmp_path):
    init(tmp_path)
    assert read_experiments(tmp_path) == []
    assert read_documents(tmp_path) == []
    assert read_chunks(tmp_path) == []
    assert read_scenarios(tmp_path) == []
    assert read_insights(tmp_path) == []


def test_list_columns_are_stored_as_json_and_parsed(tmp_path):
    write_experiments(
        [Experiment(
            id="e1", slug="s", name="n", full_name="f",
            category="detection", safety_focus="detection", materials=["glass"],
        )],
        tmp_path,
    )
    assert read_experiments(tmp_path)[0].materials == ["glass"]
    with (tmp_path / "processed" / "experiments.csv").open(
        newline="", encoding="utf-8"
    ) as file:
        row = next(csv.DictReader(file))
    assert json.loads(row["materials"]) == ["glass"]


def test_atomic_write_replaces_existing_file(tmp_path):
    write_scenarios([Scenario(key="old", name="Old")], tmp_path)
    write_scenarios([Scenario(key="new", name="New")], tmp_path)
    assert read_scenarios(tmp_path)[0].key == "new"
    assert {path.name for path in (tmp_path / "processed").iterdir()} == {"scenarios.yaml"}


def test_unit_conversions_use_documented_factors():
    assert oxygen_mole_fraction_to_pct(0.21) == pytest.approx(21.0)
    assert oxygen_mole_fraction_to_pct(0.29) == pytest.approx(29.0)
    assert oxygen_mole_fraction_to_pct(0.07) == pytest.approx(7.0)
    assert atm_to_psi(1.0) == pytest.approx(14.7)
    assert atm_to_psi(0.5) == pytest.approx(7.35)


def test_optional_fields_and_empty_lists_preserve_not_reported_values():
    experiment = Experiment(id="e1", slug="s", name="Name")
    document = Document(id="d1", title="Generated", doc_type="challenge_text", content_hash="h")

    assert experiment.full_name is None
    assert experiment.category is None
    assert experiment.safety_focus is None
    assert experiment.o2_chamber_values_pct == []
    assert document.local_path is None


@pytest.mark.parametrize(
    "values",
    [
        {"o2_chamber_values_pct": [-1]},
        {"o2_chamber_values_pct": [101]},
        {"o2_stream_values_pct": [-1]},
        {"o2_stream_values_pct": [101]},
        {"o2_chamber_min_pct": -1},
        {"o2_stream_max_pct": 101},
        {"pressure_values_psi": [-0.1]},
        {"pressure_min_psi": -1},
        {"flow_velocity_max_cm_s": -1},
        {"o2_chamber_min_pct": 30, "o2_chamber_max_pct": 20},
        {"o2_stream_min_pct": 30, "o2_stream_max_pct": 20},
        {"pressure_min_psi": 2, "pressure_max_psi": 1},
        {"flow_velocity_min_cm_s": 4, "flow_velocity_max_cm_s": 3},
    ],
)
def test_experiment_rejects_invalid_bounds(values):
    with pytest.raises(ValidationError):
        Experiment(id="e1", slug="s", name="Name", **values)


@pytest.mark.parametrize(
    "field, value",
    [
        ("o2_chamber_min_pct", -1),
        ("o2_chamber_max_pct", 101),
        ("o2_stream_min_pct", -1),
        ("o2_stream_max_pct", 101),
    ],
)
def test_experiment_rejects_invalid_o2_percent_fields(field, value):
    with pytest.raises(ValidationError):
        Experiment(id="e1", slug="s", name="Name", **{field: value})


def test_empty_data_dir_returns_all_experiment_columns(tmp_path):
    frame = load_experiments(str(tmp_path))

    assert frame.empty
    assert list(frame.columns) == list(Experiment.model_fields)


def test_experiment_cache_refreshes_when_file_mtime_changes(tmp_path):
    first = Experiment(id="e1", slug="first", name="First")
    second = Experiment(id="e2", slug="second", name="Second")
    write_experiments([first], tmp_path)
    first_frame = load_experiments(str(tmp_path))

    write_experiments([second], tmp_path)
    path = Path(tmp_path) / "processed" / "experiments.csv"
    os.utime(path, (path.stat().st_atime, path.stat().st_mtime + 2))
    second_frame = load_experiments(str(tmp_path))

    assert first_frame["slug"].tolist() == ["first"]
    assert second_frame["slug"].tolist() == ["second"]


def test_sparse_experiment_round_trips_without_nan_values(tmp_path):
    original = Experiment(id="e1", slug="sparse", name="Sparse")

    write_experiments([original], tmp_path)
    loaded = read_experiments(tmp_path)[0]

    assert loaded == original
    assert loaded.full_name is None
    assert loaded.category is None
    assert loaded.safety_focus is None
    assert loaded.o2_chamber_values_pct == []
    assert loaded.pressure_values_psi == []
    assert not any(
        isinstance(value, float) and np.isnan(value)
        for value in loaded.model_dump().values()
    )


def test_init_does_not_destroy_existing_experiments(tmp_path):
    original = Experiment(id="e1", slug="kept", name="Kept")
    write_experiments([original], tmp_path)

    init(tmp_path)

    assert read_experiments(tmp_path) == [original]


def test_missing_files_return_empty_values(tmp_path):
    assert read_experiments(tmp_path) == []
    assert read_documents(tmp_path) == []
    assert read_chunks(tmp_path) == []
    assert read_scenarios(tmp_path) == []
    assert read_insights(tmp_path) == []
    assert read_embeddings(tmp_path) is None
    assert read_embeddings_meta(tmp_path) is None
    assert not tmp_path.exists() or not any(tmp_path.iterdir())


def test_atomic_write_failure_preserves_previous_file(monkeypatch, tmp_path):
    path = tmp_path / "processed" / "scenarios.yaml"
    write_scenarios([Scenario(key="old", name="Old")], tmp_path)
    previous_content = path.read_text(encoding="utf-8")

    def fail_write_text(*args, **kwargs):
        raise OSError("synthetic serialization failure")

    monkeypatch.setattr(Path, "write_text", fail_write_text)
    with pytest.raises(OSError, match="synthetic serialization failure"):
        write_scenarios([Scenario(key="new", name="New")], tmp_path)

    assert path.read_text(encoding="utf-8") == previous_content
    assert list(path.parent.glob(".tmp-*")) == []


def test_discrete_lists_round_trip_as_float_lists(tmp_path):
    original = Experiment(
        id="e1",
        slug="discrete",
        name="Discrete",
        o2_chamber_values_pct=[17.0, 21.0, 30.0],
        pressure_values_psi=[4.3, 10.2],
        conditions_discrete=True,
    )

    write_experiments([original], tmp_path)
    loaded = read_experiments(tmp_path)[0]

    assert loaded.o2_chamber_values_pct == [17.0, 21.0, 30.0]
    assert loaded.pressure_values_psi == [4.3, 10.2]
    assert all(isinstance(value, float) for value in loaded.o2_chamber_values_pct)
    assert all(isinstance(value, float) for value in loaded.pressure_values_psi)
    assert loaded.conditions_discrete is True


def test_csv_bom_empty_defaults_and_reordered_columns_round_trip(tmp_path):
    original = Experiment(
        id="e1",
        slug="csv",
        name="CSV",
        objective="Synthetic objective",
        extra_conditions="",
    )
    row = original.model_dump()
    row["extra_conditions"] = ""
    row["o2_chamber_values_pct"] = json.dumps(row["o2_chamber_values_pct"])
    row["pressure_values_psi"] = json.dumps(row["pressure_values_psi"])
    row["materials"] = json.dumps(row["materials"])
    row["fuels"] = json.dumps(row["fuels"])
    row["suppression_agents"] = json.dumps(row["suppression_agents"])
    columns = list(reversed(EXPERIMENT_COLUMNS))
    path = tmp_path / "processed" / "experiments.csv"
    path.parent.mkdir(parents=True)
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerow(row)

    loaded = read_experiments(tmp_path)[0]

    assert loaded.id == original.id
    assert loaded.slug == original.slug
    assert loaded.name == original.name
    assert loaded.extra_conditions == "{}"


def test_chunk_pages_round_trip_with_nullable_integer_types(tmp_path):
    records = [
        Chunk(chunk_id="missing", document_id="d1", chunk_index=0, content="No page"),
        Chunk(chunk_id="paged", document_id="d1", chunk_index=1, content="Page", page=3),
    ]

    write_chunks(records, tmp_path)
    loaded = read_chunks(tmp_path)

    assert loaded[0].page is None
    assert loaded[1].page == 3
    assert isinstance(loaded[1].page, int)


def test_scenario_unicode_round_trip(tmp_path):
    original = Scenario(key="unicode", name="O₂ habitat", assumptions="Synthetic O₂ note")

    write_scenarios([original], tmp_path)

    assert read_scenarios(tmp_path) == [original]


def test_insight_datetime_round_trip(tmp_path):
    created_at = datetime(2026, 1, 1, 12, 30, 45).isoformat()
    original = Insight(
        category="prevention",
        experiment_slugs=["demo"],
        content="Text",
        model="test",
        created_at=created_at,
    )

    write_insights([original], tmp_path)

    assert read_insights(tmp_path) == [original]
    assert json.loads(
        (tmp_path / "processed" / "insights.json").read_text(encoding="utf-8")
    )[0]["created_at"] == created_at


def test_scenario_none_and_list_fields_round_trip_through_yaml(tmp_path):
    original = Scenario(
        key="partial",
        name="Partial",
        airflow_note=None,
        material_priorities=["glass", "steel"],
        source_note=None,
    )

    write_scenarios([original], tmp_path)

    assert read_scenarios(tmp_path) == [original]


def test_csv_missing_optional_columns_warns_and_uses_defaults(tmp_path):
    path = tmp_path / "processed" / "experiments.csv"
    path.parent.mkdir(parents=True)
    path.write_text("id,slug,name\n e1,sparse,Sparse\n".replace(" ", ""), encoding="utf-8")

    with pytest.warns(UserWarning, match="missing optional columns"):
        loaded = read_experiments(tmp_path)

    assert loaded == [Experiment(id="e1", slug="sparse", name="Sparse")]


def test_csv_errors_include_file_row_and_identifier(tmp_path):
    path = tmp_path / "processed" / "experiments.csv"
    path.parent.mkdir(parents=True)
    path.write_text(
        "id,slug,name,o2_chamber_values_pct\n"
        'e1,bad-row,Bad,"[not-json]"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=r"experiments\.csv.*row 2.*bad-row"):
        read_experiments(tmp_path)


def test_csv_reader_accepts_fields_larger_than_default_limit(tmp_path):
    path = tmp_path / "processed" / "experiments.csv"
    path.parent.mkdir(parents=True)
    objective = "x" * 200_000
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["id", "slug", "name", "objective"])
        writer.writeheader()
        writer.writerow({"id": "e1", "slug": "large", "name": "Large", "objective": objective})

    loaded = read_experiments(tmp_path)

    assert loaded[0].objective == objective


def test_text_fields_with_csv_special_characters_round_trip(tmp_path):
    objective = 'Measure "flame, spread"\nunder controlled conditions.'
    original = Experiment(id="e1", slug="text", name="Text", objective=objective)

    write_experiments([original], tmp_path)

    assert read_experiments(tmp_path)[0].objective == objective


def test_embeddings_write_metadata(tmp_path):
    embeddings = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)

    write_embeddings(embeddings, "synthetic-model", tmp_path)

    metadata_path = tmp_path / "processed" / "embeddings_meta.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata == {
        "model": "synthetic-model",
        "dimension": 2,
        "row_count": 2,
    }
    assert read_embeddings_meta(tmp_path).model_dump() == metadata


def test_embeddings_matrix_round_trip(tmp_path):
    original = np.array([[0.6, 0.8], [0.8, 0.6]], dtype=np.float32)

    write_embeddings(original, "synthetic-model", tmp_path)

    loaded = read_embeddings(tmp_path)
    assert loaded is not None
    assert np.array_equal(loaded, original)


def test_duplicate_experiment_slug_is_rejected(tmp_path):
    records = [
        Experiment(id="e1", slug="duplicate", name="First"),
        Experiment(id="e2", slug="duplicate", name="Second"),
    ]

    with pytest.raises(ValueError, match="Duplicate slug"):
        write_experiments(records, tmp_path)


@pytest.mark.parametrize("metadata_field, invalid_value", [
    ("dimension", 3),
    ("row_count", 3),
])
def test_embeddings_validate_metadata_shape(tmp_path, metadata_field, invalid_value):
    embeddings = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    write_embeddings(embeddings, "synthetic-model", tmp_path)
    metadata_path = tmp_path / "processed" / "embeddings_meta.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata[metadata_field] = invalid_value
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(ValueError, match="does not match"):
        read_embeddings(tmp_path)


@pytest.mark.parametrize("header", ["id,slug"])
def test_experiments_reject_malformed_csv_columns(tmp_path, header):
    path = tmp_path / "processed" / "experiments.csv"
    path.parent.mkdir(parents=True)
    path.write_text(f"{header}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required columns"):
        read_experiments(tmp_path)


def test_experiments_warn_about_extra_csv_columns(tmp_path):
    path = tmp_path / "processed" / "experiments.csv"
    path.parent.mkdir(parents=True)
    path.write_text("id,slug,name,unexpected\ne1,sparse,Sparse,value\n", encoding="utf-8")

    with pytest.warns(UserWarning, match="extra columns"):
        assert read_experiments(tmp_path) == [
            Experiment(id="e1", slug="sparse", name="Sparse")
        ]


def test_scenarios_reject_invalid_yaml_shape_and_values(tmp_path):
    path = tmp_path / "processed" / "scenarios.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("key: earth\nname: Earth\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must contain a list"):
        read_scenarios(tmp_path)

    path.write_text(
        "- key: earth\n  name: Earth\n  gravity_regime: invalid\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        read_scenarios(tmp_path)
