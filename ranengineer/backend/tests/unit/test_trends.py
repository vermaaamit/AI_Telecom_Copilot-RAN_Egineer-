from datetime import datetime, timezone
from app.analytics.trends.engine import TrendEngine
from app.analytics.trends.models import TrendDirection
from app.config.database import SessionLocal
from app.models.dataset import CellModel, DatasetModel


def test_trend_engine_detects_degradation():
    with SessionLocal() as db:
        # Create 2 historical datasets for the same cell
        d1 = DatasetModel(
            id="ds-t1",
            name="Day 1",
            filename="day1.csv",
            technology="LTE",
            created_at=datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc),
            row_count=1,
            cell_count=1,
            available_kpis=["PRB_UTILIZATION", "THROUGHPUT_DL"],
            unsupported_columns=[],
            invalid_values=[],
            summary={},
        )
        c1 = CellModel(
            dataset_id="ds-t1",
            cell_id="CELL_TREND_1",
            site_id="SITE_T1",
            health_score=85,
            status="HEALTHY",
            kpis={"PRB_UTILIZATION": 45.0, "THROUGHPUT_DL": 25.0},
            original={},
            issues=[],
            kpi_statuses={"PRB_UTILIZATION": "HEALTHY", "THROUGHPUT_DL": "HEALTHY"},
            probable_causes=[],
        )
        d1.cells.append(c1)
        db.add(d1)

        d2 = DatasetModel(
            id="ds-t2",
            name="Day 2",
            filename="day2.csv",
            technology="LTE",
            created_at=datetime(2026, 10, 2, 10, 0, tzinfo=timezone.utc),
            row_count=1,
            cell_count=1,
            available_kpis=["PRB_UTILIZATION", "THROUGHPUT_DL"],
            unsupported_columns=[],
            invalid_values=[],
            summary={},
        )
        c2 = CellModel(
            dataset_id="ds-t2",
            cell_id="CELL_TREND_1",
            site_id="SITE_T1",
            health_score=60,
            status="WARNING",
            # PRB increased significantly (degradation), Throughput decreased (degradation)
            kpis={"PRB_UTILIZATION": 82.0, "THROUGHPUT_DL": 12.0},
            original={},
            issues=[],
            kpi_statuses={"PRB_UTILIZATION": "WARNING", "THROUGHPUT_DL": "WARNING"},
            probable_causes=[],
        )
        d2.cells.append(c2)
        db.add(d2)
        db.commit()

        engine = TrendEngine(db)
        trends = engine.calculate_cell_trends("CELL_TREND_1")
        assert trends is not None
        assert trends.data_points_count == 2
        assert trends.overall_health_trend == TrendDirection.DEGRADING

        prb_trend = trends.trends["PRB_UTILIZATION"]
        assert prb_trend.trend_direction == TrendDirection.DEGRADING
        assert prb_trend.slope > 0
        assert len(prb_trend.points) == 2

        dl_trend = trends.trends["THROUGHPUT_DL"]
        assert dl_trend.trend_direction == TrendDirection.DEGRADING
        assert dl_trend.slope < 0

