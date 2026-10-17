from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.dataset import CellModel, DatasetModel


def cell_to_dict(cell: CellModel) -> dict[str, object]:
    return {"cell_id": cell.cell_id, "site_id": cell.site_id, "technology": cell.technology, "kpis": cell.kpis, "original": cell.original, "health_score": cell.health_score, "status": cell.status, "issues": cell.issues, "kpi_statuses": cell.kpi_statuses, "kpi_degradation": cell.kpi_degradation or [], "probable_causes": cell.probable_causes}


def dataset_to_dict(dataset: DatasetModel, include_cells: bool = True) -> dict[str, object]:
    result = {"id": dataset.id, "name": dataset.name, "filename": dataset.filename, "technology": dataset.technology, "created_at": dataset.created_at.isoformat(), "row_count": dataset.row_count, "cell_count": dataset.cell_count, "available_kpis": dataset.available_kpis, "unsupported_columns": dataset.unsupported_columns, "invalid_values": dataset.invalid_values, "summary": dataset.summary}
    if include_cells:
        result["cells"] = [cell_to_dict(cell) for cell in dataset.cells]
    return result


class DatasetRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def save(self, analysis: dict[str, object]) -> dict[str, object]:
        dataset = DatasetModel(id=analysis["id"], name=analysis["name"], filename=analysis["filename"], technology=analysis["technology"], created_at=analysis["created_at"], row_count=analysis["row_count"], cell_count=analysis["cell_count"], available_kpis=analysis["available_kpis"], unsupported_columns=analysis["unsupported_columns"], invalid_values=analysis["invalid_values"], summary=analysis["summary"])
        for cell in analysis["cells"]:
            dataset.cells.append(CellModel(dataset_id=analysis["id"], cell_id=cell["cell_id"], site_id=cell["site_id"], technology=cell["technology"], kpis=cell["kpis"], original=cell["original"], health_score=cell["health_score"], status=cell["status"], issues=cell["issues"], kpi_statuses=cell["kpi_statuses"], kpi_degradation=cell.get("kpi_degradation", []), probable_causes=cell["probable_causes"]))
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)
        return dataset_to_dict(dataset)

    def get(self, dataset_id: str) -> dict[str, object] | None:
        dataset = self.db.scalar(select(DatasetModel).where(DatasetModel.id == dataset_id).options(selectinload(DatasetModel.cells)))
        return dataset_to_dict(dataset) if dataset else None

    def list(self) -> list[dict[str, object]]:
        datasets = self.db.scalars(select(DatasetModel).order_by(DatasetModel.created_at.desc())).all()
        return [dataset_to_dict(dataset, include_cells=False) for dataset in datasets]

    def find_cell(self, cell_id: str) -> dict[str, object] | None:
        cell = self.db.scalar(select(CellModel).where(CellModel.cell_id == cell_id).options(selectinload(CellModel.dataset)))
        return {"dataset_id": cell.dataset_id, **cell_to_dict(cell)} if cell else None
