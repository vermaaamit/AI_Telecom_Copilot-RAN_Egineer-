from datetime import datetime, timezone
from app.ai.agents.orchestrator import MultiAgentOrchestrator
from app.config.database import SessionLocal
from app.models.dataset import CellModel, DatasetModel


def test_multi_agent_investigation_orchestration():
    with SessionLocal() as db:
        # Seed test dataset and cell
        d = DatasetModel(
            id="ds-agent-test",
            name="Agent Test Dataset",
            filename="agent_test.csv",
            technology="LTE",
            created_at=datetime.now(timezone.utc),
            row_count=1,
            cell_count=1,
            available_kpis=["PRB_UTILIZATION", "SINR"],
            unsupported_columns=[],
            invalid_values=[],
            summary={},
        )
        c = CellModel(
            dataset_id="ds-agent-test",
            cell_id="CELL_AGENT_100",
            site_id="SITE_AGENT_10",
            health_score=45,
            status="CRITICAL",
            kpis={"PRB_UTILIZATION": 92.0, "SINR": -2.0},
            original={},
            issues=["High PRB Congestion", "Poor Radio Quality"],
            kpi_statuses={"PRB_UTILIZATION": "CRITICAL", "SINR": "CRITICAL"},
            probable_causes=[
                {
                    "category": "Congestion",
                    "description": "High PRB load exceeding threshold",
                    "recommended_checks": ["Check carrier load"],
                }
            ],
        )
        d.cells.append(c)
        db.add(d)
        db.commit()

        orchestrator = MultiAgentOrchestrator(db)
        report = orchestrator.investigate_cell("CELL_AGENT_100")
        assert report is not None
        assert report.target_cell_id == "CELL_AGENT_100"
        assert report.health_score == 45
        assert len(report.agent_contributions) == 5  # KPI, Anomaly, RCA, Standards, Optimization
        assert len(report.consolidated_remediations) >= 1
        assert len(report.standards_references) >= 1
        assert "CELL_AGENT_100" in report.overall_verdict


def test_multi_agent_investigation_nonexistent_cell():
    with SessionLocal() as db:
        orchestrator = MultiAgentOrchestrator(db)
        report = orchestrator.investigate_cell("NONEXISTENT_CELL_9999")
        assert report is None

