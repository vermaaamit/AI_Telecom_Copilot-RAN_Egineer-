"""Pydantic models for Operational Shift Handover Intelligence."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field


class NetworkOperationalStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


class CriticalCellSummary(BaseModel):
    cell_id: str
    site_id: Optional[str] = None
    technology: Optional[str] = None
    health_score: float
    status: str
    top_issue: Optional[str] = None
    probable_causes: List[Any] = Field(default_factory=list)


class ActiveAlarmSummary(BaseModel):
    id: str
    site_id: Optional[str] = None
    cell_id: Optional[str] = None
    severity: str
    alarm_type: str
    description: str
    started_at: Optional[str] = None


class OpenIncidentSummary(BaseModel):
    id: str
    title: str
    severity: str
    status: str
    affected_cells: List[str] = Field(default_factory=list)
    related_alarms: List[str] = Field(default_factory=list)


class PredictiveWarningSummary(BaseModel):
    cell_id: str
    kpi_name: str
    velocity_per_hour: float
    projected_value: float
    eta_critical_hours: float
    recommendation: str


class RAppStatusSummary(BaseModel):
    id: str
    name: str
    policy_type: str
    review_status: str
    target_cells: List[str]


class ShiftHandoverReport(BaseModel):
    report_id: str = Field(default_factory=lambda: f"HND-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}")
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    shift_title: str = "NOC RAN Operational Shift Handover"
    prepared_by: str = "Senior RAN Optimization Engineer"
    system_status: NetworkOperationalStatus = NetworkOperationalStatus.HEALTHY
    dataset_id: Optional[str] = None
    dataset_name: Optional[str] = None
    total_cells_monitored: int = 0
    degraded_cell_count: int = 0
    critical_cells: List[CriticalCellSummary] = Field(default_factory=list)
    active_alarms: List[ActiveAlarmSummary] = Field(default_factory=list)
    open_incidents: List[OpenIncidentSummary] = Field(default_factory=list)
    predictive_warnings: List[PredictiveWarningSummary] = Field(default_factory=list)
    oran_rapps: List[RAppStatusSummary] = Field(default_factory=list)
    handover_action_items: List[str] = Field(default_factory=list)
    executive_summary: str

