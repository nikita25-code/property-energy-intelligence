"""Read-only FastAPI over the reproducible SQLite demo portfolio."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import os
import sqlite3

from fastapi import FastAPI, HTTPException, Path as ApiPath, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Literal
from pydantic import ValidationError

from .models import AskRequest
from .query import UnsupportedQuestion, build_query, choose_plan, explain_results
from .settings import DB_PATH
from .planning import plan_roadmap

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"

app = FastAPI(
    title="Property Energy Intelligence",
    description=(
        "Read-only scenario analytics for fictional public buildings. "
        "Cost estimates are assumptions, not observed prices or ML predictions. "
        "NL questions resolve to an auditable, parameterized SQL template."
    ),
    version="2.0.0",
)


# Same-origin static frontend; no Node build, CORS setup, or external CDN required.
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="frontend-assets")


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(FRONTEND_DIR / "index.html", media_type="text/html")


@app.get("/favicon.svg", include_in_schema=False)
def favicon():
    return FileResponse(FRONTEND_DIR / "favicon.svg", media_type="image/svg+xml")


def database_path() -> Path:
    return Path(os.getenv("DB_PATH", str(DB_PATH)))


@contextmanager
def read_connection():
    db = database_path()
    if not db.exists():
        raise HTTPException(
            status_code=503,
            detail="Database not initialized. Run 'python ingest.py --generate'.",
        )
    uri = f"{db.resolve().as_uri()}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=5)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc
    try:
        yield conn
    finally:
        conn.close()


@app.get("/health", tags=["System"])
def health():
    """Shallow readiness (no writes or sensitive information)."""
    return {"status": "ready" if database_path().exists() else "uninitialized",
            "dataset": "synthetic", "scenario_year": 2026}


@app.get("/analytics/summary", tags=["Analytics"])
def summary():
    """Rollup; numeric energy scores are ordinal (A=1 through G=7), not physical energy units."""
    sql = """
    SELECT COUNT(*) AS total_properties,
           ROUND(AVG(energy_score), 2) AS average_energy_score,
           SUM(CASE WHEN energy_score IS NULL THEN 1 ELSE 0 END) AS unknown_energy_ratings,
           ROUND(SUM(estimated_maintenance_cost_dkk), 2) AS total_estimated_retrofit_cost_dkk,
           ROUND(SUM(estimated_maintenance_cost_dkk) / NULLIF(SUM(floor_area_m2), 0), 2)
               AS portfolio_weighted_cost_per_m2_dkk,
           SUM(CASE WHEN priority_score >= 70 THEN 1 ELSE 0 END) AS high_priority_properties,
           SUM(CASE WHEN year_imputed = 1 OR area_imputed = 1 THEN 1 ELSE 0 END)
               AS properties_with_imputed_fields
    FROM properties
    """
    with read_connection() as conn:
        record = dict(conn.execute(sql).fetchone())
        component_count = conn.execute("SELECT COUNT(*) FROM components").fetchone()[0]
        hierarchy = dict(conn.execute("""SELECT
          (SELECT COUNT(*) FROM sites) AS total_sites,
          (SELECT COUNT(*) FROM assets) AS total_assets,
          (SELECT COUNT(*) FROM inspections) AS total_inspections,
          (SELECT COUNT(*) FROM interventions) AS total_interventions,
          (SELECT ROUND(SUM(estimated_savings_kwh_year),2) FROM interventions) AS theoretical_annual_savings_kwh,
          (SELECT COUNT(*) FROM system_coverage WHERE status='not_inspected') AS not_inspected_systems
          """).fetchone())
    ordinal = record["average_energy_score"]
    return {
        **record,
        "average_energy_rating_approx": "ABCDEFG"[min(6, max(0, round(ordinal) - 1))] if ordinal is not None else None,
        "total_components": component_count,
        **hierarchy,
        "currency": "DKK",
        "data_source": "synthetic",
        "cost_model": "assumption_based_scenario_not_ml",
        "scenario_year": 2026,
    }


@app.get("/analytics/breakdown", tags=["Analytics"])
def analytics_breakdown():
    """Small, transparent aggregations behind frontend charts."""
    with read_connection() as conn:
        ratings = [dict(r) for r in conn.execute("""
            SELECT energy_rating AS label, COUNT(*) AS property_count,
                ROUND(SUM(estimated_maintenance_cost_dkk), 2) AS cost_dkk
            FROM properties GROUP BY energy_rating
            ORDER BY CASE energy_rating WHEN 'U' THEN 8 ELSE unicode(energy_rating) - unicode('A') + 1 END
        """).fetchall()]
        types = [dict(r) for r in conn.execute("""
            SELECT building_type AS label, COUNT(*) AS property_count,
                ROUND(SUM(estimated_maintenance_cost_dkk), 2) AS cost_dkk,
                ROUND(SUM(floor_area_m2), 2) AS area_m2,
                ROUND(SUM(estimated_maintenance_cost_dkk) / NULLIF(SUM(floor_area_m2), 0), 2) AS cost_per_m2_dkk
            FROM properties GROUP BY building_type ORDER BY cost_dkk DESC
        """).fetchall()]
        districts = [dict(r) for r in conn.execute("""
            SELECT district AS label, COUNT(*) AS property_count,
                ROUND(SUM(estimated_maintenance_cost_dkk), 2) AS cost_dkk
            FROM properties GROUP BY district ORDER BY cost_dkk DESC
        """).fetchall()]
        components = [dict(r) for r in conn.execute("""
            SELECT component_type AS label, COUNT(*) AS component_count,
                ROUND(SUM(estimated_maintenance_cost_dkk), 2) AS cost_dkk,
                SUM(CASE WHEN intervention_recommended = 1 THEN 1 ELSE 0 END) AS recommended_count
            FROM components GROUP BY component_type ORDER BY cost_dkk DESC
        """).fetchall()]
        priorities = [dict(r) for r in conn.execute("""
            SELECT CASE WHEN priority_score >= 70 THEN 'High'
                        WHEN priority_score >= 40 THEN 'Medium' ELSE 'Low' END AS label,
                COUNT(*) AS property_count,
                ROUND(SUM(estimated_maintenance_cost_dkk), 2) AS cost_dkk
            FROM properties GROUP BY label
            ORDER BY CASE label WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END
        """).fetchall()]
    return {
        "energy_ratings": ratings, "building_types": types, "districts": districts,
        "components": components, "priorities": priorities,
        "note": "All cost figures are synthetic, assumption-based scenario estimates.",
    }


@app.get("/properties", tags=["Properties"])
def list_properties(
    q: str = Query(default="", max_length=100),
    building_type: str | None = Query(default=None),
    district: Literal["North", "South", "East", "West", "Central", "Harbour"] | None = None,
    energy_rating: Literal["A", "B", "C", "D", "E", "F", "G", "U"] | None = None,
    priority: Literal["all", "high", "medium", "low"] = "all",
    sort: Literal["priority", "cost", "energy", "name", "year"] = "priority",
    page: int = Query(default=1, ge=1, le=100000),
    page_size: int = Query(default=12, ge=1, le=100),
):
    """Server-side, parameterized search with stable sorting and pagination."""
    conditions: list[str] = []
    params: list[str | int] = []
    if q.strip():
        conditions.append("(id LIKE ? OR name LIKE ?)")
        term = f"%{q.strip()}%"
        params.extend((term, term))
    if building_type:
        allowed = {"School", "Library", "Sports Facility", "Administrative Office", "Daycare", "Health Clinic"}
        if building_type not in allowed:
            raise HTTPException(status_code=422, detail="Unknown building type")
        conditions.append("building_type = ?")
        params.append(building_type)
    if district:
        conditions.append("district = ?")
        params.append(district)
    if energy_rating:
        conditions.append("energy_rating = ?")
        params.append(energy_rating)
    if priority != "all":
        conditions.append({"high":"priority_score >= 70", "medium":"priority_score >= 40 AND priority_score < 70",
                           "low":"priority_score < 40"}[priority])
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    order = {
        "priority":"priority_score DESC, id ASC",
        "cost":"estimated_maintenance_cost_dkk DESC, id ASC",
        "energy":"energy_score DESC NULLS LAST, priority_score DESC, id ASC",
        "name":"name COLLATE NOCASE ASC, id ASC",
        "year":"built_year ASC, id ASC",
    }[sort]
    with read_connection() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM properties {where}", params).fetchone()[0]
        items = [dict(r) for r in conn.execute(
            f"""SELECT id, name, building_type, district, built_year, floor_area_m2,
                energy_rating, priority_score, estimated_maintenance_cost_dkk,
                estimated_cost_per_m2_dkk, year_imputed, area_imputed
            FROM properties {where} ORDER BY {order} LIMIT ? OFFSET ?""",
            [*params, page_size, (page - 1) * page_size],
        ).fetchall()]
    return {"items": items, "total": total, "page": page, "page_size": page_size,
            "pages": (total + page_size - 1) // page_size}


@app.get("/properties/{property_id}", tags=["Properties"])
def property_detail(property_id: str = ApiPath(pattern=r"^P\d{5}$")):
    """One property with component-level evidence and quality flags."""
    with read_connection() as conn:
        result = conn.execute("SELECT * FROM properties WHERE id = ?", (property_id,)).fetchone()
        if result is None:
            raise HTTPException(status_code=404, detail="Property not found")
        components = conn.execute(
            "SELECT * FROM components WHERE property_id = ? ORDER BY estimated_maintenance_cost_dkk DESC, id",
            (property_id,),
        ).fetchall()
    return {
        "property": dict(result),
        "components": [dict(row) for row in components],
        "note": "Component costs are scenario estimates. Condition 1=excellent; 5=critical.",
    }


@app.get('/analytics/assets', tags=['Analytics'])
def asset_breakdown():
    """Evidence-based rollup of the asset/intervention inventory."""
    with read_connection() as conn:
        rows = [dict(r) for r in conn.execute('''
          SELECT s.system_type AS label, COUNT(DISTINCT a.id) AS asset_count,
                 COUNT(DISTINCT i.id) AS intervention_count,
                 ROUND(COALESCE(SUM(i.cost_dkk),0),2) AS investment_dkk,
                 ROUND(COALESCE(SUM(i.estimated_savings_kwh_year),0),2) AS annual_savings_kwh
          FROM systems s JOIN assets a ON a.system_id=s.id
          LEFT JOIN interventions i ON i.asset_id=a.id
          GROUP BY s.system_type ORDER BY investment_dkk DESC
        ''')]
        coverage = [dict(r) for r in conn.execute('''
          SELECT system_type AS label, status, COUNT(*) AS building_count
          FROM system_coverage GROUP BY system_type,status ORDER BY system_type,status
        ''')]
    return {'systems':rows,'coverage':coverage,
            'note':'Energy savings and asset quantities are synthetic assumptions, not measured savings.'}


@app.get('/properties/{property_id}/assets', tags=['Properties'])
def property_assets(property_id: str = ApiPath(pattern=r'^P\d{5}$')):
    """Site -> building -> system -> asset -> inspection / optional intervention."""
    with read_connection() as conn:
        prop = conn.execute('''SELECT p.id,p.name,p.building_type,p.site_id,
             st.name AS site_name,st.district,p.floor_area_m2,p.priority_score,
             p.estimated_maintenance_cost_dkk
             FROM properties p JOIN sites st ON st.id=p.site_id WHERE p.id=?''',(property_id,)).fetchone()
        if prop is None: raise HTTPException(status_code=404,detail='Property not found')
        baseline = dict(conn.execute('SELECT * FROM energy_baselines WHERE property_id=?',(property_id,)).fetchone())
        rows = [dict(r) for r in conn.execute('''SELECT
            s.id AS system_id,s.system_type,a.id AS asset_id,a.name AS asset_name,
            a.quantity,a.unit,a.unit_cost_dkk,a.condition_score,a.installed_year,a.source,
            ins.inspected_on,ins.finding,ins.confidence AS inspection_confidence,
            i.id AS intervention_id,i.action,i.cost_dkk,i.estimated_savings_kwh_year,
            i.annual_savings_dkk,i.co2_avoided_kg_year,i.lifetime_years,i.npv_dkk,
            i.confidence AS intervention_confidence,i.prerequisite_intervention_id
            FROM systems s JOIN assets a ON a.system_id=s.id
            LEFT JOIN inspections ins ON ins.asset_id=a.id
            LEFT JOIN interventions i ON i.asset_id=a.id
            WHERE s.property_id=? ORDER BY s.system_type,a.name
        ''',(property_id,)).fetchall()]
        coverage = [dict(r) for r in conn.execute('''SELECT system_type,status,reason FROM system_coverage
                     WHERE property_id=? ORDER BY system_type''',(property_id,)).fetchall()]
    systems = {}
    for r in rows:
        system = systems.setdefault(r['system_id'],{'id':r['system_id'],'type':r['system_type'],'assets':[]})
        system['assets'].append({
            'id':r['asset_id'],'name':r['asset_name'],'quantity':r['quantity'],'unit':r['unit'],
            'unit_cost_dkk':r['unit_cost_dkk'],'condition_score':r['condition_score'],
            'installed_year':r['installed_year'],'source':r['source'],
            'inspection':{'date':r['inspected_on'],'finding':r['finding'],'confidence':r['inspection_confidence']},
            'intervention': (None if r['intervention_id'] is None else {
                'id':r['intervention_id'],'action':r['action'],'cost_dkk':r['cost_dkk'],
                'annual_savings_kwh':r['estimated_savings_kwh_year'],
                'annual_savings_dkk':r['annual_savings_dkk'],
                'annual_co2_avoided_kg':r['co2_avoided_kg_year'],
                'lifetime_years':r['lifetime_years'],'npv_dkk':r['npv_dkk'],
                'confidence':r['intervention_confidence'],
                'prerequisite_intervention_id':r['prerequisite_intervention_id'],
            })})
    return {'property':dict(prop),'energy_baseline':baseline,'systems':list(systems.values()),
            'coverage':coverage,
            'note':'Illustrative synthetic assets; missing assessments are not evidence of good condition. Interventions reflect condition 3+ and are not procurement specifications.'}


@app.get('/planning/roadmap', tags=['Planning'])
def roadmap(
    annual_budget_dkk: float = Query(default=50_000_000, ge=100_000, le=2_000_000_000),
    start_year: int = Query(default=2027, ge=2027, le=2033),
    end_year: int = Query(default=2030, ge=2027, le=2033),
    strategy: Literal['urgency','energy','value'] = 'urgency',
    energy_price_dkk_kwh: float = Query(default=1.2, ge=.1, le=10),
):
    """Reproducible, constrained greedy investment roadmap with dependencies."""
    if end_year < start_year or end_year - start_year > 6:
        raise HTTPException(status_code=422,detail='End year must follow start year, within a seven-year horizon')
    with read_connection() as conn:
        return plan_roadmap(conn,annual_budget_dkk=annual_budget_dkk,start_year=start_year,
                            end_year=end_year,strategy=strategy,
                            energy_price_dkk_kwh=energy_price_dkk_kwh)


@app.post("/ask", tags=["Natural-language queries"])
def ask(payload: AskRequest):
    """Question -> optional LLM/rules plan -> whitelisted SQL -> verified database rows."""
    try:
        plan, planner = choose_plan(payload.question)
        sql, parameters = build_query(plan)
    except UnsupportedQuestion as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (ValidationError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="Question cannot be mapped to a supported safe query") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    with read_connection() as conn:
        try:
            rows = [dict(r) for r in conn.execute(sql, parameters).fetchall()]
        except sqlite3.Error as exc:
            raise HTTPException(status_code=503, detail="Query execution failed") from exc
    return {
        "question": payload.question,
        "planner": planner,
        "interpreted_plan": plan.model_dump(mode="json", exclude_none=True),
        "verified_answer": explain_results(plan, rows),
        "row_count": len(rows),
        "rows": rows,
        "sql": sql,
        "sql_parameters": parameters,
        "evidence": "Returned rows are computed by read-only SQLite; monetary values are scenario estimates.",
    }
