from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.analytics.kpi.thresholds import get_kpi_thresholds, KpiDirection, get_kpi_direction
from app.analytics.predictive.models import (
    PredictiveAnomalyItem,
    PredictiveReport,
    PredictiveRiskLevel,
)
from app.models.dataset import CellModel, DatasetModel


class PredictiveAnomalyEngine:
    """Predictive degradation engine using linear velocity projection across datasets."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def analyze_predictive_anomalies(self) -> PredictiveReport:
        # Get all distinct cell IDs
        cell_ids = list(self.db.scalars(select(CellModel.cell_id).distinct()).all())
        at_risk_items: list[PredictiveAnomalyItem] = []

        for cid in cell_ids:
            # Fetch occurrences in chronological order
            records = list(
                self.db.scalars(
                    select(CellModel)
                    .join(DatasetModel, CellModel.dataset_id == DatasetModel.id)
                    .where(CellModel.cell_id == cid)
                    .order_by(DatasetModel.created_at.asc())
                ).all()
            )
            if len(records) < 2:
                continue

            prev_cell = records[-2]
            curr_cell = records[-1]

            if not curr_cell.kpis or not prev_cell.kpis:
                continue

            for kpi, curr_val in curr_cell.kpis.items():
                prev_val = prev_cell.kpis.get(kpi)
                if curr_val is None or prev_val is None:
                    continue

                try:
                    c_float = float(curr_val)
                    p_float = float(prev_val)
                except (ValueError, TypeError):
                    continue

                velocity = round(c_float - p_float, 2)
                projected_next = round(c_float + velocity, 2)
                thresholds = get_kpi_thresholds(kpi)
                if not thresholds:
                    continue

                direction = get_kpi_direction(kpi)
                is_at_risk = False
                risk_level = PredictiveRiskLevel.LOW_RISK
                breach_cond = ""
                action = ""

                if direction == KpiDirection.LOWER_IS_BETTER:
                    crit = thresholds.critical
                    warn = thresholds.warning
                    # Degrading if velocity is positive (increasing value)
                    if velocity > 0 and c_float < crit:
                        if projected_next >= crit:
                            is_at_risk = True
                            risk_level = PredictiveRiskLevel.HIGH_RISK
                            breach_cond = f"Projected to breach CRITICAL ({projected_next} >= {crit})"
                        elif projected_next >= warn and c_float < warn:
                            is_at_risk = True
                            risk_level = PredictiveRiskLevel.MEDIUM_RISK
                            breach_cond = f"Projected to enter WARNING ({projected_next} >= {warn})"

                elif direction == KpiDirection.HIGHER_IS_BETTER:
                    crit = thresholds.critical
                    warn = thresholds.warning
                    # Degrading if velocity is negative (decreasing value)
                    if velocity < 0 and c_float > crit:
                        if projected_next <= crit:
                            is_at_risk = True
                            risk_level = PredictiveRiskLevel.HIGH_RISK
                            breach_cond = f"Projected to fall below CRITICAL ({projected_next} <= {crit})"
                        elif projected_next <= warn and c_float > warn:
                            is_at_risk = True
                            risk_level = PredictiveRiskLevel.MEDIUM_RISK
                            breach_cond = f"Projected to drop below WARNING ({projected_next} <= {warn})"

                if is_at_risk:
                    if kpi == "PRB_UTILIZATION":
                        action = "Proactively offload traffic via carrier aggregation or adjust tilt to reduce cell footprint."
                    elif kpi in ("RSRP", "SINR"):
                        action = "Audit pilot pollution and check for external RF interference sources."
                    elif kpi in ("CALL_DROP_RATE", "HANDOVER_SUCCESS_RATE"):
                        action = "Check neighbor relations (ANR) and adjust handover hysteresis timers."
                    else:
                        action = f"Inspect cell hardware, transport link, and RF conditions for {kpi}."

                    at_risk_items.append(
                        PredictiveAnomalyItem(
                            cell_id=cid,
                            site_id=curr_cell.site_id,
                            technology=curr_cell.technology,
                            kpi_name=kpi,
                            current_value=c_float,
                            projected_value=projected_next,
                            velocity_rate=velocity,
                            risk_level=risk_level,
                            projected_breach_condition=breach_cond,
                            recommended_action=action,
                            summary=(
                                f"Cell {cid} {kpi} changed from {p_float} to {c_float} "
                                f"(velocity: {velocity:+}). {breach_cond}."
                            ),
                        )
                    )

        # Sort by risk level (HIGH_RISK first)
        risk_order = {PredictiveRiskLevel.HIGH_RISK: 0, PredictiveRiskLevel.MEDIUM_RISK: 1, PredictiveRiskLevel.LOW_RISK: 2}
        at_risk_items.sort(key=lambda x: risk_order[x.risk_level])

        return PredictiveReport(
            total_evaluated_cells=len(cell_ids),
            at_risk_cells_count=len(at_risk_items),
            items=at_risk_items,
        )

