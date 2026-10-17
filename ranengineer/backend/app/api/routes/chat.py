from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.ai.grounded_chat import answer_question
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.dataset import ChatRequest
from app.services.dataset_service import find_underperforming_cells

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", summary="Ask a grounded dataset question")
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    dataset = DatasetRepository(db).get(request.dataset_id)
    if not dataset:
        raise HTTPException(404, detail={"error": {"code": "DATASET_NOT_FOUND", "message": "Dataset was not found.", "details": []}})
    return answer_question(request.question, dataset)
