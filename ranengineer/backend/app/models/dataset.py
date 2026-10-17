from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class DatasetModel(Base):
    __tablename__ = "datasets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    filename: Mapped[str] = mapped_column(String(255))
    technology: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    row_count: Mapped[int] = mapped_column(Integer)
    cell_count: Mapped[int] = mapped_column(Integer)
    available_kpis: Mapped[list] = mapped_column(JSON)
    unsupported_columns: Mapped[list] = mapped_column(JSON)
    invalid_values: Mapped[list] = mapped_column(JSON)
    summary: Mapped[dict] = mapped_column(JSON)
    cells: Mapped[list["CellModel"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")


class CellModel(Base):
    __tablename__ = "cells"
    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"), index=True)
    cell_id: Mapped[str] = mapped_column(String(128), index=True)
    site_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    technology: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    health_score: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(16), index=True)
    kpis: Mapped[dict] = mapped_column(JSON)
    original: Mapped[dict] = mapped_column(JSON)
    issues: Mapped[list] = mapped_column(JSON)
    kpi_statuses: Mapped[dict] = mapped_column(JSON)
    kpi_degradation: Mapped[list] = mapped_column(JSON, default=list)
    probable_causes: Mapped[list] = mapped_column(JSON)
    dataset: Mapped[DatasetModel] = relationship(back_populates="cells")
