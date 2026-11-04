# Record the updated two-minute Loom walkthrough

**Screen share only.** Record after launching Docker and ensuring the dashboard has populated. Replace the marked Loom placeholder at the **very top of README** with your real link; do not invent a recording URL.

| Time | Screen | Narration |
|---|---|---|
| 0:00–0:20 | Architecture diagram in README | “A reproducible data pipeline validates imperfect fictional building records, enriches them with systems and assets, and loads an auditable relational database.” |
| 0:20–0:40 | ATLAS overview and asset explorer | “The dashboard computes portfolio investment and priorities from SQLite rather than hard-coded figures.” |
| 0:40–1:05 | Open a property; scroll to Site → Systems → Assets | “Each asset includes an inspection, an estimated quantity, and where indicated, a traceable intervention and lifetime value calculation. Missing assessments are not mistaken for good conditions.” |
| 1:05–1:30 | 2030 Investment plan; change budget or strategy | “A financial controller can compare annual allocations and unfunded backlog under three explicit ranking heuristics, with roof-before-attic dependencies checked.” |
| 1:30–1:50 | Ask intelligence; run “Which interventions save the most energy?” | “Questions become typed query plans, then parameterized SQL; responses show the evidence and planner mode.” |
| 1:50–2:00 | `python -m pytest -q`, briefly show quality report | “Tests verify database integrity, financial reconciliation, security and budget constraints; every figure is labeled synthetic.” |

Before recording, enlarge the browser and terminal typography, check that API keys and other secrets are not displayed, and use `docker compose up --build` from the extracted repository root.
