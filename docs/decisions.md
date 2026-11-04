# Architectural decisions / trade-offs

**ADR 001 — SQLite over hosted warehouse.** A file database removes setup, cloud cost, network credentials and demo fragility. Foreign keys, indexes, atomic rebuild and parameterized queries provide meaningful backend practice. A production multi-user service could move to PostgreSQL, with migrations and managed backups.

**ADR 002 — Synthetic-but-messy data over scraped real addresses.** A deterministic generator makes tests and screenshots reproducible and avoids privacy, ownership and licensing issues. It deliberately tests invalid/NULL handling. The trade-off is no real predictive credibility; actual results are not externally meaningful.

**ADR 003 — Constrained query plans over free-form text-to-SQL.** The optional model produces only a typed intent and approved filters, and the application composes known safe SQL. This sharply limits question coverage, but protects the demo from unrestricted SQL execution and makes tests possible. Unknown questions are rejected rather than guessed.

**ADR 004 — Rule-based default, optional hosted LLM.** Free offline operation works for recruiters without an API key. The optional LLM demonstrates a structured-model integration without requiring anyone to pay to run the project. Any actual hosted inference must be funded, monitored and evaluated separately.

**ADR 005 — Explainable scenario costing over fake machine learning.** A formula with declared unit rates, condition multipliers and a visible score is inspectable. There are no labeled training examples, so a 'predicted' cost from an ML model would be misleading. When suitable historical tender costs become available, calibrated regression plus uncertainty bounds would be a credible next step.

**ADR 006 — Read-only analytics API.** `/ask` and other endpoints cannot write to the database. The connection is opened in SQLite read-only mode with `query_only` set. There is no authorization or internet-facing deployment claim; security hardening is a future milestone.

**ADR 007 — Atomic database replacement + quarantine.** Clean output is built in a separate file and only replaces the last valid database after referential-integrity checks. Rejected inputs are reported, and meaningful bad data never silently becomes valid. In a continuously available system, ingestion and query workloads would use migrations, versioned snapshots, and staged publication rather than replacing an open database file.

## v3 ADR — Preserve source lineage; enrich after validation

**Decision:** Retain the original `components` and public API for backward compatibility; derive `sites`, `systems`, `assets`, `inspections`, `interventions`, energy baselines and coverage *after* validating source CSVs. The final building and source-component investment figures are reconciled with the sum of sub-asset intervention costs inside the same temporary SQLite database, then atomically published. This avoids silently treating synthetic augmentation as source observations. Detailed assumptions are in [asset-model.md](asset-model.md).

**Trade-off:** Source records have only four category observations; derived asset quantity and cost assumptions are not engineering surveys. Existing source reports remain meaningful while detailed data are explicitly synthetic.

## v3 ADR — Auditable, bounded planning rather than spurious optimization

**Decision:** Use a fixed-annual-budget greedy screening allocator with deterministic sorting, optional urgency/energy/NPV objective, and same-year prerequisite purchasing for attic insulation when the roof is in poor condition. Sensitivity is represented by an assumed energy price input, never a forecast.

**Trade-off:** This model deliberately does not claim global optimality or solve contractor sequencing, correlated savings, legal compliance, uncertainty bands or real project feasibility. Each limitation is surfaced in the dashboard and API response.
