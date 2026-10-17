from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class PredictiveRiskLevel(str, Enum):
    HIGH_RISK = "HIGH_RISK"
    MEDIUM_RISK = "MEDIUM_RISK"
    LOW_RISK = "LOW_RISK"


class PredictiveAnomalyItem(BaseModel):
    cell_id: str
    site_id: str | None = None
    technology: str | None = None
    kpi_name: str
    current_value: float
    projected_value: float
    velocity_rate: float
    risk_level: PredictiveRiskLevel
    projected_breach_condition: str
    recommended_action: str
    summary: str


class PredictiveReport(BaseModel):
    total_evaluated_cells: int
    at_risk_cells_count: int
    items: list[PredictiveAnomalyItem] = Field(default_factory=list)
    methodology: str = (
        "Linear velocity projection based on historical time-series intervals. "
        "Flags pre-threshold degradations to enable proactive maintenance."
    )

