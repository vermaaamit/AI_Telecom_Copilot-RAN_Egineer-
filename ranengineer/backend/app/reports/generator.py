"""Operational Shift Handover Report Generator."""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.alarms.store import AlarmStore
from app.analytics.predictive.engine import PredictiveAnomalyEngine
from app.incidents.store import IncidentStore
from app.oran.store import get_rapp_store
from app.reports.models import (
    ActiveAlarmSummary,
    CriticalCellSummary,
    NetworkOperationalStatus,
    OpenIncidentSummary,
    PredictiveWarningSummary,
    RAppStatusSummary,
    ShiftHandoverReport,
)
from app.repositories.dataset_repository import DatasetRepository


class ShiftHandoverGenerator:
    """Aggregates multi-source RAN telemetry, alarms, incidents, and predictive warnings."""

    def __init__(self, db: Session):
        self.db = db
        self.dataset_repo = DatasetRepository(db)
        self.alarm_store = AlarmStore()
        self.incident_store = IncidentStore()
        self.predictive_engine = PredictiveAnomalyEngine(db)
        self.rapp_store = get_rapp_store()

    def generate(
        self,
        dataset_id: Optional[str] = None,
        prepared_by: str = "Senior RAN Optimization Engineer",
        shift_title: str = "NOC RAN Operational Shift Handover",
    ) -> ShiftHandoverReport:
        # 1. Resolve dataset
        dataset = None
        if dataset_id:
            dataset = self.dataset_repo.get(dataset_id)
        else:
            all_datasets = self.dataset_repo.list()
            if all_datasets:
                dataset = self.dataset_repo.get(all_datasets[0]["id"])

        # 2. Cells & Health
        critical_cells: List[CriticalCellSummary] = []
        total_cells = 0
        degraded_count = 0

        if dataset and "cells" in dataset:
            cells = dataset.get("cells", [])
            total_cells = len(cells)
            for c in cells:
                score = float(c.get("health_score", 100))
                status_str = str(c.get("status", "HEALTHY")).upper()
                if score < 60 or status_str in ["DEGRADED", "CRITICAL"]:
                    degraded_count += 1
                    top_issue = c.get("issues", [None])[0] if c.get("issues") else None
                    raw_causes = c.get("probable_causes", [])
                    extracted_causes: List[str] = []
                    for rc in raw_causes:
                        if isinstance(rc, dict):
                            extracted_causes.append(rc.get("title") or rc.get("rule_id") or str(rc))
                        elif isinstance(rc, str):
                            extracted_causes.append(rc)
                        elif hasattr(rc, "title"):
                            extracted_causes.append(str(rc.title))
                        else:
                            extracted_causes.append(str(rc))

                    critical_cells.append(
                        CriticalCellSummary(
                            cell_id=c.get("cell_id", "UNKNOWN"),
                            site_id=c.get("site_id"),
                            technology=c.get("technology"),
                            health_score=score,
                            status=status_str,
                            top_issue=top_issue,
                            probable_causes=extracted_causes,
                        )
                    )

        # Sort worst health first
        critical_cells.sort(key=lambda x: x.health_score)

        # 3. Active Alarms
        active_alarms: List[ActiveAlarmSummary] = []
        try:
            db_alarms = self.alarm_store.list_active()
            for a in db_alarms:
                active_alarms.append(
                    ActiveAlarmSummary(
                        id=getattr(a, "alarm_id", getattr(a, "id", "UNKNOWN")),
                        site_id=a.site_id,
                        cell_id=a.cell_id,
                        severity=a.severity.value if hasattr(a.severity, "value") else str(a.severity),
                        alarm_type=a.alarm_type.value if hasattr(a.alarm_type, "value") else str(a.alarm_type),
                        description=a.description,
                        started_at=a.started_at.isoformat() if a.started_at else None,
                    )
                )
        except Exception as e:
            pass

        # 4. Open Incidents
        open_incidents: List[OpenIncidentSummary] = []
        try:
            db_incidents = self.incident_store.list_open()
            for inc in db_incidents:
                open_incidents.append(
                    OpenIncidentSummary(
                        id=inc.id,
                        title=inc.title,
                        severity=inc.severity.value if hasattr(inc.severity, "value") else str(inc.severity),
                        status=inc.status.value if hasattr(inc.status, "value") else str(inc.status),
                        affected_cells=inc.affected_cells,
                        related_alarms=inc.related_alarms,
                    )
                )
        except Exception:
            pass

        # 5. Predictive Warnings
        predictive_warnings: List[PredictiveWarningSummary] = []
        try:
            pred_report = self.predictive_engine.analyze_predictive_anomalies()
            for p in pred_report.at_risk_cells:
                predictive_warnings.append(
                    PredictiveWarningSummary(
                        cell_id=p.cell_id,
                        kpi_name=p.kpi_name,
                        velocity_per_hour=p.velocity_per_hour,
                        projected_value=p.projected_value,
                        eta_critical_hours=p.eta_critical_hours or 0.0,
                        recommendation=p.suggested_action,
                    )
                )
        except Exception:
            pass

        # 6. O-RAN rApps
        oran_rapps: List[RAppStatusSummary] = []
        try:
            rapps = self.rapp_store.list_all()
            for r in rapps[:5]:
                oran_rapps.append(
                    RAppStatusSummary(
                        id=r.id,
                        name=r.name,
                        policy_type=r.policy_type.value if hasattr(r.policy_type, "value") else str(r.policy_type),
                        review_status=r.review_status.value if hasattr(r.review_status, "value") else str(r.review_status),
                        target_cells=r.target_cells,
                    )
                )
        except Exception:
            pass

        # 7. System Status Calculation
        has_critical_alarms = any(a.severity.upper() == "CRITICAL" for a in active_alarms)
        has_critical_incidents = any(i.severity.upper() in ["CRITICAL", "HIGH"] for i in open_incidents)
        has_severe_cell_failure = any(c.health_score < 40 for c in critical_cells)

        if has_critical_alarms or has_critical_incidents or has_severe_cell_failure:
            system_status = NetworkOperationalStatus.CRITICAL
        elif degraded_count > 0 or len(active_alarms) > 0 or len(open_incidents) > 0 or len(predictive_warnings) > 0:
            system_status = NetworkOperationalStatus.DEGRADED
        else:
            system_status = NetworkOperationalStatus.HEALTHY

        # 8. Action Items
        actions: List[str] = []
        if critical_cells:
            worst_ids = ", ".join([c.cell_id for c in critical_cells[:3]])
            actions.append(f"Prioritize inspection and field parameter tuning for critical sectors: {worst_ids}.")
        if active_alarms:
            actions.append(f"Review and acknowledge {len(active_alarms)} active alarm(s), focusing on critical backhaul and interference triggers.")
        if open_incidents:
            actions.append(f"Follow up on {len(open_incidents)} open incident ticket(s) with field dispatch teams.")
        if predictive_warnings:
            preds_summary = ", ".join([f"{pw.cell_id} ({pw.kpi_name})" for pw in predictive_warnings[:2]])
            actions.append(f"Proactive early-warning alert: monitor velocity trends on {preds_summary} before peak traffic.")
        if any(r.review_status != "ENGINEER_APPROVED" for r in oran_rapps):
            actions.append("Review pending O-RAN rApp policies in rApp Studio before lab sign-off.")
        if not actions:
            actions.append("All network cells, alarms, and incidents operating within healthy baseline thresholds. Maintain routine monitoring.")

        # 9. Executive Summary
        exec_summary = (
            f"Operational shift concluded with overall network state rated as {system_status.value}. "
            f"Monitored {total_cells} active cells across current sector telemetry, identifying "
            f"{degraded_count} degraded sector(s), {len(active_alarms)} active alarm(s), and "
            f"{len(open_incidents)} open operational incident(s). "
            f"A total of {len(predictive_warnings)} predictive early-warning anomalies were projected."
        )

        return ShiftHandoverReport(
            shift_title=shift_title,
            prepared_by=prepared_by,
            system_status=system_status,
            dataset_id=dataset.get("id") if dataset else None,
            dataset_name=dataset.get("name") if dataset else None,
            total_cells_monitored=total_cells,
            degraded_cell_count=degraded_count,
            critical_cells=critical_cells,
            active_alarms=active_alarms,
            open_incidents=open_incidents,
            predictive_warnings=predictive_warnings,
            oran_rapps=oran_rapps,
            handover_action_items=actions,
            executive_summary=exec_summary,
        )

    @staticmethod
    def format_markdown(report: ShiftHandoverReport) -> str:
        """Converts structured shift handover report into clean, professional Markdown."""
        lines = [
            f"# {report.shift_title}",
            f"**Report ID:** `{report.report_id}`  ",
            f"**Generated:** {report.generated_at} (UTC)  ",
            f"**Lead Engineer:** {report.prepared_by}  ",
            f"**Operational Network Status:** **{report.system_status.value}**  ",
            "",
            "## Executive Summary",
            report.executive_summary,
            "",
            "## Immediate Handover Action Checklist",
        ]
        for idx, item in enumerate(report.handover_action_items, 1):
            lines.append(f"{idx}. [ ] {item}")

        lines.extend([
            "",
            "## Critical & Degraded Cells",
            f"**Monitored:** {report.total_cells_monitored} cells | **Degraded:** {report.degraded_cell_count} cells",
        ])
        if report.critical_cells:
            lines.append("| Cell ID | Site ID | Tech | Health Score | Status | Top Root Cause |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for c in report.critical_cells:
                cause = c.probable_causes[0] if c.probable_causes else (c.top_issue or "N/A")
                lines.append(f"| `{c.cell_id}` | {c.site_id or '-'} | {c.technology or '-'} | {c.health_score:.1f} | {c.status} | {cause} |")
        else:
            lines.append("No cells currently degraded below baseline thresholds.")

        lines.extend(["", "## Active Operational Alarms"])
        if report.active_alarms:
            lines.append("| Alarm ID | Severity | Type | Target | Description |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for a in report.active_alarms:
                target = a.cell_id or a.site_id or "Network"
                lines.append(f"| `{a.id}` | {a.severity} | {a.alarm_type} | {target} | {a.description} |")
        else:
            lines.append("No active operational alarms reported.")

        lines.extend(["", "## Open Incident Tickets"])
        if report.open_incidents:
            lines.append("| Incident ID | Priority | Status | Title | Affected Cells |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for inc in report.open_incidents:
                cells = ", ".join(inc.affected_cells) if inc.affected_cells else "N/A"
                lines.append(f"| `{inc.id}` | {inc.severity} | {inc.status} | {inc.title} | {cells} |")
        else:
            lines.append("No open operational incident tickets.")

        lines.extend(["", "## Predictive Anomaly Velocity Warnings"])
        if report.predictive_warnings:
            lines.append("| Cell ID | KPI | Velocity (/hr) | Projected | Time to Critical | Action |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for pw in report.predictive_warnings:
                lines.append(f"| `{pw.cell_id}` | {pw.kpi_name} | {pw.velocity_per_hour:+.2f} | {pw.projected_value:.2f} | {pw.eta_critical_hours:.1f} hrs | {pw.recommendation} |")
        else:
            lines.append("No forward-looking predictive anomalies detected in current trend horizon.")

        lines.extend(["", "## O-RAN Non-RT RIC Policy Studio State"])
        if report.oran_rapps:
            lines.append("| rApp ID | Policy Name | Type | Review Status | Target Cells |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for r in report.oran_rapps:
                cells = ", ".join(r.target_cells) if r.target_cells else "Network-wide"
                lines.append(f"| `{r.id}` | {r.name} | {r.policy_type} | {r.review_status} | {cells} |")
        else:
            lines.append("No active rApps registered in Non-RT RIC studio.")

        lines.extend([
            "",
            "---",
            "*Report compiled by AI Telecom Copilot – RAN Engineer. Analytics calculates. Rules interpret. Database stores. Engineer decides.*",
        ])
        return "\n".join(lines)
