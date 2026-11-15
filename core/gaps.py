"""Research-gap record partitioning with explicit evidence categories."""

from __future__ import annotations

import csv
from pathlib import Path

from .ranking import is_ranking_eligible
from .schema import Experiment


def partition_gap_records(
    experiments: list[Experiment],
) -> dict[str, list[Experiment]]:
    """Partition records into placeable, ground, and unplaceable groups."""
    result = {"placeable": [], "ground": [], "unplaceable": []}
    for experiment in experiments:
        if experiment.investigation_type == "ground":
            result["ground"].append(experiment)
        elif is_ranking_eligible(experiment):
            result["placeable"].append(experiment)
        else:
            result["unplaceable"].append(experiment)
    return result


def count_test_points(slug: str, processed_dir: str | Path = "data/processed") -> int | None:
    """Count individual test points for a gap cell, or return None for fallback."""
    path = Path(processed_dir) / "test_points.csv"
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as file:
        return sum(1 for row in csv.DictReader(file) if row.get("slug") == slug)


def summarize_gap_cell(
    experiment: Experiment,
    processed_dir: str | Path = "data/processed",
) -> dict[str, object]:
    """Return test-point counts and condition spans for one gap-map cell."""
    path = Path(processed_dir) / "test_points.csv"
    if path.exists():
        with path.open(newline="", encoding="utf-8") as file:
            rows = [
                row
                for row in csv.DictReader(file)
                if row.get("slug") == experiment.slug
            ]
        if rows:
            def span(field: str) -> list[float]:
                values = [float(row[field]) for row in rows if row.get(field)]
                return [min(values), max(values)] if values else []

            return {
                "test_count": len(rows),
                "o2_chamber_pct_span": span("o2_chamber_pct"),
                "pressure_psi_span": span("pressure_psi"),
                "airflow_cm_s_span": span("airflow_cm_s"),
            }
    return {
        "test_count": None,
        "o2_chamber_pct_span": _experiment_span(
            experiment.o2_chamber_min_pct, experiment.o2_chamber_max_pct
        ),
        "pressure_psi_span": _experiment_span(
            experiment.pressure_min_psi, experiment.pressure_max_psi
        ),
        "airflow_cm_s_span": _experiment_span(
            experiment.flow_velocity_min_cm_s, experiment.flow_velocity_max_cm_s
        ),
    }


def _experiment_span(minimum: float | None, maximum: float | None) -> list[float]:
    if minimum is None or maximum is None:
        return []
    return [minimum, maximum]
