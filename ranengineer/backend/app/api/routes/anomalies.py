from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.dataset import CellModel
from app.repositories.dataset_repository import cell_to_dict

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("", summary="List critical cell anomalies")
def list_anomalies(limit: int = Query(50, ge=1, le=500), dataset_id: str | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
    query = select(CellModel).where(CellModel.status == "CRITICAL")
    if dataset_id:
        query = query.where(CellModel.dataset_id == dataset_id)
    query = query.order_by(CellModel.health_score.asc().nulls_first()).limit(limit)
    cells = db.scalars(query).all()
    items = [cell_to_dict(cell) for cell in cells]
    return {"items": items, "total": len(items)}


@router.get("/predictive", summary="Predictive anomaly detection across historical datasets")
def get_predictive_anomalies(db: Session = Depends(get_db)) -> dict[str, object]:
    from app.analytics.predictive import PredictiveAnomalyEngine
    report = PredictiveAnomalyEngine(db).analyze_predictive_anomalies()
    return report.model_dump(mode="json")

