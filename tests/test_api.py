import sqlite3

from fastapi.testclient import TestClient

from property_intelligence.api import app

client = TestClient(app)


def test_summary_and_property_detail(seeded_db):
    response = client.get("/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_properties"] >= 75
    assert data["total_components"] > data["total_properties"]
    assert data["cost_model"] == "assumption_based_scenario_not_ml"
    assert data["portfolio_weighted_cost_per_m2_dkk"] > 0
    with sqlite3.connect(seeded_db) as conn:
        pid = conn.execute("SELECT id FROM properties LIMIT 1").fetchone()[0]
    detail = client.get(f"/properties/{pid}")
    assert detail.status_code == 200
    assert len(detail.json()["components"]) == 4
    assert abs(sum(c["estimated_maintenance_cost_dkk"] for c in detail.json()["components"])
               - detail.json()["property"]["estimated_maintenance_cost_dkk"]) < .02
    assert client.get("/properties/P99999").status_code == 404
    assert client.get("/properties/not-an-id").status_code == 422


def test_ask_returns_sql_grounded_numbers(seeded_db):
    r = client.post("/ask", json={"question": "Which schools built before 1970 have the worst energy ratings?"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["planner"] == "rules"
    assert data["interpreted_plan"]["built_before"] == 1970
    assert data["sql_parameters"] == ["School", 1970, 10]
    assert data["row_count"] == len(data["rows"])
    for row in data["rows"]:
        assert row["building_type"] == "School" and row["built_year"] < 1970
    assert "SELECT" in data["sql"] and "DELETE" not in data["sql"]


def test_ask_aggregate_matches_sql(seeded_db):
    r = client.post("/ask", json={"question": "What is the total cost for schools?"})
    assert r.status_code == 200
    aggregate = r.json()["rows"][0]
    with sqlite3.connect(seeded_db) as conn:
        expected = conn.execute("SELECT COUNT(*), ROUND(SUM(estimated_maintenance_cost_dkk),2) FROM properties WHERE building_type = 'School'").fetchone()
    assert (aggregate["property_count"], aggregate["total_estimated_cost_dkk"]) == expected


def test_unsupported_question_and_read_only_behavior(seeded_db):
    assert client.post("/ask", json={"question": "DROP TABLE properties; DELETE DATABASE"}).status_code == 422
    assert client.post("/ask", json={"question": "hi"}).status_code == 422
    assert client.post("/ask", json={"question": "What is the cost per m2 for libraries?"}).status_code == 200
    with sqlite3.connect(seeded_db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM properties").fetchone()[0] > 0


def test_database_uninitialized(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "does-not-exist.sqlite3"))
    assert client.get("/analytics/summary").status_code == 503
    assert client.get("/health").json()["status"] == "uninitialized"
