"""CSV -> validated / normalized records -> relational SQLite -> audit report."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, datetime, timezone
import json
from pathlib import Path
import sqlite3
from statistics import median

from pydantic import ValidationError

from .costs import estimate_component_cost, property_priority_score
from .assets import populate_extended_model
from .generator import generate_dataset
from .models import ComponentRecord, PropertyRecord
from .settings import AS_OF_YEAR, BUILDING_TYPES, COMPONENT_TYPES, DATA_DIR, DB_PATH

MISSING = {"", "null", "unknown", "n/a", "na", "-", "none"}

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
CREATE TABLE properties (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    building_type TEXT NOT NULL,
    district TEXT NOT NULL,
    built_year INTEGER NOT NULL CHECK (built_year BETWEEN 1850 AND 2026),
    floor_area_m2 REAL NOT NULL CHECK (floor_area_m2 > 0),
    energy_rating TEXT NOT NULL CHECK (energy_rating IN ('A','B','C','D','E','F','G','U')),
    energy_score INTEGER CHECK (energy_score BETWEEN 1 AND 7),
    last_audit TEXT,
    year_imputed INTEGER NOT NULL,
    area_imputed INTEGER NOT NULL,
    energy_unknown INTEGER NOT NULL,
    estimated_maintenance_cost_dkk REAL NOT NULL CHECK (estimated_maintenance_cost_dkk >= 0),
    estimated_cost_per_m2_dkk REAL NOT NULL CHECK (estimated_cost_per_m2_dkk >= 0),
    priority_score REAL NOT NULL CHECK (priority_score BETWEEN 0 AND 100)
);
CREATE TABLE components (
    id TEXT PRIMARY KEY,
    property_id TEXT NOT NULL REFERENCES properties(id),
    component_type TEXT NOT NULL CHECK (component_type IN ('HVAC','Insulation','Roof','Windows')),
    condition_score INTEGER NOT NULL CHECK (condition_score BETWEEN 1 AND 5),
    installed_year INTEGER NOT NULL,
    last_serviced TEXT,
    year_imputed INTEGER NOT NULL,
    estimated_maintenance_cost_dkk REAL NOT NULL CHECK (estimated_maintenance_cost_dkk >= 0),
    intervention_recommended INTEGER NOT NULL,
    UNIQUE(property_id, component_type)
);
CREATE INDEX idx_properties_type_year ON properties(building_type, built_year);
CREATE INDEX idx_properties_energy_priority ON properties(energy_score DESC, priority_score DESC);
CREATE INDEX idx_properties_priority ON properties(priority_score DESC);
CREATE INDEX idx_components_type_cost ON components(component_type, estimated_maintenance_cost_dkk DESC);
CREATE INDEX idx_components_property ON components(property_id);
"""


def is_missing(value: object) -> bool:
    return str(value if value is not None else "").strip().lower() in MISSING


def normalized_date(value: str) -> date | None:
    if is_missing(value):
        return None
    for pattern in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value.strip(), pattern).date()
        except ValueError:
            pass
    raise ValueError(f"Unrecognized date format: {value!r}")


