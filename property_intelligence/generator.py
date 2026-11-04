"""Generate an entirely fictional, reproducible portfolio with intentionally messy CSV inputs.

No records describe actual properties, schools, people or municipalities.
"""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path
import random

from .settings import BUILDING_TYPES, COMPONENT_TYPES, DISTRICTS, AS_OF_YEAR

PROPERTY_COLUMNS = (
    "id", "name", "building_type", "district", "built_year",
    "floor_area_m2", "energy_rating", "last_audit",
)
COMPONENT_COLUMNS = (
    "id", "property_id", "component_type", "condition_score", "installed_year",
    "last_serviced",
)


def _date_string(day: date, rng: random.Random) -> str:
    return day.strftime(rng.choice(("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d")))


def generate_dataset(output_dir: Path, *, count: int = 6000, seed: int = 42) -> tuple[Path, Path]:
    """Write source CSVs. The seed and count are adjustable for repeatable demonstrations."""
    if count < 1 or count > 50000:
        raise ValueError("count must be between 1 and 50,000")
    rng = random.Random(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    props_path = output_dir / "properties_raw.csv"
    comps_path = output_dir / "components_raw.csv"

    with props_path.open("w", newline="", encoding="utf-8") as props_file, \
         comps_path.open("w", newline="", encoding="utf-8") as comps_file:
        pw = csv.DictWriter(props_file, fieldnames=PROPERTY_COLUMNS)
        cw = csv.DictWriter(comps_file, fieldnames=COMPONENT_COLUMNS)
        pw.writeheader()
        cw.writeheader()

        for i in range(1, count + 1):
            pid = f"P{i:05d}"
            kind = rng.choices(BUILDING_TYPES, weights=(31, 9, 16, 13, 23, 8))[0]
            district = rng.choice(DISTRICTS)
            year = rng.randint(1895, 2023)
            area = round(rng.uniform(650, 13000) if kind in ("School", "Sports Facility") else rng.uniform(220, 5800), 2)
            # Older stock is more likely to have poor ratings; still allows renovated exceptions.
            rating_score = min(7, max(1, round(1.5 + (2024 - year) / 28 + rng.gauss(0, 1.7))))
            energy = "ABCDEFG"[rating_score - 1]
            audit = date(2026, 1, 1) - timedelta(days=rng.randint(0, 2300))
            raw_prop = {
                "id": pid,
                "name": f"{district} {kind} {i:05d} (fictional)",
                "building_type": kind,
                "district": district,
                "built_year": str(year),
                "floor_area_m2": f"{area:.2f}",
                "energy_rating": energy.lower() if rng.random() < .08 else f" {energy} ",
                "last_audit": _date_string(audit, rng),
            }
            # Inject missing data and invalid source values to demonstrate cleansing/quarantine.
            if rng.random() < .035:
                raw_prop["floor_area_m2"] = rng.choice(("", "NULL", "n/a"))
            if rng.random() < .026:
                raw_prop["built_year"] = rng.choice(("", "unknown", "NULL"))
            if rng.random() < .025:
                raw_prop["energy_rating"] = rng.choice(("", "unknown", "N/A"))
            if rng.random() < .023:
                raw_prop["last_audit"] = ""
            if rng.random() < .004:
                raw_prop["built_year"] = "1800x"  # rejected, never silently imputed
            pw.writerow(raw_prop)
            if i % 251 == 0:
                pw.writerow(raw_prop)  # duplicate IDs: first valid record wins

            for component in COMPONENT_TYPES:
                installed = rng.randint(year, 2025) if year <= 2025 else year
                condition = min(5, max(1, round((2026 - installed) / 16 + rng.gauss(1.9, .85))))
                serviced = date(2026, 1, 1) - timedelta(days=rng.randint(30, 3800))
                raw_component = {
                    "id": f"{pid}-{component.upper()}",
                    "property_id": pid,
                    "component_type": component.lower() if rng.random() < .10 else component,
                    "condition_score": str(condition),
                    "installed_year": str(installed),
                    "last_serviced": _date_string(serviced, rng),
                }
                if rng.random() < .035:
                    raw_component["last_serviced"] = rng.choice(("", "NULL"))
                if rng.random() < .018:
                    raw_component["installed_year"] = ""
                if rng.random() < .004:
                    raw_component["condition_score"] = "bad"  # rejected
                cw.writerow(raw_component)
                if i % 337 == 0 and component == "HVAC":
                    cw.writerow(raw_component)
    return props_path, comps_path
