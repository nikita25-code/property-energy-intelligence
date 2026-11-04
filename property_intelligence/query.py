"""Auditable natural-language -> constrained intent -> parameterized SELECT templates.

LLM only produces a typed query plan (optional), never executable SQL.
"""

from __future__ import annotations

import json
import os
import re
from urllib import request as urlrequest

from pydantic import ValidationError

from .models import QueryPlan


class UnsupportedQuestion(ValueError):
    """No safe supported interpretation of a question could be determined."""


BUILDING_ALIASES = {
    "School": r"\bschools?\b",
    "Library": r"\blibrar(?:y|ies)\b",
    "Sports Facility": r"\b(?:sports? facilit(?:y|ies)|gymnasiums?|sports? centres?)\b",
    "Administrative Office": r"\b(?:offices?|administrative buildings?)\b",
    "Daycare": r"\b(?:daycares?|nurseries|kindergartens?)\b",
    "Health Clinic": r"\b(?:health clinics?|clinics?)\b",
}
COMPONENT_ALIASES = {
    "HVAC": r"\b(?:hvac|heating|ventilation|air conditioning)\b",
    "Insulation": r"\binsulat(?:ion|e)\b",
    "Roof": r"\broofs?\b",
    "Windows": r"\bwindows?\b",
}


def rules_plan(question: str) -> QueryPlan:
    q = question.strip().lower()
    filters = {}
    for kind, pattern in BUILDING_ALIASES.items():
        if re.search(pattern, q):
            filters["building_type"] = kind
            break
    for component, pattern in COMPONENT_ALIASES.items():
        if re.search(pattern, q):
            filters["component_type"] = component
            break
    for district in ("North", "South", "East", "West", "Central", "Harbour"):
        if re.search(rf"\b{district.lower()}\b", q):
            filters["district"] = district
            break
    year = re.search(r"\b(?:built|constructed)?\s*(?:before|prior to|older than)\s+(18\d\d|19\d\d|20\d\d)\b", q)
    if year:
        filters["built_before"] = int(year.group(1))
    limit = re.search(r"\b(?:top|first|show|list)\s+(\d{1,3})\b", q)
    if limit:
        filters["limit"] = min(25, max(1, int(limit.group(1))))

    if re.search(r"\b(?:npv|net present value|financial return|best value)\b", q):
        intent = "intervention_value"
    elif re.search(r"\b(?:annual energy sav|save(?:s|d)? (?:the )?(?:most )?energy|energy reduction|kwh sav|energy savings)\w*", q):
        intent = "energy_savings"
    elif re.search(r"\b(?:assets?|units?|equipment)\b", q) and re.search(r"\b(?:condition|wear|worst|poor|critical)\b", q):
        intent = "asset_condition"
    elif re.search(r"\b(?:worst|poorest|bad|lowest|inefficient)\b", q) and re.search(r"\b(?:energy|rating|rated|efficien)\w*", q):
        intent = "worst_energy"
    elif re.search(r"\b(?:per (?:square met(?:er|re)|m2|sqm)|/m2|/sqm|per m²)\b", q):
        intent = "cost_per_m2"
    elif re.search(r"\b(?:total|overall|aggregate|combined)\b", q) and re.search(r"\b(?:cost|budget|expenditure)\w*", q):
        intent = "total_cost"
    elif "component_type" in filters and re.search(r"\b(?:cost|repair|upgrade|priority|priorities|urgent|expensive|maintenan|retrofit)\w*", q):
        intent = "component_priority"
    elif re.search(r"\b(?:priority|priorities|urgent|most critical|retrofit first|upgrade first|maintenan|rank|which buildings)\w*", q):
        intent = "priority"
    else:
        raise UnsupportedQuestion(
            "Supported examples: 'Which schools built before 1970 have the worst energy ratings?', "
            "'Show top 5 urgent HVAC upgrades', 'What is the estimated cost per m2 for libraries?', "
            "or 'What is the total retrofit cost for schools?', 'Which interventions save the most energy?'."
        )
    return QueryPlan(intent=intent, **filters)


