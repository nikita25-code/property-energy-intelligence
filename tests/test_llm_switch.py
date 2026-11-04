from fastapi.testclient import TestClient

from property_intelligence import query
from property_intelligence.api import app
from property_intelligence.models import QueryPlan


def test_optional_llm_strategy_can_be_mocked(monkeypatch):
    monkeypatch.setenv("PLANNER_MODE", "llm")
    monkeypatch.setenv("OPENAI_API_KEY", "test-not-real")
    monkeypatch.setattr(query, "llm_plan", lambda _question: QueryPlan(intent="total_cost", building_type="School"))
    plan, source = query.choose_plan("Total cost of schools?")
    assert source == "llm"
    assert plan.intent == "total_cost"
    assert plan.building_type == "School"


def test_auto_fallback_is_explicit(monkeypatch):
    monkeypatch.setenv("PLANNER_MODE", "auto")
    monkeypatch.setenv("OPENAI_API_KEY", "test-not-real")

    def fail(_question):
        raise RuntimeError("simulated provider outage")

    monkeypatch.setattr(query, "llm_plan", fail)
    plan, source = query.choose_plan("What is the total cost for schools?")
    assert source == "rules_fallback"
    assert plan.intent == "total_cost"


def test_required_llm_without_key_returns_503(seeded_db, monkeypatch):
    monkeypatch.setenv("PLANNER_MODE", "llm")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = TestClient(app).post("/ask", json={"question": "What is the total cost for schools?"})
    assert response.status_code == 503
