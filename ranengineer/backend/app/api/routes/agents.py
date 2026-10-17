from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.agents import MultiAgentOrchestrator
from app.config.database import get_db

router = APIRouter(prefix="/agents", tags=["agents"])


class CellInvestigationRequest(BaseModel):
    cell_id: str


@router.post("/investigate", summary="Multi-Agent Cooperative Cell Investigation")
def investigate_cell(
    payload: CellInvestigationRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    orchestrator = MultiAgentOrchestrator(db)
    report = orchestrator.investigate_cell(payload.cell_id)
    if not report:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "CELL_NOT_FOUND",
                    "message": f"Cell {payload.cell_id} was not found in analyzed datasets.",
                    "details": [],
                }
            },
        )
    return report.model_dump(mode="json")

