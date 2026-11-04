"""Interpretable scenario cost / priority formulae, not trained predictions."""

from .settings import ENERGY_SCORES, EXPECTED_LIFE_YEARS, UNIT_COST_DKK_M2

CONDITION_FACTOR = {1: 0.00, 2: 0.15, 3: 0.40, 4: 0.75, 5: 1.00}


def estimate_component_cost(*, component_type: str, area_m2: float,
                            condition_score: int, installed_year: int,
                            rating: str) -> float:
    """Assumption-driven 2026 DKK estimate for indicated work; see docs/assumptions."""
    age = max(0, 2026 - installed_year)
    life = EXPECTED_LIFE_YEARS[component_type]
    energy_factor = {"A": .85, "B": .90, "C": .95, "D": 1.,
                     "E": 1.08, "F": 1.16, "G": 1.25, "U": 1.}[rating]
    return round(
        area_m2 * UNIT_COST_DKK_M2[component_type] * CONDITION_FACTOR[condition_score]
        * energy_factor * (1 + .12 * min(age / life, 2)), 2
    )


def property_priority_score(*, rating: str, year_built: int, max_condition: int,
                            cost_per_m2: float) -> float:
    """0-100 relative screening score, NOT a statutory EPC/2030 compliance measure."""
    energy = (ENERGY_SCORES[rating] or 4) / 7 * 40
    condition = max_condition / 5 * 35
    age = min(max(2026 - year_built, 0) / 80, 1) * 15
    cost = min(cost_per_m2 / 4500, 1) * 10
    return round(min(100, energy + condition + age + cost), 1)
