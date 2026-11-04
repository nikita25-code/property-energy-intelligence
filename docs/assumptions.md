# Model assumptions, interpretation and limitations

## Scope

This is a **fictional municipal portfolio screening scenario**, as of **2026**, for planning possible retrofits ahead of 2030. It does not assert anything about a specific city's assets, actual EPC compliance rules, tender prices, interventions scheduled for 2030, or quantified savings. Names, districts, condition assessments, dates and energy ratings are generated for demonstration only. No engineering inspections or cost predictions were observed.

## v3 quantity-based component model (current)

The current portfolio cost is the **sum of proposed asset interventions**, each calculated from an explicit synthetic quantity and invented unit price, scaled by condition (3=0.38, 4=0.72, 5=1.0). It no longer uses the original generic `building floor area × component price/m²` as the final cost. For example, a window intervention is based on a *proxy glazing area*, while an air handler is priced by a *proxy number of units*.

- See [v3 asset and investment methodology](asset-model.md) for every asset, unit-rate assumption, energy baseline, savings factor, lifetime, and financial calculation.
- A separate legacy `estimate_component_cost` formula remains in `costs.py` for historical comparison/testing. It does **not** determine the final API and dashboard retrofit costs after enriched ingestion.
- `property_estimated_cost = SUM(component retrofit cost) = SUM(eligible asset intervention cost)`. The portfolio-level DKK/m² is area-weighted across buildings.

**Caveat:** Quantity proxies derived from floor area are not surveys of actual glazing, roof area or equipment counts. None of the rates are tender quotations. No price interval or calibrated prediction is claimed.

## Relative priority score (0–100)

- Energy rating: up to 40 points (`ordinal_energy_score / 7 × 40`, where A=1 and G=7; U is assumed 4 for scoring only).
- Worst component condition: up to 35 points (`worst_condition / 5 × 35`).
- Building age: up to 15 points (`min(age / 80, 1) × 15`).
- Estimated cost intensity: up to 10 points (`min(cost_per_m² / 4500, 1) × 10`).

The sum is rounded to one decimal, capped at 100. High priority is defined for demonstration as **score ≥70**. These are arbitrary weights and cutoffs with no historical validation. A building can score high for several correlated reasons; comparing a real municipal portfolio would require domain-expert calibration and sensitivity analysis.

## Quality handling

- Missing built year: impute the **median within the building type**; record `year_imputed = true`.
- Missing area: impute the **median within the building type**; record `area_imputed = true`.
- Missing rating: represent as `U`; exclude it from average energy score and worst-rated queries. Only for the ranking priority formula does U use a neutral ordinal of 4.
- Missing last-audit / last-serviced dates: store SQL NULL. Valid dates normalize to ISO date. Invalid non-missing dates go to the quarantine file.
- Malformed years or areas: reject, rather than treating malformed data as missing.
- Duplicate IDs: the first **valid** record wins; subsequent instances go into quarantine.
- Child component with no valid parent: quarantine with reason. Missing component observations are not automatically fabricated in ingestion.
- Energy ordinal averages are a rough display convenience. The arithmetic mean of letter grades is **not a meaningful measure of actual kWh/m²/year**.

## Before deploying with actual data

Require documented source authority, source licenses, address/property identity resolution, real net and gross floor area, physical component quantities, labor/material price baselines (incl. tender year and geography), VAT treatment, lifecycle assumptions, climate impacts, audit trails, calibrated confidence intervals, real energy measurements, and an engineering-led review of compliance and urgency logic. Protect any personal or restricted building data and add authentication and monitoring.
