"""Reproducible ranking eligibility and evidence scores."""

from __future__ import annotations

from dataclasses import dataclass

from .schema import Experiment


def has_measured_chamber_conditions(experiment: Experiment) -> bool:
    """Return whether at least one chamber condition was measured in a source table."""
    return bool(
        experiment.o2_chamber_values_pct
        or experiment.o2_chamber_min_pct is not None
        or experiment.o2_chamber_max_pct is not None
        or experiment.pressure_values_psi
        or experiment.pressure_min_psi is not None
        or experiment.pressure_max_psi is not None
    )


def is_ranking_eligible(experiment: Experiment) -> bool:
    """Exclude ground, planned/text-only, and stream-only evidence from ranking."""
    stream_only = (
        bool(experiment.o2_stream_values_pct)
        or experiment.o2_stream_min_pct is not None
        or experiment.o2_stream_max_pct is not None
    ) and not (
        experiment.o2_chamber_values_pct
        or experiment.o2_chamber_min_pct is not None
        or experiment.o2_chamber_max_pct is not None
    )
    return (
        experiment.investigation_type == "flight"
        and experiment.include_in_ranking
        and experiment.conditions_status == "reported_table"
        and not stream_only
        and has_measured_chamber_conditions(experiment)
    )


@dataclass(frozen=True)
class RankingResult:
    """A deterministic score with the evidence that produced it."""

    experiment: Experiment
    score: int
    reasons: tuple[str, ...]


def rank_experiments(experiments: list[Experiment]) -> list[RankingResult]:
    """Rank eligible records by available measured evidence, then slug."""
    results: list[RankingResult] = []
    for experiment in experiments:
        if not is_ranking_eligible(experiment):
            continue
        reasons = []
        if experiment.o2_chamber_values_pct or experiment.o2_chamber_min_pct is not None:
            reasons.append("measured chamber oxygen")
        if experiment.pressure_values_psi or experiment.pressure_min_psi is not None:
            reasons.append("measured chamber pressure")
        if experiment.conditions_discrete:
            reasons.append("discrete table conditions")
        results.append(
            RankingResult(
                experiment=experiment,
                score=len(reasons),
                reasons=tuple(reasons),
            )
        )
    return sorted(results, key=lambda result: (-result.score, result.experiment.slug))
