from fastapi import APIRouter

from app.config.kpi_config import get_kpi_definitions

router = APIRouter(prefix="/kpis", tags=["kpis"])


@router.get("", summary="Get configured KPI definitions")
def list_kpis() -> dict[str, object]:
    return {"items": get_kpi_definitions()}
