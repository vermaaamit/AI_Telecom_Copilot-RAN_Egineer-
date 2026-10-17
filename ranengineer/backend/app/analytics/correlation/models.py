from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class CorrelationConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class CorrelatedAlarm(BaseModel):
    alarm_id: str
    alarm_type: str
    severity: str
    status: str
    description: str
    matched_kpis: list[str] = Field(default_factory=list)
    confidence: CorrelationConfidence
    rationale: str


class CellRcaResult(BaseModel):
    cell_id: str
    site_id: str | None = None
    technology: str | None = None
    health_score: int | None = None
    status: str
    kpis: dict[str, Any] = Field(default_factory=dict)
    kpi_statuses: dict[str, str] = Field(default_factory=dict)
    probable_causes: list[dict[str, Any]] = Field(default_factory=list)
    correlated_alarms: list[CorrelatedAlarm] = Field(default_factory=list)
    primary_hypothesis: str | None = None
    recommended_actions: list[str] = Field(default_factory=list)
    correlation_summary: str
    disclaimer: str = (
        "Deterministic correlation based on available KPI telemetry and alarm records. "
        "Engineers must verify on-site before executing field interventions."
    )

