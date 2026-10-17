from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class TrendDirection(str, Enum):
    IMPROVING = "IMPROVING"
    DEGRADING = "DEGRADING"
    STABLE = "STABLE"


class KpiTrendPoint(BaseModel):
    dataset_id: str
    timestamp: str
    value: float | None
    status: str | None = None


class CellKpiTrend(BaseModel):
    kpi_name: str
    points: list[KpiTrendPoint] = Field(default_factory=list)
    trend_direction: TrendDirection
    slope: float
    percentage_change: float
    summary: str


class CellHistoricalTrends(BaseModel):
    cell_id: str
    site_id: str | None = None
    technology: str | None = None
    data_points_count: int
    trends: dict[str, CellKpiTrend] = Field(default_factory=dict)
    overall_health_trend: TrendDirection
    summary: str

