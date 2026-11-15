"""Prepare processed test-point data for plotting."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from .config import ROOT_DIR

PROCESSED_DIR = ROOT_DIR / "data" / "processed"


def _is_missing(series: pd.Series) -> pd.Series:
    """Return a mask for null or blank values."""
    return series.isna() | series.astype("string").str.strip().eq("")


def _row_keys(frame: pd.DataFrame) -> pd.Series:
    """Build stable row keys for matching flagged records."""
    key_columns = [
        column
        for column in ("slug", "psi_id", "test_id")
        if column in frame.columns
    ]
    if not key_columns:
        raise ValueError("test points must include a row identifier column")
    return frame[key_columns].fillna("").astype(str).agg("\x1f".join, axis=1)


def _has_flag(series: pd.Series) -> pd.Series:
    """Interpret the JSON flag lists written by the test-point pipeline."""
    def has_flag(value: object) -> bool:
        if pd.isna(value) or not str(value).strip():
            return False
        try:
            parsed = json.loads(str(value))
        except json.JSONDecodeError:
            return True
        return bool(parsed)

    return series.map(has_flag)


def get_plot_points(
    experiment_slug: str,
    x_col: str,
    y_col: str,
    group_col: str | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Return unflagged, complete test points and exclusion counts.

    Values are read from the already-converted processed columns and are not
    transformed. The returned frame is a copy of the source rows.
    """
    points = pd.read_csv(PROCESSED_DIR / "test_points.csv")
    flags = pd.read_csv(PROCESSED_DIR / "test_points_flags.csv")

    if "slug" not in points.columns:
        raise ValueError("test_points.csv must include a slug column")
    for column in (x_col, y_col):
        if column not in points.columns:
            raise KeyError(column)
    if group_col is not None and group_col not in points.columns:
        raise KeyError(group_col)

    selected = points.loc[points["slug"].eq(experiment_slug)].copy()
    flagged_keys = set(_row_keys(flags))
    flagged = _row_keys(selected).isin(flagged_keys)
    if "flags" in selected.columns:
        flagged |= _has_flag(selected["flags"])

    missing_x = _is_missing(selected[x_col])
    missing_y = _is_missing(selected[y_col])
    excluded = flagged | missing_x | missing_y
    reasons = {
        "flagged": int(flagged.sum()),
        "missing_x": int((~flagged & missing_x).sum()),
        "missing_y": int((~flagged & ~missing_x & missing_y).sum()),
    }

    plotted = selected.loc[~excluded].copy()
    summary: dict[str, Any] = {
        "n_total": len(selected),
        "n_plotted": len(plotted),
        "n_excluded": int(excluded.sum()),
        "exclusion_reasons": reasons,
    }
    return plotted, summary
