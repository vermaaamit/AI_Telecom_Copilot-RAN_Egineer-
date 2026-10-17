from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.dataset_repository import DatasetRepository


def get_dataset_or_404(db: Session, dataset_id: str) -> dict[str, object]:
    dataset = DatasetRepository(db).get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail={"error": {"code": "DATASET_NOT_FOUND", "message": "Dataset was not found.", "details": []}})
    return dataset
