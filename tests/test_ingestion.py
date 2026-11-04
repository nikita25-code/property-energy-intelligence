import json
import sqlite3

import pytest

from property_intelligence.costs import estimate_component_cost
from property_intelligence.generator import generate_dataset
from property_intelligence.ingestion import clean_properties, normalized_date, run_ingestion


def test_dates_and_invalid_dates():
    assert str(normalized_date("21/05/2025")) == "2025-05-21"
    assert str(normalized_date("2025/05/21")) == "2025-05-21"
    assert normalized_date("NULL") is None
    with pytest.raises(ValueError):
        normalized_date("yesterday")


def test_cost_monotonic_with_condition():
    kwargs = {"component_type": "HVAC", "area_m2": 1500,
              "installed_year": 1998, "rating": "F"}
    assert estimate_component_cost(condition_score=5, **kwargs) > estimate_component_cost(condition_score=3, **kwargs)
    assert estimate_component_cost(condition_score=1, **kwargs) == 0


def test_invalid_and_missing_property_are_handled():
    base = {"id": "P00001", "name": "Sample library",
            "building_type": "Library", "district": "North",
            "built_year": "1990", "floor_area_m2": "800", "energy_rating": "e", "last_audit": "2025-02-12"}
    records = [base, {**base, "id": "P00002", "built_year": "NULL", "floor_area_m2": ""},
               {**base, "id": "P00003", "built_year": "not-a-year"}, base]
    clean, rejected, stats = clean_properties(records)
    assert len(clean) == 2
    assert len(rejected) == 2
    assert clean["P00002"].year_imputed and clean["P00002"].area_imputed
    assert clean["P00001"].energy_rating == "E"
    assert stats["year_imputed"] == 1


def test_full_pipeline_atomic_integrity_and_report(seeded_db):
    with sqlite3.connect(seeded_db) as conn:
        props = conn.execute("SELECT COUNT(*) FROM properties").fetchone()[0]
        comps = conn.execute("SELECT COUNT(*) FROM components").fetchone()[0]
        assert props > 75
        assert comps > 280
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("SELECT MIN(estimated_maintenance_cost_dkk) FROM properties").fetchone()[0] >= 0
        diffs = conn.execute("""SELECT p.id FROM properties p WHERE ABS(p.estimated_maintenance_cost_dkk -
            COALESCE((SELECT SUM(c.estimated_maintenance_cost_dkk) FROM components c WHERE c.property_id=p.id),0)) > 0.015""").fetchall()
        assert not diffs
    report = json.loads((seeded_db.parent / "reports" / "ingestion_report.json").read_text())
    assert report["properties"]["loaded"] == props
    assert report["components"]["loaded"] == comps


def test_failed_ingest_preserves_previous_database(tmp_path):
    original = tmp_path / "live.sqlite3"
    original.write_bytes(b"do not replace")
    raw = tmp_path / "raw"
    prop_csv, comp_csv = generate_dataset(raw, count=2)
    # Force all component rows invalid so the valid database is not overwritten.
    comp_csv.write_text("id,property_id,component_type,condition_score,installed_year,last_serviced\n", encoding="utf-8")
    with pytest.raises(ValueError, match="No valid"):
        run_ingestion(properties_csv=prop_csv, components_csv=comp_csv,
                      db_path=original, report_dir=tmp_path / "reports")
    assert original.read_bytes() == b"do not replace"
