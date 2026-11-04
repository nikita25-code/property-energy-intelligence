"""Runtime configuration shared by the pipeline and API."""

from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data")))
DB_PATH = Path(os.getenv("DB_PATH", str(DATA_DIR / "property_energy.sqlite3")))

BUILDING_TYPES = (
    "School", "Library", "Sports Facility", "Administrative Office",
    "Daycare", "Health Clinic",
)
COMPONENT_TYPES = ("HVAC", "Insulation", "Roof", "Windows")
DISTRICTS = ("North", "South", "East", "West", "Central", "Harbour")
# Illustrative 2026 DKK per m² of gross floor area; NOT a contractor quote.
UNIT_COST_DKK_M2 = {"HVAC": 1550, "Insulation": 1250, "Roof": 850, "Windows": 1100}
EXPECTED_LIFE_YEARS = {"HVAC": 25, "Insulation": 45, "Roof": 35, "Windows": 30}
ENERGY_SCORES = {letter: idx for idx, letter in enumerate("ABCDEFG", start=1)}
ENERGY_SCORES["U"] = None
AS_OF_YEAR = 2026
