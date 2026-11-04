# Data dictionary

All fields refer to **fictional assets** for a 2026 scenario. Source files can be regenerated with `python ingest.py --generate`.

## Input CSV: `data/raw/properties_raw.csv`

| Column | Example | Meaning |
|---|---|---|
| `id` | `P00001` | Unique property identifier |
| `name` | `North School 00001 (fictional)` | Display label, not a real institution |
| `building_type` | `School` | School, Library, Sports Facility, Administrative Office, Daycare, Health Clinic |
| `district` | `North` | Fictional North, South, East, West, Central, Harbour |
| `built_year` | `1968` | Four-digit construction year; missing values are imputed |
| `floor_area_m2` | `3200.5` | Gross internal area proxy; missing values are imputed |
| `energy_rating` | `G` | Ordinal A (best) to G (worst), or U (unknown) |
| `last_audit` | `31/10/2024` | Accepted source formats: YYYY-MM-DD, DD/MM/YYYY, YYYY/MM/DD |

## Input CSV: `data/raw/components_raw.csv`

| Column | Example | Meaning |
|---|---|---|
| `id` | `P00001-HVAC` | Unique component identifier |
| `property_id` | `P00001` | Foreign key to properties |
| `component_type` | `HVAC` | HVAC, Insulation, Roof, Windows |
| `condition_score` | `4` | 1 excellent, 2 good, 3 fair, 4 poor, 5 critical |
| `installed_year` | `2000` | Component installation year, imputed from property year if missing |
| `last_serviced` | `2025-04-01` | Last maintenance date, NULL allowed |

Input may include deliberately inconsistent casing, whitespace, empty strings, NULL-like tokens, duplicates and malformed values. The loader writes rejected rows, including their reasons, in `data/reports/`.

## Database: `properties`

Contains normalized source columns plus:

| Field | Meaning |
|---|---|
| `energy_score` | A=1...G=7, SQL NULL if U |
| `year_imputed`, `area_imputed`, `energy_unknown` | 0/1 quality flags |
| `estimated_maintenance_cost_dkk` | Sum of present component-level scenario estimates, DKK |
| `estimated_cost_per_m2_dkk` | Estimated cost divided by property floor area |
| `priority_score` | Interpretive 0-100 relative urgency score |

## Database: `components`

Normalized component identifiers/types/condition/years and dates, plus:

| Field | Meaning |
|---|---|
| `year_imputed` | Installation year copied from property year (0/1) |
| `estimated_maintenance_cost_dkk` | Computed component scenario cost, DKK |
| `intervention_recommended` | At least one derived sub-asset has a scenario intervention cost >0 (0/1) |

`id` is the component primary key; `property_id` is an enforced foreign key. `(property_id, component_type)` is unique. `last_audit` and `last_serviced` are normalized ISO dates stored as text, or SQL NULL.

## Data quality reports

`ingestion_report.json` gives raw vs accepted vs quarantined row counts and key imputation counts. `rejected_properties.csv` and `rejected_components.csv` show the source fields and one explicit `reason`. Do not use a rejected record in analytics.

## Enriched relational schema (v3)

Additional normalized tables appear after source validation and are explicitly **synthetic enrichments**, not additional raw source data.

| Table | Representative fields | Meaning |
|---|---|---|
| `sites` | `id`, `name`, `district` | Fictional campus grouping (up to 3 buildings per group) |
| `systems` | `id`, `property_id`, `source_component_id` | Preserves source-category lineage |
| `assets` | `id`, `system_id`, `name`, `quantity`, `unit`, `unit_cost_dkk`, `condition_score` | Derived modelled physical assets |
| `inspections` | `asset_id`, `inspected_on`, `finding`, `confidence` | One synthetic assessment per asset |
| `interventions` | `asset_id`, `cost_dkk`, `estimated_savings_kwh_year`, `npv_dkk`, `prerequisite_intervention_id` | Proposed quantity-based work, optional dependent action |
| `energy_baselines` | `property_id`, `annual_energy_kwh`, `intensity_kwh_m2_year`, `source` | Synthetic EPC-mapped baseline, not measured |
| `system_coverage` | `property_id`, `system_type`, `status`, `reason` | Assessed / not inspected / not applicable |

Foreign keys are enforced by SQLite. Input records are unchanged; re-running `python ingest.py --generate` creates the entire schema deterministically. See [methodology](asset-model.md).
