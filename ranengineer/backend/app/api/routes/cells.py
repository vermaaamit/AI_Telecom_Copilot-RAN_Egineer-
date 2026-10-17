from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.repositories.dataset_repository import DatasetRepository

router = APIRouter(prefix="/cells", tags=["cells"])


def find_cell(cell_id: str, db: Session) -> dict[str, object]:
    cell = DatasetRepository(db).find_cell(cell_id)
    if cell:
        return cell
    raise HTTPException(404, detail={"error": {"code": "CELL_NOT_FOUND", "message": "Cell was not found in analyzed datasets.", "details": []}})


@router.get("/{cell_id}", summary="Get a cell")
def get_cell(cell_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    return find_cell(cell_id, db)


@router.get("/{cell_id}/analysis", summary="Get deterministic cell analysis")
def get_cell_analysis(cell_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    cell = find_cell(cell_id, db)
    recommended_checks = []
    for cause in cell.get("probable_causes", []):
        for check in cause.get("recommended_checks", []):
            if check not in recommended_checks:
                recommended_checks.append(check)
    return {
        "cell_id": cell["cell_id"],
        "site_id": cell.get("site_id"),
        "technology": cell.get("technology"),
        "health_score": cell.get("health_score"),
        "status": cell.get("status"),
        "kpis": cell.get("kpis", {}),
        "kpi_statuses": cell.get("kpi_statuses", {}),
        "issues": cell.get("issues", []),
        "probable_causes": cell.get("probable_causes", []),
        "recommended_checks": recommended_checks,
        "summary": f"Cell {cell['cell_id']} has an application-defined health score of {cell.get('health_score')}/100 ({cell.get('status')}).",
        "limitations": "Analysis is calculated deterministically from available KPI data. Inferences represent rule-based probable causes, not confirmed field faults."
    }


@router.get("/{cell_id}/rca", summary="Enhanced Root Cause Analysis with Alarm Correlation")
def get_cell_rca(cell_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    from app.alarms import get_alarm_store
    from app.analytics.correlation import get_correlation_engine

    cell = find_cell(cell_id, db)
    alarms = get_alarm_store().list_all()
    result = get_correlation_engine().correlate_cell_with_alarms(cell, alarms)
    return result.model_dump(mode="json")


@router.get("/{cell_id}/trends", summary="Time-series KPI trends across historical datasets")
def get_cell_trends(cell_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    from app.analytics.trends import TrendEngine

    trends = TrendEngine(db).calculate_cell_trends(cell_id)
    if not trends:
        raise HTTPException(404, detail={"error": {"code": "CELL_NOT_FOUND", "message": f"Cell {cell_id} not found in historical datasets.", "details": []}})
    return trends.model_dump(mode="json")

