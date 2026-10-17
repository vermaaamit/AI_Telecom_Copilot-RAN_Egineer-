from datetime import datetime, timezone
from app.analytics.predictive.engine import PredictiveAnomalyEngine
from app.analytics.predictive.models import PredictiveRiskLevel
from app.config.database import SessionLocal
from app.models.dataset import CellModel, DatasetModel


def test_predictive_anomaly_detection_velocity():
    with SessionLocal() as db:
        # Create baseline and recent dataset
        # PRB is 70% in ds1, rises to 80% in ds2 (velocity +10). Next projected is 90% (>= 85% CRITICAL)
        d1 = DatasetModel(
            id="ds-pred-1",
            name="Pred 1",
            filename="p1.csv",
            technology="LTE",
            created_at=datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc),
            row_count=1,
            cell_count=1,
            available_kpis=["PRB_UTILIZATION"],
            unsupported_columns=[],
            invalid_values=[],
            summary={},
        )
        c1 = CellModel(
            dataset_id="ds-pred-1",
            cell_id="CELL_PRED_1",
            site_id="SITE_P1",
            health_score=75,
            status="WARNING",
            kpis={"PRB_UTILIZATION": 75.0},
            original={},
            issues=[],
            kpi_statuses={"PRB_UTILIZATION": "WARNING"},
            probable_causes=[],
        )
        d1.cells.append(c1)
        db.add(d1)

        d2 = DatasetModel(
            id="ds-pred-2",
            name="Pred 2",
            filename="p2.csv",
            technology="LTE",
            created_at=datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc),
            row_count=1,
            cell_count=1,
            available_kpis=["PRB_UTILIZATION"],
            unsupported_columns=[],
            invalid_values=[],
            summary={},
        )
        c2 = CellModel(
            dataset_id="ds-pred-2",
            cell_id="CELL_PRED_1",
            site_id="SITE_P1",
            health_score=60,
            status="CRITICAL",
            kpis={"PRB_UTILIZATION": 89.0},
            original={},
            issues=[],
            kpi_statuses={"PRB_UTILIZATION": "WARNING"},
            probable_causes=[],
        )
        d2.cells.append(c2)
        db.add(d2)
        db.commit()

        engine = PredictiveAnomalyEngine(db)
        report = engine.analyze_predictive_anomalies()
        assert report.total_evaluated_cells >= 1
        assert report.at_risk_cells_count >= 1

        target = next((item for item in report.items if item.cell_id == "CELL_PRED_1"), None)
        assert target is not None
        assert target.risk_level == PredictiveRiskLevel.HIGH_RISK
        assert target.projected_value >= 85.0
        assert "carrier aggregation" in target.recommended_action.lower()
