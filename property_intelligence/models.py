"""Strict validated, public-facing contracts and cleaned records."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict

BuildingType = Literal[
    "School", "Library", "Sports Facility", "Administrative Office", "Daycare", "Health Clinic"
]
ComponentType = Literal["HVAC", "Insulation", "Roof", "Windows"]
EnergyRating = Literal["A", "B", "C", "D", "E", "F", "G", "U"]


class PropertyRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^P\d{5}$")
    name: str = Field(min_length=4, max_length=120)
    building_type: BuildingType
    district: Literal["North", "South", "East", "West", "Central", "Harbour"]
    built_year: int = Field(ge=1850, le=2026)
    floor_area_m2: float = Field(gt=0, le=100000)
    energy_rating: EnergyRating
    last_audit: date | None
    year_imputed: bool
    area_imputed: bool
    energy_unknown: bool


class ComponentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^P\d{5}-(HVAC|INSULATION|ROOF|WINDOWS)$")
    property_id: str = Field(pattern=r"^P\d{5}$")
    component_type: ComponentType
    condition_score: int = Field(ge=1, le=5)
    installed_year: int = Field(ge=1850, le=2026)
    last_serviced: date | None
    year_imputed: bool
    estimated_maintenance_cost_dkk: float = Field(ge=0)
    intervention_recommended: bool


class AskRequest(BaseModel):
    question: str = Field(min_length=10, max_length=500, examples=["Which schools built before 1970 have the worst energy ratings?"])


class QueryPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: Literal["worst_energy", "priority", "cost_per_m2", "total_cost", "component_priority",
                    "energy_savings", "asset_condition", "intervention_value"]
    building_type: BuildingType | None = None
    component_type: ComponentType | None = None
    built_before: int | None = Field(default=None, ge=1850, le=2026)
    district: Literal["North", "South", "East", "West", "Central", "Harbour"] | None = None
    limit: int = Field(default=10, ge=1, le=25)
