import pytest

from property_intelligence.models import QueryPlan
from property_intelligence.query import UnsupportedQuestion, build_query, rules_plan


def test_realistic_question_interpreted():
    plan = rules_plan("Which schools built before 1970 have the worst energy ratings?")
    assert plan.intent == "worst_energy"
    assert plan.building_type == "School"
    assert plan.built_before == 1970
    sql, params = build_query(plan)
    assert "p.energy_score DESC" in sql
    assert params == ["School", 1970, 10]


def test_cost_and_component_intents():
    assert rules_plan("What is the cost per m2 for libraries?").intent == "cost_per_m2"
    assert rules_plan("What is the total cost of schools?").intent == "total_cost"
    plan = rules_plan("Show top 5 urgent HVAC upgrades in North")
    assert (plan.intent, plan.component_type, plan.limit, plan.district) == ("component_priority", "HVAC", 5, "North")
    sql, params = build_query(plan)
    assert params == ["North", "HVAC", 5]


def test_sql_injection_stays_in_data_not_in_sql():
    plan = QueryPlan(intent="priority", building_type="School")
    sql, params = build_query(plan)
    assert "School" not in sql
    assert params[0] == "School"
    with pytest.raises(UnsupportedQuestion):
        rules_plan("DROP TABLE properties; SELECT * FROM users")


def test_validation_rejects_arbitrary_intent():
    with pytest.raises(ValueError):
        QueryPlan(intent="DELETE FROM properties")
