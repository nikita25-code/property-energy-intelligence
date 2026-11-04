"""Read-only, deterministic budget scenario; a screening heuristic, not an optimizer.

Greedy allocation under an annual cap. Prerequisites are purchased within the same
year if not already funded. No claims of globally optimal investment decisions.
"""
from __future__ import annotations

from .assets import _npv, EMISSIONS_KG_KWH


def plan_roadmap(conn, *, annual_budget_dkk: float, start_year: int = 2027,
                 end_year: int = 2030, strategy: str = 'urgency',
                 energy_price_dkk_kwh: float = 1.2) -> dict:
    data = [dict(row) for row in conn.execute('''
        SELECT i.id, i.property_id, p.name AS property_name, p.building_type,
               a.name AS asset_name, a.condition_score, s.system_type,
               i.action, i.cost_dkk, i.estimated_savings_kwh_year,
               i.co2_avoided_kg_year, i.lifetime_years, i.priority_score,
               i.prerequisite_intervention_id, i.confidence
        FROM interventions i JOIN properties p ON i.property_id=p.id
        JOIN assets a ON a.id=i.asset_id JOIN systems s ON s.id=i.system_id
        ORDER BY i.id
    ''')]
    for row in data:
        row['annual_savings_dkk'] = round(row['estimated_savings_kwh_year'] * energy_price_dkk_kwh, 2)
        row['npv_dkk'] = _npv(row['cost_dkk'], row['annual_savings_dkk'], row['lifetime_years'])
        row['simple_payback_years'] = (round(row['cost_dkk']/row['annual_savings_dkk'], 1)
                                       if row['annual_savings_dkk'] else None)
    by_id = {r['id']: r for r in data}
    if strategy == 'energy':
        ranking = lambda r: (-r['estimated_savings_kwh_year'] / max(1,r['cost_dkk']), -r['priority_score'],r['id'])
    elif strategy == 'value':
        ranking = lambda r: (-r['npv_dkk'] / max(1,r['cost_dkk']), -r['priority_score'],r['id'])
    else:
        ranking = lambda r: (-r['priority_score'], -r['estimated_savings_kwh_year'],r['id'])
    ordered = sorted(data, key=ranking)
    selected_ids: set[str] = set()
    funded = []
    yearly = []
    for year in range(start_year,end_year+1):
        remaining = annual_budget_dkk
        annual = []
        for r in ordered:
            if r['id'] in selected_ids: continue
            prerequisite = r['prerequisite_intervention_id']
            package = []
            if prerequisite and prerequisite not in selected_ids:
                required = by_id.get(prerequisite)
                if not required:
                    continue  # fail closed if corrupted dependency
                package.append(required)
            package.append(r)
            package = [item for item in package if item['id'] not in selected_ids]
            total = sum(item['cost_dkk'] for item in package)
            if total > remaining + 1e-6:
                continue
            for item in package:
                selected_ids.add(item['id'])
                funded.append({'year':year, **item})
                annual.append(item)
            remaining -= total
        yearly.append({
            'year':year,
            'budget_dkk':round(annual_budget_dkk,2),
            'investment_dkk':round(sum(r['cost_dkk'] for r in annual),2),
            'unspent_dkk':round(remaining,2),
            'funded_interventions':len(annual),
            'annual_energy_savings_kwh':round(sum(r['estimated_savings_kwh_year'] for r in annual),2),
            'annual_bill_savings_dkk':round(sum(r['annual_savings_dkk'] for r in annual),2),
            'annual_co2_avoided_kg':round(sum(r['co2_avoided_kg_year'] for r in annual),2),
        })
    return {
        'parameters': {'annual_budget_dkk':annual_budget_dkk,'start_year':start_year,
                       'end_year':end_year,'strategy':strategy,
                       'energy_price_dkk_kwh':energy_price_dkk_kwh},
        'years':yearly,
        'totals': {
            'funded_interventions':len(funded),
            'investment_dkk':round(sum(x['cost_dkk'] for x in funded),2),
            'annual_energy_savings_kwh':round(sum(x['estimated_savings_kwh_year'] for x in funded),2),
            'annual_bill_savings_dkk':round(sum(x['annual_savings_dkk'] for x in funded),2),
            'annual_co2_avoided_kg':round(sum(x['co2_avoided_kg_year'] for x in funded),2),
            'unfunded_interventions':len(data)-len(funded),
            'unfunded_cost_dkk':round(sum(x['cost_dkk'] for x in data if x['id'] not in selected_ids),2),
            'total_available_interventions':len(data),
        },
        'selected_preview':funded[:25],
        'methodology':'Greedy screening allocation, not globally optimized. Dependencies funded before dependents in the same year; no capital carryover. Synthetic quantities, energy and prices; ignores overlapping savings, inflation, sequencing capacity and uncertainty ranges.',
    }
