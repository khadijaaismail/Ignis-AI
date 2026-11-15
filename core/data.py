"""Cached Streamlit loaders for the processed NASA PSI data layer."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from .config import ROOT_DIR, settings
from .schema import EXPERIMENT_COLUMNS, Chunk, Experiment, Scenario
from .store import read_chunks, read_embeddings, read_experiments, read_scenarios


def _resolve_data_dir(data_dir: str | None) -> str:
    """Resolve an explicit data directory or the configured default."""
    if data_dir is not None:
        return str(Path(data_dir))
    configured = Path(settings.data_dir)
    return str(configured if configured.is_absolute() else ROOT_DIR / configured)


def _file_mtime(data_dir: str, filename: str) -> float:
    """Return a file modification time, or zero when the file is missing."""
    path = Path(data_dir) / "processed" / filename
    return path.stat().st_mtime if path.exists() else 0.0


@st.cache_data
def _cached_experiments(data_dir: str, modified_at: float) -> pd.DataFrame:
    """Load experiments into a column-complete DataFrame."""
    records = [record.model_dump() for record in read_experiments(data_dir)]
    return pd.DataFrame(records, columns=EXPERIMENT_COLUMNS)


def load_experiments(data_dir: str | None = None) -> pd.DataFrame:
    """Return cached experiments with invalidation based on file modification time."""
    resolved_dir = _resolve_data_dir(data_dir)
    return _cached_experiments(
        resolved_dir, _file_mtime(resolved_dir, "experiments.csv")
    )


@st.cache_data
def _cached_scenarios(data_dir: str, modified_at: float) -> dict[str, Scenario]:
    """Load scenarios keyed by their scenario key."""
    return {scenario.key: scenario for scenario in read_scenarios(data_dir)}


def load_scenarios(data_dir: str | None = None) -> dict[str, Scenario]:
    """Return cached scenarios keyed by scenario key."""
    resolved_dir = _resolve_data_dir(data_dir)
    return _cached_scenarios(resolved_dir, _file_mtime(resolved_dir, "scenarios.yaml"))


@st.cache_data
def _cached_chunks(data_dir: str, modified_at: float) -> list[Chunk]:
    """Load document chunks with cache invalidation metadata."""
    return read_chunks(data_dir)


def load_chunks(data_dir: str | None = None) -> list[Chunk]:
    """Return cached document chunks."""
    resolved_dir = _resolve_data_dir(data_dir)
    return _cached_chunks(resolved_dir, _file_mtime(resolved_dir, "chunks.parquet"))


@st.cache_resource
def _cached_embeddings(data_dir: str, modified_at: float) -> np.ndarray | None:
    """Load the optional embedding matrix with cache invalidation metadata."""
    return read_embeddings(data_dir)


def load_embeddings(data_dir: str | None = None) -> np.ndarray | None:
    """Return the cached optional embedding matrix."""
    resolved_dir = _resolve_data_dir(data_dir)
    return _cached_embeddings(resolved_dir, _file_mtime(resolved_dir, "embeddings.npy"))


def get_experiments_df(data_dir: str | None = None) -> pd.DataFrame:
    """Return the cached experiments DataFrame used by Streamlit pages."""
    return load_experiments(data_dir)


def load_experiment_records(data_dir: str | None = None) -> list[Experiment]:
    """Return validated experiment records for ranking and gap consumers."""
    return read_experiments(data_dir)
