# Interactive frontend — architecture and verification

**Entry point:** `http://localhost:8000/` after `docker compose up --build`. Swagger UI stays at `/docs`.

This is a **real, same-origin frontend**, not a static screenshot. It is intentionally built in plain HTML/CSS/JavaScript for zero build-step friction. All displayed portfolio counts, chart proportions, property rows, cost figures and assistant responses come from FastAPI endpoints. The synthetic dataset is reset to seed 42 every Docker startup for repeatable demonstrations.

## Views

| View | API source | Behavior |
|---|---|---|
| Overview | `/analytics/summary`, `/analytics/breakdown`, `/properties?page_size=5&sort=priority` | Four live KPIs; grade counts; cost breakdown by building type; five-item watchlist; honest data-quality flags |
| Property explorer | `/properties` | Search name or ID, filter type/district/rating/priority, sort by priority/cost/energy/name/year, paginate 12 rows at a time |
| Property drawer | `/properties/{id}` | Drill into cost per m², area, priority, four components, condition and imputed fields |
| Ask intelligence | `/ask` | Supported natural-language questions; retrieved database rows, executed SQL, bound parameters, validated plan and planner name |
| Methodology | N/A | Scope, limitations and model interpretation |

Data is never written through the frontend. All database connections use read-only SQLite, backed by restricted parameterized SQL. UI text is escaped before HTML insertion; user queries and filters are validated server-side. No third-party scripts, user tracking or persistent browser storage are used.

## Start

```sh
docker compose up --build
```

Open `http://localhost:8000/` for the dashboard. You do **not** need to run `npm` or `npm run dev`. To stop use `Ctrl+C` or `docker compose down`. After you update frontend files, run `docker compose up --build` again to rebuild the container.

## API contracts added for frontend

- `GET /analytics/breakdown`: categorical counts and assumption-based cost sums for energy grades, building types, districts, components and priority bands.
- `GET /properties`: `q`, `building_type`, `district`, `energy_rating`, `priority`, `sort`, `page`, `page_size` query parameters. All value filters are bound; sort options are restricted to an allowlist; page size maximum is 100.

## Verify

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The dashboard tests ensure its assets are served, aggregations reconcile against `/analytics/summary`, pagination is stable and search/filter values do not execute SQL. The JavaScript was also exercised in Chromium against real response payloads using a local API mock, including narrow-screen navigation, property detail and natural-language results. This is not a substitute for checking the final Docker UI on the target computer.

## Limitations

The app is a **portfolio screening demonstration**. All records are fictional and all cost/priority calculations are illustrative. "AI" names the optional question-intent planning capability, not a machine-learning retrofit-cost predictor. `PLANNER_MODE=rules` is deterministic/offline by default, and real model inference requires separately configuring an API key. The demo is for localhost and does not include authentication or rate limiting.

## v3 portfolio decisions

The **2030 investment plan** tab fetches `/planning/roadmap` with a DKK annual cap, ranking strategy and assumed energy price. It draws per-year allocation bars, scenario KPIs, and a 25-row preview of the funded interventions. Numbers are returned by the backend, not fabricated in JavaScript; all assumptions and omissions are visible on the screen.

Clicking a property also fetches `/properties/{property_id}/assets` and displays the **Site → System → Asset → Inspection → Intervention** structure, with quantities, condition, lifetime value, modeled savings, prerequisite IDs and assessment coverage. The old system-level component summary is kept for comparison. The UI distinguishes missing inspections from legitimately not-applicable systems.

New rules-based NL intents answer which asset observations have the worst condition, which interventions save the most annual energy, and which have the highest modelled NPV. All return bound-query evidence and a deterministic narration.
