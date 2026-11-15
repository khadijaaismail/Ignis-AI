from pathlib import Path

from app.components import _field
from core.config import Settings
from core.ingest import _read_seed


def test_settings_defaults():
    s = Settings(_env_file=None)
    assert s.min_retrieval_score == 0.35
    assert s.demo_mode is False


def test_field_keeps_zero_and_defaults_missing():
    assert _field({"id": 0}, "id") == 0
    assert _field({}, "id") == "Not reported"


def test_seed_rows_keep_status_and_structured_fields():
    records = _read_seed(Path(__file__).parents[1] / "data" / "seed_experiments.csv")

    assert records
    assert all(
        record.data_status in {"from_challenge_text", "from_psi", "unknown"}
        for record in records
    )
    flex = next(record for record in records if record.slug == "flex")
    assert flex.suppression_agents == ["carbon dioxide", "helium"]