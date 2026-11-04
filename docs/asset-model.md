# v3 — Asset-level data model & decision logic

**All data are fictional.** No physical surveys, energy measurements, building addresses, tender unit rates, engineering estimates or statutory 2030 classifications are represented.

## Relational model

| Table | Grain and keys | Purpose |
|---|---|---|
| `sites` | one site ID, usually 1–3 fictional buildings | Group buildings by district and type in reproducible campus-like clusters |
| `properties` | one building (`P00001`); `site_id` FK | Source attributes, imputation flags, priority and cost totals |
| `components` | one validated original system-category observation per building | Backward-compatible API and source lineage |
| `systems` | one parent component per system | Allows grouping the derived sub-assets under HVAC/insulation/roof/windows |
| `assets` | one named sub-asset per observed system | Quantity, unit, assumed price, installation year, condition |
| `inspections` | one synthetic condition event per asset | Finding, last inspection proxy, assessment confidence |
| `interventions` | optional proposed work per asset (condition ≥ 3) | Cost, expected yearly savings, CO₂ proxy, NPV, optional dependency |
| `energy_baselines` | one baseline per building | Rating-mapped annual kWh; **not a meter reading** |
| `system_coverage` | one building/system category | Distinguishes **assessed**, **not_inspected**, **not_applicable** |

`systems`, `assets`, `inspections`, `interventions` and coverages are generated *after* the source CSVs have been cleaned and validated. The detailed quantities, condition differences, financial assumptions and inspection findings are **synthetic enrichments**, not hidden real source observations. Missing source components produce `not_inspected`, not zero-condition assets.

### Demonstration quantities and rates

| Asset | Quantity proxy | 2026 assumed rate | Life (years) |
|---|---|---:|---:|
| Heating plant | 1 per 1,400 m², rounded up | DKK 185,000 / unit | 18 |
| Air handling unit | 1 per 1,800 m², rounded up | DKK 148,000 / unit | 18 |
| BMS controls | 1 per 3,200 m² | DKK 58,000 / unit | 12 |
| Facade insulation | 46% of floor area, as proxy m² | DKK 1,020 / m² | 30 |
| Attic insulation | 34% of floor area, as proxy m² | DKK 530 / m² | 30 |
| Roof covering | 34% of floor area, as proxy m² | DKK 875 / m² | 25 |
| Roof drainage | 1 per 2,500 m² | DKK 19,000 / unit | 20 |
| Window glazing | 17% of floor area, as proxy m² | DKK 1,650 / m² | 25 |
| External doors | 1 per 900 m² | DKK 32,000 / unit | 25 |

These are **transparent sizing proxies**, not surveyed geometry. For a real municipality, envelope dimensions, installed units, specification and measured flow should replace them. The unit costs are invented for comparative demonstrations, not Danish contractor quotations.

An intervention is created for asset condition ≥3. Its capital cost is `quantity × unit_rate × condition_factor` where the factor is 0.38 (condition 3), 0.72 (4), 1.0 (5). All component and building retrofit costs are recalculated as **sums of eligible asset interventions**, ensuring reconciliation with portfolio totals. A system with no intervention has a modeled zero investment but remains assessed; unassessed systems are explicitly separate.

## Energy and value assumptions

Annual baseline energy = `building floor area × fictional kWh/m² mapped to rating` with: A=65, B=95, C=125, D=160, E=205, F=260, G=330, unknown=160. These are **invented scenario values** and energy class is never treated as measured usage.

Intervention energy reductions are bounded fixed shares of that baseline: heating plant 12%, air handling 9%, BMS 2.5%, facade insulation 7%, attic insulation 5%, window glazing 6.5%, doors 1.5%, and **roof covering / drainage 0%**. They are further scaled by condition (3: 55%, 4: 85%, 5: 100%). Shares are illustrative and may overlap physically; **summing them is not a validated prediction**. Total shares per building remain below baseline but are not dynamically netted against one another.

Annual cost saving = `annual kWh saved × illustrative DKK 1.20/kWh`, and a **hypothetical** emissions estimate uses 0.08 kg/kWh. Neither constant is an official price, tariff or emissions factor.

NPV = `−capital cost + discounted sum of annual savings` at 4% over each asset's modeled life; the roadmap recalculates annual bill savings and NPV when the user changes the assumed energy price. Maintenance savings, residual values, VAT, taxes, capacity constraints, inflation, financing, deterioration and uncertain price trajectories are omitted. A negative NPV is possible, and safety repairs may still be important.

## Planning algorithm

`GET /planning/roadmap` greedily ranks proposed interventions by:

- **urgency**: asset priority score descending (not safety-calibrated)
- **energy**: assumed annual energy kWh saved per invested DKK
- **value**: assumed NPV per invested DKK

It selects items up to a fixed **annual** spending cap for each year in the chosen window. A selected attic-insulation intervention with a seriously degraded roof is bundled with its roof-covering prerequisite, and both must fit the cap in the same year unless the roof has already been funded. Investments are not double counted and funding is never carried forward. Output includes annual budgets, funded intervention counts, the implied full-year savings after funding, and unfunded backlog. Results are **not globally optimized** and don't imply that all measures can be constructed in one year.

**Important caveat:** Annual savings shown per funding year are the incremental expected annual run-rate from *that year's funded measures*, not accumulated multi-year energy savings and not a physical engineering simulation. This screen does not determine actual EPC directive compliance or deadlines.

## Verification and limitations

- All keys have foreign-key constraints; raw source rejects are quarantined; final database is atomically replaced only after successful validation.
- Portfolio investment equals the sum of component costs and proposed interventions; tests assert the reconciliation.
- `/ask` returns only rows from parameterized, preapproved read-only SQL; optional LLM produces only a typed intent, never raw executable SQL.
- Confidence is `Low` if material original fields were imputed or the rating is unknown; otherwise `Medium`. **It is never `High`** because no field survey was performed.
- Missing assessments, `not_applicable`, and condition=1 are distinct states.
- No real estate ownership, permitted address, detailed engineering or regulatory data are provided. There is no production login, role security or cost sensitivity band yet.
