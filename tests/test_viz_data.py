import pandas as pd

from core import viz_data


def test_get_plot_points_excludes_flagged_and_missing_rows_without_mutating_source(tmp_path, monkeypatch):
    processed = tmp_path / "processed"
    processed.mkdir()
    points = pd.DataFrame(
        [
            {"slug": "demo", "test_id": "good", "x": 1, "y": 2, "group": "a", "flags": ""},
            {"slug": "demo", "test_id": "flagged", "x": 3, "y": 4, "group": "a", "flags": ""},
            {"slug": "demo", "test_id": "missing-x", "x": None, "y": 6, "group": "b", "flags": ""},
            {"slug": "demo", "test_id": "missing-y", "x": 7, "y": None, "group": "b", "flags": ""},
            {"slug": "other", "test_id": "other", "x": 9, "y": 10, "group": "c", "flags": ""},
        ]
    )
    flags = points.iloc[[1]].copy()
    points.to_csv(processed / "test_points.csv", index=False)
    flags.to_csv(processed / "test_points_flags.csv", index=False)
    original = points.copy(deep=True)
    monkeypatch.setattr(viz_data, "PROCESSED_DIR", processed)

    plotted, summary = viz_data.get_plot_points("demo", "x", "y", "group")

    pd.testing.assert_frame_equal(points, original)
    assert plotted["test_id"].tolist() == ["good"]
    assert plotted["group"].tolist() == ["a"]
    assert summary == {
        "n_total": 4,
        "n_plotted": 1,
        "n_excluded": 3,
        "exclusion_reasons": {"flagged": 1, "missing_x": 1, "missing_y": 1},
    }
