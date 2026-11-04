"""Frontend availability and truthful, bounded portfolio reporting."""

import sqlite3

from fastapi.testclient import TestClient

from property_intelligence.api import app

client = TestClient(app)


def test_dashboard_served_on_same_origin(seeded_db):
    page = client.get("/")
    assert page.status_code == 200
    assert "text/html" in page.headers["content-type"]
    assert "Property Energy Intelligence" in page.text
    assert 'id="view-overview"' in page.text
    assert 'id="view-intelligence"' in page.text
    assert 'id="view-properties"' in page.text
    assert client.get("/assets/styles.css").status_code == 200
    script = client.get("/assets/app.js")
    assert script.status_code == 200
    assert "fetchJSON('/ask'" in script.text or "fetchJSON('/ask'," in script.text
    assert client.get("/favicon.svg").status_code == 200
    assert client.get("/docs").status_code == 200


def test_distributions_reconcile_with_summary(seeded_db):
    summary = client.get("/analytics/summary").json()
    distributions = client.get("/analytics/breakdown").json()
    for key in ("energy_ratings", "building_types", "districts", "priorities"):
        assert sum(row["property_count"] for row in distributions[key]) == summary["total_properties"]
        assert abs(sum(row["cost_dkk"] for row in distributions[key]) - summary["total_estimated_retrofit_cost_dkk"]) < .10
    assert sum(row["component_count"] for row in distributions["components"]) == summary["total_components"]
    assert abs(sum(row["cost_dkk"] for row in distributions["components"]) - summary["total_estimated_retrofit_cost_dkk"]) < .10
    assert next(r["property_count"] for r in distributions["priorities"] if r["label"] == "High") == summary["high_priority_properties"]


def test_paginated_properties_and_detail_are_consistent(seeded_db):
    first = client.get("/properties?page=1&page_size=3&sort=cost").json()
    second = client.get("/properties?page=2&page_size=3&sort=cost").json()
    assert first["page"] == 1
    assert first["page_size"] == 3
    assert first["total"] == client.get("/analytics/summary").json()["total_properties"]
    assert len(first["items"]) == 3 and len(second["items"]) == 3
    assert {p["id"] for p in first["items"]}.isdisjoint({p["id"] for p in second["items"]})
    assert first["items"][0]["estimated_maintenance_cost_dkk"] >= first["items"][2]["estimated_maintenance_cost_dkk"]
    detail = client.get("/properties/" + first["items"][0]["id"]).json()["property"]
    assert detail["estimated_cost_per_m2_dkk"] == first["items"][0]["estimated_cost_per_m2_dkk"]


def test_filter_by_type_district_rating_priority_and_search(seeded_db):
    with sqlite3.connect(seeded_db) as conn:
        kind, district, energy, pid = conn.execute(
            "SELECT building_type, district, energy_rating, id FROM properties LIMIT 1"
        ).fetchone()
    r = client.get("/properties", params={
        "building_type":kind,"district":district,"energy_rating":energy,"q":pid,"page_size":10
    })
    assert r.status_code == 200
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["id"] == pid
    for label, lo, hi in (("high",70,101),("medium",40,70),("low",0,40)):
        data = client.get("/properties",params={"priority":label,"page_size":100}).json()
        assert all(lo <= p["priority_score"] < hi for p in data["items"])


def test_filters_are_not_executable_sql(seeded_db):
    assert client.get("/properties",params={"building_type":"School'; DROP TABLE properties;--"}).status_code == 422
    assert client.get("/properties",params={"sort":"(SELECT 1)"}).status_code == 422
    assert client.get("/properties",params={"page_size":5000}).status_code == 422
    assert client.get("/properties",params={"q":"' OR 1=1 --"}).json()["total"] == 0
    assert client.get("/analytics/summary").status_code == 200


def test_empty_filter_and_out_of_range_pagination(seeded_db):
    empty = client.get("/properties",params={"q":"unlikely_fictional_property_zzzz"}).json()
    assert empty["total"] == 0 and empty["items"] == [] and empty["pages"] == 0
    beyond = client.get("/properties",params={"page":9999}).json()
    assert beyond["items"] == []
    assert beyond["total"] > 0
