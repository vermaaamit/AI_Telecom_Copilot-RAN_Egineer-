from datetime import datetime, timezone
from sqlalchemy import DateTime, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base

class IncidentModel(Base):
    __tablename__ = "incidents"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(1024))
    severity: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    resolution: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    
    # Store related cell IDs and alarm IDs as JSON arrays
    affected_cells: Mapped[list] = mapped_column(JSON, default=list)
    related_alarms: Mapped[list] = mapped_column(JSON, default=list)

