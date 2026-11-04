"""Isolated temporary fixtures: no production/test cross-contamination."""

from pathlib import Path

import pytest

from property_intelligence.generator import generate_dataset
from property_intelligence.ingestion import run_ingestion


@pytest.fixture
def seeded_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    raw = tmp_path / "raw"
    prop_path, comp_path = generate_dataset(raw, count=90, seed=17)
    db = tmp_path / "test.sqlite3"
    run_ingestion(properties_csv=prop_path, components_csv=comp_path,
                  db_path=db, report_dir=tmp_path / "reports")
    monkeypatch.setenv("DB_PATH", str(db))
    monkeypatch.setenv("PLANNER_MODE", "rules")
    return db