SYSTEM_PROMPT = """You translate building portfolio questions into a constrained JSON plan.
Never write SQL. Select exactly one intent: worst_energy, priority, cost_per_m2,
total_cost, component_priority, energy_savings, asset_condition, intervention_value. The only fields are intent, building_type,
component_type, built_before, district, limit. building_type must be School,
Library, Sports Facility, Administrative Office, Daycare, Health Clinic or null.
component_type must be HVAC, Insulation, Roof, Windows or null.
district must be North, South, East, West, Central, Harbour or null.
Use numeric year for 'built before', not a greater-than filter. Use limit 10 unless
specified (maximum 25). Return JSON only; never invent facts or numerical answers.
If the question is unsupported, return {"intent":"priority"} only if it clearly
requests building prioritization; otherwise produce an invalid intent 'unsupported'.
"""


def llm_plan(question: str) -> QueryPlan:
    """Optional LLM parsing via OpenAI-compatible Chat Completions JSON mode.

    Only the question is sent to the provider; no database records are transmitted.
    """
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    req = urlrequest.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urlrequest.urlopen(req, timeout=12) as response:
        parsed = json.loads(response.read().decode("utf-8"))
    content = parsed["choices"][0]["message"]["content"]
    return QueryPlan.model_validate_json(content)


def choose_plan(question: str) -> tuple[QueryPlan, str]:
    mode = os.getenv("PLANNER_MODE", "rules").lower()
    if mode not in ("rules", "llm", "auto"):
        raise ValueError("PLANNER_MODE must be rules, llm or auto")
    if mode == "rules":
        return rules_plan(question), "rules"
    if mode == "auto" and not os.getenv("OPENAI_API_KEY"):
        return rules_plan(question), "rules"
    try:
        return llm_plan(question), "llm"
    except (RuntimeError, ValueError, KeyError, OSError, ValidationError) as exc:
        if mode == "llm":
            raise RuntimeError("LLM planner unavailable; use PLANNER_MODE=rules") from exc
        return rules_plan(question), "rules_fallback"


