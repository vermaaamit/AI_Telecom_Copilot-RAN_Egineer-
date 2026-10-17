from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.analytics.trends.models import (
    CellHistoricalTrends,
    CellKpiTrend,
    KpiTrendPoint,
    TrendDirection,
)
from app.models.dataset import CellModel, DatasetModel
from app.analytics.kpi.thresholds import get_kpi_direction, KpiDirection


class TrendEngine:
    """Deterministic Time-Series KPI Trend Engine across multiple datasets."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def calculate_cell_trends(self, cell_id: str) -> CellHistoricalTrends | None:
        # Fetch all historical cell occurrences across datasets ordered chronologically
        query = (
            select(CellModel)
            .join(DatasetModel, CellModel.dataset_id == DatasetModel.id)
            .where(CellModel.cell_id == cell_id)
            .order_by(DatasetModel.created_at.asc())
            .options(selectinload(CellModel.dataset))
        )
        records = list(self.db.scalars(query).all())
        if not records:
            return None

        site_id = records[-1].site_id
        tech = records[-1].technology

        # Extract all available KPI names across occurrences
        all_kpis: set[str] = set()
        for rec in records:
            if rec.kpis:
                all_kpis.update(rec.kpis.keys())

        trends_map: dict[str, CellKpiTrend] = {}

        for kpi in sorted(all_kpis):
            points: list[KpiTrendPoint] = []
            values: list[float] = []

            for rec in records:
                val = rec.kpis.get(kpi) if rec.kpis else None
                status = rec.kpi_statuses.get(kpi) if rec.kpi_statuses else None
                created_iso = (
                    rec.dataset.created_at.isoformat()
                    if rec.dataset and rec.dataset.created_at
                    else ""
                )
                points.append(
                    KpiTrendPoint(
                        dataset_id=rec.dataset_id,
                        timestamp=created_iso,
                        value=val,
                        status=status,
                    )
                )
                if val is not None:
                    try:
                        values.append(float(val))
                    except (ValueError, TypeError):
                        pass

            if len(values) < 2:
                # Insufficient points for trend slope
                slope = 0.0
                pct_change = 0.0
                direction = TrendDirection.STABLE
                summary = f"{kpi} has insufficient historical data points for slope calculation."
            else:
                first_val = values[0]
                last_val = values[-1]
                delta = last_val - first_val
                slope = round(delta / (len(values) - 1), 3)
                pct_change = (
                    round((delta / abs(first_val)) * 100, 2)
                    if abs(first_val) > 1e-6
                    else 0.0
                )

                # Determine if movement is DEGRADING or IMPROVING
                kpi_dir = get_kpi_direction(kpi)
                if abs(pct_change) < 3.0:
                    direction = TrendDirection.STABLE
                    summary = f"{kpi} is stable ({last_val} vs baseline {first_val})."
                elif kpi_dir == KpiDirection.HIGHER_IS_BETTER:
                    if delta > 0:
                        direction = TrendDirection.IMPROVING
                        summary = f"{kpi} improved by {pct_change}% (slope +{slope})."
                    else:
                        direction = TrendDirection.DEGRADING
                        summary = f"{kpi} degraded by {abs(pct_change)}% (slope {slope})."
                elif kpi_dir == KpiDirection.LOWER_IS_BETTER:
                    if delta > 0:
                        direction = TrendDirection.DEGRADING
                        summary = f"{kpi} degraded (increased) by {pct_change}% (slope +{slope})."
                    else:
                        direction = TrendDirection.IMPROVING
                        summary = f"{kpi} improved (reduced) by {abs(pct_change)}% (slope {slope})."
                else:
                    direction = TrendDirection.STABLE
                    summary = f"{kpi} changed by {pct_change}%."

            trends_map[kpi] = CellKpiTrend(
                kpi_name=kpi,
                points=points,
                trend_direction=direction,
                slope=slope,
                percentage_change=pct_change,
                summary=summary,
            )

        # Health score trend
        health_scores = [r.health_score for r in records if r.health_score is not None]
        if len(health_scores) >= 2:
            h_delta = health_scores[-1] - health_scores[0]
            if h_delta > 5:
                overall_trend = TrendDirection.IMPROVING
            elif h_delta < -5:
                overall_trend = TrendDirection.DEGRADING
            else:
                overall_trend = TrendDirection.STABLE
        else:
            overall_trend = TrendDirection.STABLE

        overall_summary = (
            f"Analyzed {len(records)} temporal sample(s) for cell {cell_id}. "
            f"Overall health trend is {overall_trend.value}."
        )

        return CellHistoricalTrends(
            cell_id=cell_id,
            site_id=site_id,
            technology=tech,
            data_points_count=len(records),
            trends=trends_map,
            overall_health_trend=overall_trend,
            summary=overall_summary,
        )

