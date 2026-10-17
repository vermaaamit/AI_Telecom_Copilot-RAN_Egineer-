from __future__ import annotations

from typing import Any
from app.alarms.models import Alarm, AlarmType
from app.analytics.correlation.models import CellRcaResult, CorrelatedAlarm, CorrelationConfidence

ALARM_TO_KPI_MAPPING: dict[str, list[str]] = {
    AlarmType.HIGH_PRB_UTILIZATION.value: ["PRB_UTILIZATION", "THROUGHPUT_DL", "THROUGHPUT_UL"],
    AlarmType.LOW_THROUGHPUT.value: ["THROUGHPUT_DL", "THROUGHPUT_UL"],
    AlarmType.POOR_RADIO_QUALITY.value: ["RSRP", "SINR", "CQI", "BLER"],
    AlarmType.HIGH_CALL_DROP.value: ["CALL_DROP_RATE", "CALL_SETUP_SUCCESS_RATE"],
    AlarmType.HANDOVER_FAILURE.value: ["HANDOVER_SUCCESS_RATE"],
    AlarmType.CELL_UNAVAILABLE.value: ["AVAILABILITY", "TRAFFIC_DL_GB", "THROUGHPUT_DL"],
}


class CorrelationEngine:
    """Deterministic Telecom KPI and Alarm Correlation Engine."""

    def correlate_cell_with_alarms(
        self,
        cell: dict[str, Any],
        alarms: list[Alarm],
    ) -> CellRcaResult:
        cell_id = str(cell.get("cell_id", ""))
        site_id = str(cell.get("site_id", "")) if cell.get("site_id") else None
        kpi_statuses = cell.get("kpi_statuses", {}) or {}
        probable_causes = cell.get("probable_causes", []) or []

        degraded_kpis = {
            kpi for kpi, status in kpi_statuses.items()
            if str(status).upper() in ("CRITICAL", "WARNING")
        }

        correlated_alarms: list[CorrelatedAlarm] = []

        for alarm in alarms:
            alarm_cell_id = alarm.cell_id
            alarm_site_id = alarm.site_id
            alarm_type_str = alarm.alarm_type.value if hasattr(alarm.alarm_type, "value") else str(alarm.alarm_type)

            mapped_kpis = ALARM_TO_KPI_MAPPING.get(alarm_type_str, [])
            matching_degraded_kpis = [k for k in mapped_kpis if k in degraded_kpis]

            is_direct_cell = bool(alarm_cell_id and alarm_cell_id.lower() == cell_id.lower())
            is_same_site = bool(site_id and alarm_site_id and alarm_site_id.lower() == site_id.lower())

            if not (is_direct_cell or is_same_site):
                continue

            if is_direct_cell and matching_degraded_kpis:
                confidence = CorrelationConfidence.HIGH
                rationale = (
                    f"Direct alarm on {cell_id} matching degraded KPI(s): "
                    f"{', '.join(matching_degraded_kpis)}."
                )
            elif is_direct_cell or (is_same_site and matching_degraded_kpis):
                confidence = CorrelationConfidence.MEDIUM
                rationale = (
                    f"Alarm on site {site_id or cell_id} correlated with degraded telecom metrics."
                )
            else:
                confidence = CorrelationConfidence.LOW
                rationale = f"Co-located site alarm on {site_id} without direct KPI match."

            correlated_alarms.append(
                CorrelatedAlarm(
                    alarm_id=alarm.alarm_id,
                    alarm_type=alarm_type_str,
                    severity=alarm.severity.value if hasattr(alarm.severity, "value") else str(alarm.severity),
                    status=alarm.status.value if hasattr(alarm.status, "value") else str(alarm.status),
                    description=alarm.description,
                    matched_kpis=matching_degraded_kpis,
                    confidence=confidence,
                    rationale=rationale,
                )
            )

        # Sort correlated alarms by confidence (HIGH -> MEDIUM -> LOW)
        confidence_order = {CorrelationConfidence.HIGH: 0, CorrelationConfidence.MEDIUM: 1, CorrelationConfidence.LOW: 2}
        correlated_alarms.sort(key=lambda a: confidence_order[a.confidence])

        # Generate primary hypothesis & recommended actions
        recommended_actions: list[str] = []
        for cause in probable_causes:
            for check in cause.get("recommended_checks", []):
                if check not in recommended_actions:
                    recommended_actions.append(check)

        if correlated_alarms:
            top_alarm = correlated_alarms[0]
            if top_alarm.confidence == CorrelationConfidence.HIGH:
                primary_hypothesis = (
                    f"KPI degradation is strongly correlated with active alarm "
                    f"[{top_alarm.alarm_type}] ({top_alarm.description})."
                )
            else:
                primary_hypothesis = (
                    f"KPI degradation is partially correlated with site alarm "
                    f"[{top_alarm.alarm_type}] ({top_alarm.description})."
                )
            recommended_actions.insert(0, f"Check OSS alarm {top_alarm.alarm_id} and clear physical/logical faults.")
        elif probable_causes:
            primary_hypothesis = (
                f"No active alarms correlated. Primary hypothesis: "
                f"{probable_causes[0].get('category', 'Radio/Capacity anomaly')} - "
                f"{probable_causes[0].get('description', '')}"
            )
        else:
            primary_hypothesis = "Telemetry indicates normal operation or unclassified deviation."

        summary = (
            f"Cell {cell_id} (Health: {cell.get('health_score')}/100, {cell.get('status')}) "
            f"correlated with {len(correlated_alarms)} alarm(s)."
        )

        return CellRcaResult(
            cell_id=cell_id,
            site_id=site_id,
            technology=cell.get("technology"),
            health_score=cell.get("health_score"),
            status=str(cell.get("status", "UNKNOWN")),
            kpis=cell.get("kpis", {}) or {},
            kpi_statuses=kpi_statuses,
            probable_causes=probable_causes,
            correlated_alarms=correlated_alarms,
            primary_hypothesis=primary_hypothesis,
            recommended_actions=recommended_actions,
            correlation_summary=summary,
        )


_correlation_engine: CorrelationEngine | None = None


def get_correlation_engine() -> CorrelationEngine:
    global _correlation_engine
    if _correlation_engine is None:
        _correlation_engine = CorrelationEngine()
    return _correlation_engine

