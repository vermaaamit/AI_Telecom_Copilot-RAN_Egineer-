from __future__ import annotations

import uuid
from typing import Any
from sqlalchemy.orm import Session

from app.ai.agents.models import (
    AgentContribution,
    AgentRole,
    MultiAgentInvestigationReport,
)
from app.alarms import get_alarm_store
from app.analytics.correlation import get_correlation_engine
from app.analytics.predictive import PredictiveAnomalyEngine
from app.ai.rag import get_knowledge_retriever
from app.repositories.dataset_repository import DatasetRepository


class MultiAgentOrchestrator:
    """Orchestrates cooperative specialized agents to investigate network entities."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = DatasetRepository(db)

    def investigate_cell(self, cell_id: str) -> MultiAgentInvestigationReport | None:
        cell = self.repo.find_cell(cell_id)
        if not cell:
            return None

        site_id = cell.get("site_id")
        health_score = cell.get("health_score")
        kpis = cell.get("kpis", {}) or {}
        kpi_statuses = cell.get("kpi_statuses", {}) or {}
        probable_causes = cell.get("probable_causes", []) or []

        contributions: list[AgentContribution] = []
        consolidated_remediations: list[str] = []
        standards_references: list[str] = []

        # 1. KpiAgent
        kpi_findings = []
        for kpi_name, status in kpi_statuses.items():
            if str(status).upper() in ("CRITICAL", "WARNING"):
                kpi_findings.append(f"{kpi_name} evaluated as {status} (value: {kpis.get(kpi_name)}).")
        if not kpi_findings:
            kpi_findings.append("All reported telemetry values fall within standard operational bounds.")

        contributions.append(
            AgentContribution(
                role=AgentRole.KPI_ANALYST,
                agent_name="KPI Telemetry Analyst",
                findings=kpi_findings,
                metrics_evaluated=kpis,
                recommendations=["Continue telemetry sampling at regular 15-minute intervals."],
            )
        )

        # 2. AnomalyAgent
        anomaly_findings = []
        pred_engine = PredictiveAnomalyEngine(self.db)
        pred_report = pred_engine.analyze_predictive_anomalies()
        cell_pred = next((i for i in pred_report.items if i.cell_id == cell_id), None)
        if cell_pred:
            anomaly_findings.append(
                f"Predictive anomaly detected: {cell_pred.kpi_name} with velocity {cell_pred.velocity_rate:+}/interval. {cell_pred.projected_breach_condition}."
            )
            consolidated_remediations.append(cell_pred.recommended_action)
        else:
            anomaly_findings.append("No acute predictive degradation velocity detected across historical datasets.")

        contributions.append(
            AgentContribution(
                role=AgentRole.ANOMALY_DETECTOR,
                agent_name="Anomaly & Velocity Specialist",
                findings=anomaly_findings,
                metrics_evaluated={"predictive_anomaly_present": cell_pred is not None},
                recommendations=[cell_pred.recommended_action] if cell_pred else [],
            )
        )

        # 3. RcaAgent
        rca_findings = []
        alarms = get_alarm_store().list_all()
        corr_engine = get_correlation_engine()
        rca_res = corr_engine.correlate_cell_with_alarms(cell, alarms)

        if rca_res.correlated_alarms:
            for ca in rca_res.correlated_alarms:
                rca_findings.append(
                    f"Correlated alarm [{ca.alarm_type}] ({ca.confidence.value} confidence): {ca.description}."
                )
        elif probable_causes:
            for pc in probable_causes:
                rca_findings.append(f"Rule-based RCA hypothesis: {pc.get('description', '')}.")
        else:
            rca_findings.append("No active correlated alarms or rule triggers matched.")

        contributions.append(
            AgentContribution(
                role=AgentRole.RCA_SPECIALIST,
                agent_name="Root Cause & Alarm Specialist",
                findings=rca_findings,
                metrics_evaluated={"correlated_alarms_count": len(rca_res.correlated_alarms)},
                recommendations=rca_res.recommended_actions,
            )
        )
        for act in rca_res.recommended_actions:
            if act not in consolidated_remediations:
                consolidated_remediations.append(act)

        # 4. KnowledgeAgent (RAG)
        rag_findings = []
        search_query = f"{cell.get('technology', 'RAN')} {' '.join([pc.get('category', '') for pc in probable_causes])} {' '.join(kpi_findings)}"
        knowledge_res = get_knowledge_retriever().search_ran_knowledge(search_query, limit=2)
        for doc in knowledge_res.documents:
            standards_references.append(f"{doc.id}: {doc.title} ({doc.source})")
            rag_findings.append(f"Standard {doc.title}: {doc.content[:160]}...")

        contributions.append(
            AgentContribution(
                role=AgentRole.STANDARDS_ENGINEER,
                agent_name="3GPP & O-RAN Standards Specialist",
                findings=rag_findings or ["Referenced standard 3GPP RAN troubleshooting profiles."],
                metrics_evaluated={"matched_standards_count": len(knowledge_res.documents)},
                recommendations=["Align cell parameter bounds with 3GPP specifications."],
            )
        )

        # 5. OptimizationAgent
        opt_actions = []
        if any("PRB" in f for f in kpi_findings):
            opt_actions.append("Adjust carrier aggregation secondary cell (SCell) priorities to offload PRBs.")
        if any("RSRP" in f or "SINR" in f for f in kpi_findings):
            opt_actions.append("Perform remote electrical tilt (RET) down-tilt by 2 degrees to contain cell footprint.")
        if any("HANDOVER" in f or "DROP" in f for f in kpi_findings):
            opt_actions.append("Audit Automatic Neighbor Relations (ANR) and increase Time-to-Trigger (TTT) to 160ms.")

        if not opt_actions:
            opt_actions.append("Maintain baseline parameters; schedule routine drive-test audit.")

        contributions.append(
            AgentContribution(
                role=AgentRole.OPTIMIZATION_ENGINEER,
                agent_name="RAN Parameter Optimization Specialist",
                findings=[f"Recommended {len(opt_actions)} parameter adjustment action(s)."],
                metrics_evaluated={},
                recommendations=opt_actions,
            )
        )
        for act in opt_actions:
            if act not in consolidated_remediations:
                consolidated_remediations.append(act)

        # 6. Overall Verdict synthesis
        verdict = (
            f"Multi-Agent investigation concluded for Cell {cell_id} (Health: {health_score}/100, {cell.get('status')}). "
            f"{rca_res.primary_hypothesis or 'Cell is operating within nominal thresholds.'}"
        )

        return MultiAgentInvestigationReport(
            investigation_id=f"INV-{uuid.uuid4().hex[:8].upper()}",
            target_cell_id=cell_id,
            target_site_id=site_id,
            health_score=health_score,
            overall_verdict=verdict,
            agent_contributions=contributions,
            consolidated_remediations=consolidated_remediations,
            standards_references=standards_references,
        )

