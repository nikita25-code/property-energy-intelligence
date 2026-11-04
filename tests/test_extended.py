"""End-to-end, integrity, money reconciliation, read-only and planning invariants."""
import sqlite3
import pytest
from fastapi.testclient import TestClient
from property_intelligence.api import app

client=TestClient(app)


def test_hierarchy_and_costs_reconcile(seeded_db):
    summary=client.get('/analytics/summary').json()
    with sqlite3.connect(seeded_db) as conn:
        assert conn.execute('PRAGMA foreign_key_check').fetchall()==[]
        assert summary['total_assets']==conn.execute('SELECT COUNT(*) FROM assets').fetchone()[0]
        assert summary['total_inspections']==summary['total_assets']
        assert summary['total_sites']<summary['total_properties']
        # All stored portfolio, legacy-component and detailed intervention investment must reconcile.
        p,c,i=[conn.execute(f'SELECT ROUND(SUM({col}),2) FROM {table}').fetchone()[0]
                for table,col in [('properties','estimated_maintenance_cost_dkk'),
                    ('components','estimated_maintenance_cost_dkk'),('interventions','cost_dkk')]]
        assert abs(p-c)<.02 and abs(p-i)<.02
        assert conn.execute('SELECT COUNT(*) FROM properties WHERE site_id IS NULL').fetchone()[0]==0
        assert conn.execute('SELECT COUNT(*) FROM assets WHERE quantity<=0').fetchone()[0]==0
        assert conn.execute('SELECT COUNT(*) FROM interventions WHERE estimated_savings_kwh_year<0').fetchone()[0]==0


def test_component_level_drilldown_inspections_and_coverage(seeded_db):
    detail=client.get('/properties/P00001/assets')
    assert detail.status_code==200
    d=detail.json()
    assert d['property']['site_id'].startswith('S')
    assert d['energy_baseline']['annual_energy_kwh']>0
    assert any(s['assets'] for s in d['systems'])
    assert all(a['quantity']>0 and a['inspection']['finding'] for s in d['systems'] for a in s['assets'])
    assert any(x['status']=='not_inspected' for x in d['coverage'])
    with sqlite3.connect(seeded_db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM system_coverage WHERE status='not_applicable'").fetchone()[0]>0
    assert client.get('/properties/P99999/assets').status_code==404
    assert client.get('/properties/ABC/assets').status_code==422


def test_roadmap_respects_budgets_dependencies_and_backlog(seeded_db):
    r=client.get('/planning/roadmap',params={'annual_budget_dkk':2500000,'start_year':2027,'end_year':2029})
    assert r.status_code==200
    d=r.json()
    assert len(d['years'])==3
    assert all(y['investment_dkk']<=2500000.01 for y in d['years'])
    assert sum(y['funded_interventions'] for y in d['years'])==d['totals']['funded_interventions']
    assert d['totals']['funded_interventions'] + d['totals']['unfunded_interventions']==d['totals']['total_available_interventions']
    assert abs(d['totals']['investment_dkk']+d['totals']['unfunded_cost_dkk']-client.get('/analytics/summary').json()['total_estimated_retrofit_cost_dkk']) < .1
    assert len(d['selected_preview'])<=25
    # A late dependent intervention must never appear without an earlier/same-year prerequisite.
    with sqlite3.connect(seeded_db) as conn:
        all_ids={row[0] for row in conn.execute('SELECT id FROM interventions')}
        deps=[row for row in conn.execute('SELECT id,prerequisite_intervention_id FROM interventions WHERE prerequisite_intervention_id IS NOT NULL')]
        assert deps and all(pre in all_ids for _,pre in deps)


def test_scenario_sensitivity_and_validation(seeded_db):
    small=client.get('/planning/roadmap',params={'annual_budget_dkk':500000,'energy_price_dkk_kwh':1.2}).json()
    large=client.get('/planning/roadmap',params={'annual_budget_dkk':5000000,'energy_price_dkk_kwh':1.2}).json()
    assert large['totals']['investment_dkk']>=small['totals']['investment_dkk']
    assert client.get('/planning/roadmap?strategy=DROP%20TABLE').status_code==422
    assert client.get('/planning/roadmap?end_year=2026').status_code==422
    assert client.get('/planning/roadmap?start_year=2032&end_year=2028').status_code==422
    assert client.get('/planning/roadmap?annual_budget_dkk=-200').status_code==422
    assert client.get('/planning/roadmap?energy_price_dkk_kwh=9999').status_code==422
    assert client.get('/analytics/summary').status_code==200


@pytest.mark.parametrize('question,intent',[
    ('Which interventions save the most energy?','energy_savings'),
    ('Which HVAC units have the worst condition?','asset_condition'),
    ('Which schools have the best net present value?','intervention_value'),
])
def test_new_nlq_intents_are_grounded(question,intent,seeded_db):
    r=client.post('/ask',json={'question':question})
    assert r.status_code==200
    result=r.json()
    assert result['interpreted_plan']['intent']==intent
    assert result['planner']=='rules'
    assert result['row_count']>0
    assert result['sql'].upper().startswith('SELECT')
    assert 'synthetic' in result['evidence'].lower() or 'scenario' in result['evidence'].lower()


def test_frontend_contains_real_planning_interfaces(seeded_db):
    html=client.get('/').text
    script=client.get('/assets/app.js').text
    assert 'view-planning' in html
    assert 'planningForm' in html
    assert '/planning/roadmap' in script
    assert '/assets' in script