def build_query(plan: QueryPlan) -> tuple[str, list[str | int]]:
    """Only predefined SELECTs; values are always passed as SQLite parameters."""
    conditions = ["1 = 1"]
    params: list[str | int] = []
    prefix = "p."
    if plan.building_type:
        conditions.append(f"{prefix}building_type = ?")
        params.append(plan.building_type)
    if plan.built_before is not None:
        conditions.append(f"{prefix}built_year < ?")
        params.append(plan.built_before)
    if plan.district:
        conditions.append(f"{prefix}district = ?")
        params.append(plan.district)
    where = " AND ".join(conditions)
    if plan.intent == "worst_energy":
        sql = f"""SELECT p.id, p.name, p.building_type, p.built_year,
        p.energy_rating, p.energy_score, p.priority_score,
        p.estimated_maintenance_cost_dkk
        FROM properties p WHERE {where} AND p.energy_score IS NOT NULL
        ORDER BY p.energy_score DESC, p.priority_score DESC, p.id ASC LIMIT ?"""
    elif plan.intent == "priority":
        sql = f"""SELECT p.id, p.name, p.building_type, p.energy_rating,
        p.priority_score, p.estimated_maintenance_cost_dkk,
        p.estimated_cost_per_m2_dkk
        FROM properties p WHERE {where}
        ORDER BY p.priority_score DESC, p.id ASC LIMIT ?"""
    elif plan.intent == "cost_per_m2":
        sql = f"""SELECT COUNT(*) AS property_count,
        ROUND(COALESCE(SUM(p.estimated_maintenance_cost_dkk), 0), 2) AS total_estimated_cost_dkk,
        ROUND(COALESCE(SUM(p.estimated_maintenance_cost_dkk) / NULLIF(SUM(p.floor_area_m2),0), 0), 2)
        AS area_weighted_cost_per_m2_dkk
        FROM properties p WHERE {where}"""
    elif plan.intent == "total_cost":
        sql = f"""SELECT COUNT(*) AS property_count,
        ROUND(COALESCE(SUM(p.estimated_maintenance_cost_dkk), 0), 2) AS total_estimated_cost_dkk
        FROM properties p WHERE {where}"""
    elif plan.intent == "component_priority":
        if plan.component_type:
            conditions.append("c.component_type = ?")
            params.append(plan.component_type)
        where = " AND ".join(conditions)
        sql = f"""SELECT c.id AS component_id, p.id AS property_id, p.name,
        p.building_type, c.component_type, c.condition_score,
        c.estimated_maintenance_cost_dkk, p.priority_score
        FROM components c JOIN properties p ON p.id = c.property_id
        WHERE {where}
        ORDER BY c.condition_score DESC, c.estimated_maintenance_cost_dkk DESC,
        c.id ASC LIMIT ?"""
    elif plan.intent == "energy_savings":
        if plan.component_type:
            conditions.append('s.system_type = ?')
            params.append(plan.component_type)
        where = " AND ".join(conditions)
        sql = f"""SELECT p.id AS property_id,p.name,s.system_type,a.name AS asset_name,
        i.estimated_savings_kwh_year,i.annual_savings_dkk,i.cost_dkk,i.confidence
        FROM interventions i JOIN properties p ON p.id=i.property_id
        JOIN systems s ON s.id=i.system_id JOIN assets a ON a.id=i.asset_id
        WHERE {where} AND i.estimated_savings_kwh_year > 0
        ORDER BY i.estimated_savings_kwh_year DESC,i.id ASC LIMIT ?"""
    elif plan.intent == "asset_condition":
        if plan.component_type:
            conditions.append('s.system_type = ?')
            params.append(plan.component_type)
        where = " AND ".join(conditions)
        sql = f"""SELECT p.id AS property_id,p.name,s.system_type,
        a.id AS asset_id,a.name AS asset_name,a.condition_score,a.quantity,a.unit,
        ins.finding,ins.confidence
        FROM assets a JOIN systems s ON s.id=a.system_id
        JOIN properties p ON p.id=a.property_id
        LEFT JOIN inspections ins ON ins.asset_id=a.id
        WHERE {where} ORDER BY a.condition_score DESC,p.priority_score DESC,a.id ASC LIMIT ?"""
    elif plan.intent == "intervention_value":
        if plan.component_type:
            conditions.append('s.system_type = ?')
            params.append(plan.component_type)
        where = " AND ".join(conditions)
        sql = f"""SELECT p.id AS property_id,p.name,s.system_type,a.name AS asset_name,
        i.cost_dkk,i.annual_savings_dkk,i.npv_dkk,i.confidence
        FROM interventions i JOIN properties p ON p.id=i.property_id
        JOIN systems s ON s.id=i.system_id JOIN assets a ON a.id=i.asset_id
        WHERE {where} ORDER BY i.npv_dkk DESC,i.id ASC LIMIT ?"""
    else:
        raise AssertionError("QueryPlan validation failed to constrain intent")
    if plan.intent in ("worst_energy", "priority", "component_priority", "energy_savings", "asset_condition", "intervention_value"):
        params.append(plan.limit)
    return " ".join(sql.split()), params


def explain_results(plan: QueryPlan, rows: list[dict]) -> str:
    """Deterministic narration derived from DB results, not generated figures."""
    if plan.intent in ("cost_per_m2", "total_cost"):
        if not rows or rows[0]["property_count"] == 0:
            return "No matching properties."
        result = rows[0]
        total = f'{result["total_estimated_cost_dkk"]:,.0f}'
        if plan.intent == "cost_per_m2":
            rate = f'{result["area_weighted_cost_per_m2_dkk"]:,.2f}'
            return f'{result["property_count"]:,} properties: scenario cost DKK {total}; portfolio-weighted DKK {rate}/m².'
        return f'{result["property_count"]:,} properties: estimated scenario cost DKK {total}.'
    if not rows:
        return "No matching records."
    if plan.intent == "worst_energy":
        return f'{len(rows)} records returned (up to {plan.limit}); worst displayed grade {rows[0]["energy_rating"]}. Excludes unknown ratings.'
    if plan.intent == "priority":
        return f'{len(rows)} records returned (up to {plan.limit}), ranked by documented 0–100 scenario priority score.'
    if plan.intent == "energy_savings":
        return f'{len(rows)} interventions returned, ranked by assumed annual energy savings (kWh); not measured performance.'
    if plan.intent == "asset_condition":
        return f'{len(rows)} assets returned, ranked by their synthetic observed condition (5 = critical).'
    if plan.intent == "intervention_value":
        return f'{len(rows)} interventions returned, ranked by illustrative 4%-discounted NPV; assumptions must be validated.'
    return f'{len(rows)} components returned (up to {plan.limit}), ranked by condition then estimated cost.' 
