from datetime import datetime
from sqlalchemy import DateTime, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base

class AlarmModel(Base):
    __tablename__ = "alarms"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    site_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    cell_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    technology: Mapped[str | None] = mapped_column(String(32), nullable=True)
    alarm_type: Mapped[str] = mapped_column(String(128), index=True)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    description: Mapped[str] = mapped_column(String(512))
    source: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    synthetic: Mapped[bool] = mapped_column(default=False)