def _rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run 'python ingest.py --generate' to create demo data.")
    with path.open(newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def _median_by_type(rows: list[dict[str, str]], column: str) -> dict[str, float]:
    valid: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if row.get("building_type") not in BUILDING_TYPES or is_missing(row.get(column)):
            continue
        try:
            value = float(row[column])
            if (1850 <= value <= AS_OF_YEAR) if column == "built_year" else (0 < value <= 100000):
                valid[row["building_type"]].append(value)
        except (ValueError, TypeError):
            pass
    if not valid:
        raise ValueError(f"No valid reference values for {column}; cannot impute")
    overall = median(v for sample in valid.values() for v in sample)
    return {kind: median(valid[kind]) if kind in valid else overall for kind in BUILDING_TYPES}


def clean_properties(raw: list[dict[str, str]]) -> tuple[dict[str, PropertyRecord], list[dict[str, str]], Counter]:
    years = _median_by_type(raw, "built_year")
    areas = _median_by_type(raw, "floor_area_m2")
    accepted: dict[str, PropertyRecord] = {}
    rejected: list[dict[str, str]] = []
    counters: Counter = Counter()
    for row in raw:
        try:
            pid = (row.get("id") or "").strip().upper()
            if pid in accepted:
                raise ValueError("Duplicate property ID (valid first record retained)")
            kind = (row.get("building_type") or "").strip()
            year_imputed = is_missing(row.get("built_year"))
            area_imputed = is_missing(row.get("floor_area_m2"))
            year = round(years[kind]) if year_imputed else int(row["built_year"])
            area = areas[kind] if area_imputed else float(row["floor_area_m2"])
            rating = (row.get("energy_rating") or "").strip().upper()
            rating = "U" if is_missing(rating) else rating
            obj = PropertyRecord.model_validate({
                "id": pid, "name": (row.get("name") or "").strip(),
                "building_type": kind,
                "district": (row.get("district") or "").strip(),
                "built_year": year,
                "floor_area_m2": round(area, 2),
                "energy_rating": rating,
                "last_audit": normalized_date(row.get("last_audit") or ""),
                "year_imputed": year_imputed,
                "area_imputed": area_imputed,
                "energy_unknown": rating == "U",
            })
            if obj.last_audit and obj.last_audit.year > AS_OF_YEAR:
                raise ValueError("Audit date after scenario year")
            accepted[pid] = obj
            counters["year_imputed"] += int(year_imputed)
            counters["area_imputed"] += int(area_imputed)
            counters["energy_unknown"] += int(obj.energy_unknown)
        except (ValueError, KeyError, TypeError, ValidationError) as error:
            rejected.append({**row, "reason": str(error).replace("\n", " ")[:450]})
    return accepted, rejected, counters


def clean_components(raw: list[dict[str, str]], properties: dict[str, PropertyRecord]) -> tuple[list[ComponentRecord], list[dict[str, str]], Counter]:
    accepted: list[ComponentRecord] = []
    rejected: list[dict[str, str]] = []
    counters: Counter = Counter()
    seen: set[str] = set()
    for row in raw:
        try:
            cid = (row.get("id") or "").strip().upper()
            pid = (row.get("property_id") or "").strip().upper()
            if cid in seen:
                raise ValueError("Duplicate component ID (valid first record retained)")
            if pid not in properties:
                raise ValueError("Parent property missing or quarantined")
            ctype = (row.get("component_type") or "").strip().lower().title()
            if ctype == "Hvac":
                ctype = "HVAC"
            if ctype not in COMPONENT_TYPES:
                raise ValueError("Unknown component type")
            if cid != f"{pid}-{ctype.upper()}":
                raise ValueError("Component ID / property / type mismatch")
            p = properties[pid]
            imputed = is_missing(row.get("installed_year"))
            installed_year = p.built_year if imputed else int(row["installed_year"])
            condition = int(row["condition_score"])
            cost = estimate_component_cost(
                component_type=ctype,
                area_m2=p.floor_area_m2,
                condition_score=condition,
                installed_year=installed_year,
                rating=p.energy_rating,
            )
            obj = ComponentRecord.model_validate({
                "id": cid, "property_id": pid,
                "component_type": ctype,
                "condition_score": condition,
                "installed_year": installed_year,
                "last_serviced": normalized_date(row.get("last_serviced") or ""),
                "year_imputed": imputed,
                "estimated_maintenance_cost_dkk": cost,
                "intervention_recommended": condition >= 4,
            })
            if obj.last_serviced and obj.last_serviced.year > AS_OF_YEAR:
                raise ValueError("Service date after scenario year")
            accepted.append(obj)
            seen.add(cid)
            counters["year_imputed"] += int(imputed)
        except (ValueError, KeyError, TypeError, ValidationError) as error:
            rejected.append({**row, "reason": str(error).replace("\n", " ")[:450]})
    return accepted, rejected, counters


def _write_rejections(path: Path, rejects: list[dict[str, str]], originals: tuple[str, ...]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=[*originals, "reason"], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rejects)


def _load_database(db_path: Path, properties: dict[str, PropertyRecord], components: list[ComponentRecord]) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = db_path.with_suffix(".tmp.sqlite3")
    temporary.unlink(missing_ok=True)
    aggregated: dict[str, list[ComponentRecord]] = defaultdict(list)
    for component in components:
        aggregated[component.property_id].append(component)
    try:
        with sqlite3.connect(temporary) as conn:
            conn.executescript(SCHEMA_SQL)
            prop_data = []
            for p in properties.values():
                parts = aggregated[p.id]
                cost = round(sum(item.estimated_maintenance_cost_dkk for item in parts), 2)
                cost_m2 = round(cost / p.floor_area_m2, 2)
                score = property_priority_score(
                    rating=p.energy_rating,
                    year_built=p.built_year,
                    max_condition=max((item.condition_score for item in parts), default=1),
                    cost_per_m2=cost_m2,
                )
                prop_data.append((
                    p.id, p.name, p.building_type, p.district, p.built_year,
                    p.floor_area_m2, p.energy_rating,
                    None if p.energy_rating == "U" else "ABCDEFG".index(p.energy_rating) + 1,
                    p.last_audit.isoformat() if p.last_audit else None,
                    int(p.year_imputed), int(p.area_imputed), int(p.energy_unknown),
                    cost, cost_m2, score,
                ))
            conn.executemany("""INSERT INTO properties VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", prop_data)
            conn.executemany("""INSERT INTO components VALUES (?,?,?,?,?,?,?,?,?)""", [
                (
                    c.id, c.property_id, c.component_type, c.condition_score, c.installed_year,
                    c.last_serviced.isoformat() if c.last_serviced else None,
                    int(c.year_imputed), c.estimated_maintenance_cost_dkk,
                    int(c.intervention_recommended),
                ) for c in components
            ])
            populate_extended_model(conn)
            conn.commit()
            result = conn.execute("PRAGMA foreign_key_check").fetchall()
            if result:
                raise RuntimeError(f"Foreign key errors: {result[:4]}")
            if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("SQLite integrity check failed")
        temporary.replace(db_path)  # atomic replacement after successful load
    finally:
        temporary.unlink(missing_ok=True)


def run_ingestion(*, properties_csv: Path, components_csv: Path, db_path: Path,
                  report_dir: Path, source_description: str = "external_csv") -> dict:
    report_dir.mkdir(parents=True, exist_ok=True)
    raw_properties, raw_components = _rows(properties_csv), _rows(components_csv)
    props, rejected_props, prop_counters = clean_properties(raw_properties)
    comps, rejected_comps, comp_counters = clean_components(raw_components, props)
    if not props or not comps:
        raise ValueError("No valid properties/components. Database not replaced.")
    _load_database(db_path, props, comps)

    # Reopen read-only: the database is completely built and committed at this
    # point. No rollback journal or write access is needed for the audit report.
    # Use an SQLite URI to avoid silently creating a new empty database when the
    # expected path is missing.
    try:
        with sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True) as db_conn:
            hierarchy_report = {
                key: db_conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for key, table in (
                    ("sites", "sites"), ("systems", "systems"),
                    ("assets", "assets"), ("inspections", "inspections"),
                    ("interventions", "interventions"),
                )
            }
            hierarchy_report["not_inspected_systems"] = db_conn.execute(
                "SELECT COUNT(*) FROM system_coverage WHERE status='not_inspected'"
            ).fetchone()[0]
    except sqlite3.Error as exc:
        raise RuntimeError(
            f"Cannot reopen generated SQLite database at {db_path}. "
            "On Docker Desktop for Windows, keep SQLite on a Docker-managed "
            "named volume (the supplied Compose configuration mounts /app/state). "
            f"Original error: {exc}"
        ) from exc

    from .generator import PROPERTY_COLUMNS, COMPONENT_COLUMNS
    _write_rejections(report_dir / "rejected_properties.csv", rejected_props, PROPERTY_COLUMNS)
    _write_rejections(report_dir / "rejected_components.csv", rejected_comps, COMPONENT_COLUMNS)
    report = {
        "source": source_description,
        "scenario_as_of_year": AS_OF_YEAR,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "properties": {"source_rows": len(raw_properties), "loaded": len(props),
                       "quarantined": len(rejected_props), **prop_counters},
        "components": {"source_rows": len(raw_components), "loaded": len(comps),
                       "quarantined": len(rejected_comps), **comp_counters},
        "hierarchy": hierarchy_report,
        "database_path": str(db_path),
        "note": "Assumption-based scenario costs, not observed maintenance costs or a trained ML forecast.",
    }
    (report_dir / "ingestion_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Load fictional building portfolio into SQLite")
    parser.add_argument("--generate", action="store_true", help="Generate fictional raw CSVs first")
    parser.add_argument("--count", type=int, default=6000, help="Synthetic property count (1-50,000)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--properties", type=Path, default=DATA_DIR / "raw" / "properties_raw.csv")
    parser.add_argument("--components", type=Path, default=DATA_DIR / "raw" / "components_raw.csv")
    parser.add_argument("--database", type=Path, default=DB_PATH)
    parser.add_argument("--reports", type=Path, default=DATA_DIR / "reports")
    args = parser.parse_args()
    if args.generate:
        generate_dataset(args.properties.parent, count=args.count, seed=args.seed)
        if args.properties.name != "properties_raw.csv" or args.components.name != "components_raw.csv" or args.components.parent != args.properties.parent:
            parser.error("--generate requires default source CSV filenames in the same directory")
    report = run_ingestion(
        properties_csv=args.properties, components_csv=args.components,
        db_path=args.database, report_dir=args.reports,
        source_description=f"synthetic_seed={args.seed};count={args.count}" if args.generate else "external_csv",
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
