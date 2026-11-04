"""Deterministic *illustrative* asset hierarchy and investment assumptions.

Not a physical energy simulation, statutory EPC assessment or cost prediction.
Derived entirely from cleaned fictional property/component observations.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
import math
import sqlite3

from .costs import property_priority_score

ENERGY_INTENSITY_KWH_M2 = {"A": 65, "B": 95, "C": 125, "D": 160,
                           "E": 205, "F": 260, "G": 330, "U": 160}
BASE_ENERGY_PRICE = 1.20  # DKK/kWh, illustrative not a tariff
EMISSIONS_KG_KWH = 0.08  # illustrative, NOT Danish official factor
DISCOUNT_RATE = 0.04

# name, quantity expression key, fraction/m2 or m2 per unit, DKK/unit, energy saving fraction, lifetime
ASSET_SPEC = {
    "HVAC": [
        ("Heating plant", "unit_per_area", 1400, 185000, .12, 18),
        ("Air handling unit", "unit_per_area", 1800, 148000, .09, 18),
        ("BMS controls", "unit_per_area", 3200, 58000, .025, 12),
    ],
    "Insulation": [
        ("Facade insulation", "area_share", .46, 1020, .07, 30),
        ("Attic insulation", "area_share", .34, 530, .05, 30),
    ],
    "Roof": [
        ("Roof covering", "area_share", .34, 875, 0, 25),
        ("Drainage", "unit_per_area", 2500, 19000, 0, 20),
    ],
    "Windows": [
        ("Window glazing", "area_share", .17, 1650, .065, 25),
        ("External doors", "unit_per_area", 900, 32000, .015, 25),
    ],
}

EXTENDED_SQL = """
PRAGMA foreign_keys = ON;
CREATE TABLE sites (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, district TEXT NOT NULL,
    building_type TEXT NOT NULL
);
CREATE TABLE systems (
    id TEXT PRIMARY KEY, property_id TEXT NOT NULL REFERENCES properties(id),
    system_type TEXT NOT NULL, source_component_id TEXT NOT NULL REFERENCES components(id),
    coverage_status TEXT NOT NULL CHECK (coverage_status = 'assessed')
);
CREATE TABLE assets (
    id TEXT PRIMARY KEY, property_id TEXT NOT NULL REFERENCES properties(id),
    system_id TEXT NOT NULL REFERENCES systems(id), name TEXT NOT NULL,
    quantity REAL NOT NULL CHECK(quantity > 0), unit TEXT NOT NULL,
    unit_cost_dkk REAL NOT NULL CHECK(unit_cost_dkk >= 0),
    condition_score INTEGER NOT NULL CHECK(condition_score BETWEEN 1 AND 5),
    installed_year INTEGER NOT NULL,
    source TEXT NOT NULL DEFAULT 'synthetic_estimate'
);
CREATE TABLE inspections (
    id TEXT PRIMARY KEY, asset_id TEXT NOT NULL REFERENCES assets(id),
    inspected_on TEXT, condition_score INTEGER NOT NULL CHECK(condition_score BETWEEN 1 AND 5),
    finding TEXT NOT NULL, confidence TEXT NOT NULL
);
CREATE TABLE interventions (
    id TEXT PRIMARY KEY, asset_id TEXT NOT NULL REFERENCES assets(id),
    property_id TEXT NOT NULL REFERENCES properties(id),
    system_id TEXT NOT NULL REFERENCES systems(id),
    action TEXT NOT NULL, cost_dkk REAL NOT NULL CHECK(cost_dkk >= 0),
    estimated_savings_kwh_year REAL NOT NULL CHECK(estimated_savings_kwh_year >= 0),
    annual_savings_dkk REAL NOT NULL CHECK(annual_savings_dkk >= 0),
    co2_avoided_kg_year REAL NOT NULL CHECK(co2_avoided_kg_year >= 0),
    lifetime_years INTEGER NOT NULL,
    npv_dkk REAL NOT NULL,
    confidence TEXT NOT NULL CHECK(confidence IN ('Low','Medium')),
    prerequisite_intervention_id TEXT REFERENCES interventions(id),
    priority_score REAL NOT NULL CHECK(priority_score BETWEEN 0 AND 100)
);
CREATE TABLE energy_baselines (
    property_id TEXT PRIMARY KEY REFERENCES properties(id),
    intensity_kwh_m2_year REAL NOT NULL,
    annual_energy_kwh REAL NOT NULL,
    assumed_price_dkk_kwh REAL NOT NULL,
    emissions_factor_kg_kwh REAL NOT NULL,
    source TEXT NOT NULL DEFAULT 'rating_mapped_synthetic_assumption'
);
CREATE TABLE system_coverage (
    property_id TEXT NOT NULL REFERENCES properties(id),
    system_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('assessed','not_inspected','not_applicable')),
    reason TEXT NOT NULL, PRIMARY KEY(property_id,system_type)
);
CREATE INDEX idx_assets_property ON assets(property_id);
CREATE INDEX idx_inspections_asset ON inspections(asset_id);
CREATE INDEX idx_interventions_property ON interventions(property_id);
CREATE INDEX idx_interventions_priority ON interventions(priority_score DESC, id);
CREATE INDEX idx_interventions_asset ON interventions(asset_id);
CREATE INDEX idx_systems_property ON systems(property_id);
"""


def _quantity(area_m2: float, style: str, factor: float) -> tuple[float, str]:
    if style == 'area_share':
        return round(max(10, area_m2 * factor), 2), 'm2'
    return float(max(1, math.ceil(area_m2 / factor))), 'unit'


def _npv(cost: float, annual_savings: float, life: int, rate: float = DISCOUNT_RATE) -> float:
    multiplier = (1 - (1 + rate) ** -life) / rate if rate else life
    return round(-cost + annual_savings * multiplier, 2)


def _conditions(base: int, name: str) -> int:
    # Differentiates sub-asset condition without random fluctuations
    delta = {'BMS controls': -1, 'Drainage': -1, 'External doors': -1,
             'Attic insulation': 1, 'Roof covering': 0}.get(name, 0)
    return max(1, min(5, base + delta))


def populate_extended_model(conn: sqlite3.Connection) -> dict:
    """Called in the same transaction as base CSV ingestion. No external datasets."""
    conn.executescript(EXTENDED_SQL)
    conn.execute('ALTER TABLE properties ADD COLUMN site_id TEXT REFERENCES sites(id)')
    props = [dict(zip([d[0] for d in conn.execute('SELECT * FROM properties LIMIT 0').description], row))
             for row in conn.execute('SELECT * FROM properties ORDER BY id')]
    comp_rows = conn.execute('SELECT * FROM components ORDER BY property_id, component_type').fetchall()
    component_cols = [d[0] for d in conn.execute('SELECT * FROM components LIMIT 0').description]
    components_by_property: dict[str, list[dict]] = defaultdict(list)
    for row in comp_rows:
        component = dict(zip(component_cols, row))
        components_by_property[component['property_id']].append(component)

    site_seq: dict[tuple[str,str],int] = defaultdict(int)
    site_assignments: dict[tuple[str,str,int],str] = {}
    sites = []
    site_updates = []
    baselines = []
    coverage = []
    systems = []
    assets = []
    inspections = []
    interventions = []
    component_cost_updates = []
    property_cost_updates = []
    dependencies: dict[str, str] = {}  # property -> roof covering intervention
    attic_candidates: list[tuple[str, str]] = []

    for p in props:
        pid = p['id']
        key = (p['district'],p['building_type'])
        bucket = site_seq[key] // 3
        site_seq[key] += 1
        skey = (*key, bucket)
        if skey not in site_assignments:
            sid = f'S{len(sites)+1:05d}'
            site_assignments[skey] = sid
            sites.append((sid, f'{p["district"]} {p["building_type"]} campus {bucket+1:03d} (fictional)', *key))
        site_updates.append((site_assignments[skey], pid))

        baseline_intensity = ENERGY_INTENSITY_KWH_M2[p['energy_rating']]
        energy_kwh = round(p['floor_area_m2'] * baseline_intensity, 2)
        baselines.append((pid, baseline_intensity, energy_kwh, BASE_ENERGY_PRICE,
                          EMISSIONS_KG_KWH, 'rating_mapped_synthetic_assumption'))
        has = {c['component_type']: c for c in components_by_property[pid]}
        coverage_types = ('Heating', 'Ventilation', 'Building automation', 'Cooling',
                          'Insulation', 'Roof', 'Windows', 'Electrical')
        mapping = {'Heating':'HVAC','Ventilation':'HVAC','Building automation':'HVAC',
                   'Insulation':'Insulation','Roof':'Roof','Windows':'Windows'}
        for category in coverage_types:
            if category in mapping:
                present = mapping[category] in has
                state = 'assessed' if present else 'not_inspected'
                reason = 'Derived from validated synthetic component' if present else 'No validated component record; do not treat as good condition'
            elif category == 'Cooling' and p['building_type'] not in ('Sports Facility', 'Health Clinic'):
                state, reason = 'not_applicable', 'Cooling not represented in this illustrative building profile'
            else:
                state, reason = 'not_inspected', 'No source assessment available'
            coverage.append((pid, category, state, reason))
        total_cost = 0
        max_condition = 1
        cost_by_component: dict[str,float] = {}
        for comp in components_by_property[pid]:
            system_id = f'SYS-{comp["id"]}'
            systems.append((system_id, pid, comp['component_type'], comp['id'], 'assessed'))
            component_cost = 0
            for index, (name, quantity_style, factor, unit_price, energy_share, life) in enumerate(ASSET_SPEC[comp['component_type']], start=1):
                aid = f'AST-{comp["id"]}-{index:02d}'
                qty, unit = _quantity(p['floor_area_m2'], quantity_style, factor)
                condition = _conditions(comp['condition_score'], name)
                max_condition = max(max_condition, condition)
                assets.append((aid, pid, system_id, name, qty, unit, float(unit_price), condition,
                               comp['installed_year'], 'synthetic_estimate'))
                confidence = 'Low' if (p['year_imputed'] or p['area_imputed'] or p['energy_unknown'] or comp['year_imputed']) else 'Medium'
                observations = {1:'Excellent visible condition',2:'Minor wear observed',3:'Moderate deterioration',
                                4:'Significant wear observed',5:'Critical wear indicated'}
                inspections.append((f'INSP-{aid}', aid, comp['last_serviced'], condition,
                                    observations[condition] + ' (fictional assessment)', confidence))
                if condition < 3:
                    continue
                # Explicit quantity x unit rate x intervention/condition multiplier; never floor-area x generic system rate.
                multiplier = {3: .38, 4: .72, 5: 1.0}[condition]
                cost = round(qty * unit_price * multiplier, 2)
                savings_kwh = round(energy_kwh * energy_share * ({3:.55,4:.85,5:1.0}[condition]), 2)
                annual_dkk = round(savings_kwh * BASE_ENERGY_PRICE, 2)
                co2 = round(savings_kwh * EMISSIONS_KG_KWH, 2)
                i_id = f'INT-{aid}'
                score = round(min(100, p['priority_score'] * .70 + condition * 6.0), 1)
                action = 'Repair or replace ' + name.lower()
                interventions.append((i_id, aid, pid, system_id, action, cost, savings_kwh,
                                      annual_dkk, co2, life, _npv(cost,annual_dkk,life), confidence,
                                      None, score))
                component_cost += cost
                if name == 'Roof covering' and condition >= 4:
                    dependencies[pid] = i_id
                if name == 'Attic insulation':
                    attic_candidates.append((i_id, pid))
            component_cost = round(component_cost, 2)
            component_cost_updates.append((component_cost, int(component_cost > 0), comp['id']))
            cost_by_component[comp['id']] = component_cost
            total_cost += component_cost
        total_cost = round(total_cost, 2)
        per_m2 = round(total_cost / p['floor_area_m2'], 2)
        priority = property_priority_score(rating=p['energy_rating'],year_built=p['built_year'],
                                           max_condition=max_condition,cost_per_m2=per_m2)
        property_cost_updates.append((total_cost,per_m2,priority,pid))

    conn.executemany('INSERT INTO sites VALUES (?,?,?,?)', sites)
    conn.executemany('UPDATE properties SET site_id=? WHERE id=?',site_updates)
    conn.executemany('INSERT INTO energy_baselines VALUES (?,?,?,?,?,?)',baselines)
    conn.executemany('INSERT INTO system_coverage VALUES (?,?,?,?)',coverage)
    conn.executemany('INSERT INTO systems VALUES (?,?,?,?,?)',systems)
    conn.executemany('INSERT INTO assets VALUES (?,?,?,?,?,?,?,?,?,?)',assets)
    conn.executemany('INSERT INTO inspections VALUES (?,?,?,?,?,?)',inspections)
    conn.executemany('INSERT INTO interventions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',interventions)
    deps = [(dependencies[pid], iid) for iid,pid in attic_candidates if pid in dependencies]
    conn.executemany('UPDATE interventions SET prerequisite_intervention_id=? WHERE id=?',deps)
    conn.executemany('UPDATE components SET estimated_maintenance_cost_dkk=?,intervention_recommended=? WHERE id=?',component_cost_updates)
    conn.executemany('UPDATE properties SET estimated_maintenance_cost_dkk=?,estimated_cost_per_m2_dkk=?,priority_score=? WHERE id=?',property_cost_updates)
    # Correct asset-intervention ranking to use FINAL building priority, not temporary legacy score.
    conn.execute('''UPDATE interventions SET priority_score = MIN(100, ROUND(
        (SELECT priority_score FROM properties p WHERE p.id=interventions.property_id) * .7
        + (SELECT condition_score FROM assets a WHERE a.id=interventions.asset_id) * 6, 1))''')
    return {'sites':len(sites), 'systems':len(systems),'assets':len(assets),
            'inspections':len(inspections),'interventions':len(interventions),'prerequisites':len(deps)}
