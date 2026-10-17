"""SQLAlchemy-backed alarm store for Phase 2."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select

from app.alarms.models import Alarm, AlarmCreate, AlarmSeverity, AlarmStatus, AlarmType
from app.config.database import SessionLocal
from app.models.alarm import AlarmModel


class AlarmStore:
    """SQLAlchemy-backed alarm repository."""

    def create(self, payload: AlarmCreate) -> Alarm:
        now = datetime.now(timezone.utc)
        alarm_id = f"ALM-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        db_alarm = AlarmModel(
            id=alarm_id,
            site_id=payload.site_id,
            cell_id=payload.cell_id,
            technology=payload.technology,
            alarm_type=payload.alarm_type,
            severity=payload.severity,
            status=payload.status,
            description=payload.description,
            source=payload.source,
            started_at=now,
            created_at=now,
            details=payload.metadata,
            synthetic=payload.synthetic
        )
        
        with SessionLocal() as db:
            db.add(db_alarm)
            db.commit()
            db.refresh(db_alarm)
            return self._to_pydantic(db_alarm)

    def get(self, alarm_id: str) -> Optional[Alarm]:
        with SessionLocal() as db:
            db_alarm = db.scalar(select(AlarmModel).where(AlarmModel.id == alarm_id))
            return self._to_pydantic(db_alarm) if db_alarm else None

    def list_all(self) -> list[Alarm]:
        with SessionLocal() as db:
            db_alarms = db.scalars(select(AlarmModel).order_by(AlarmModel.started_at.desc())).all()
            return [self._to_pydantic(a) for a in db_alarms]

    def list_active(self) -> list[Alarm]:
        with SessionLocal() as db:
            db_alarms = db.scalars(select(AlarmModel).where(AlarmModel.status == AlarmStatus.ACTIVE.value).order_by(AlarmModel.started_at.desc())).all()
            return [self._to_pydantic(a) for a in db_alarms]

    def list_critical(self) -> list[Alarm]:
        with SessionLocal() as db:
            db_alarms = db.scalars(select(AlarmModel).where(AlarmModel.severity == AlarmSeverity.CRITICAL.value).order_by(AlarmModel.started_at.desc())).all()
            return [self._to_pydantic(a) for a in db_alarms]

    def acknowledge(self, alarm_id: str) -> Optional[Alarm]:
        with SessionLocal() as db:
            db_alarm = db.scalar(select(AlarmModel).where(AlarmModel.id == alarm_id))
            if db_alarm:
                db_alarm.status = AlarmStatus.ACKNOWLEDGED.value
                db_alarm.updated_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(db_alarm)
                return self._to_pydantic(db_alarm)
        return None

    def clear(self, alarm_id: str) -> Optional[Alarm]:
        with SessionLocal() as db:
            db_alarm = db.scalar(select(AlarmModel).where(AlarmModel.id == alarm_id))
            if db_alarm:
                db_alarm.status = AlarmStatus.CLEARED.value
                db_alarm.ended_at = datetime.now(timezone.utc)
                db_alarm.updated_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(db_alarm)
                return self._to_pydantic(db_alarm)
        return None

    def create_security_alarm(
        self,
        *,
        filename: str,
        reason: str,
        request_id: str = "",
    ) -> Alarm:
        """Convenience factory for SUSPICIOUS_FILE_UPLOAD security alarms."""
        return self.create(
            AlarmCreate(
                alarm_type=AlarmType.SUSPICIOUS_FILE_UPLOAD,
                severity=AlarmSeverity.CRITICAL,
                status=AlarmStatus.ACTIVE,
                description=(
                    f"Suspicious file upload detected and blocked. "
                    f"Filename: {filename}. Reason: {reason}."
                ),
                source="FILE_UPLOAD",
                metadata={
                    "filename": filename,
                    "reason": reason,
                    "request_id": request_id,
                    "action": "BLOCKED",
                },
            )
        )

    def _to_pydantic(self, model: AlarmModel) -> Alarm:
        return Alarm(
            alarm_id=model.id,
            site_id=model.site_id,
            cell_id=model.cell_id,
            technology=model.technology,
            alarm_type=AlarmType(model.alarm_type),
            severity=AlarmSeverity(model.severity),
            status=AlarmStatus(model.status),
            started_at=model.started_at,
            ended_at=model.ended_at,
            description=model.description,
            source=model.source,
            created_at=model.created_at,
            updated_at=model.updated_at,
            metadata=model.details,
            synthetic=model.synthetic,
        )

# Application-scoped singleton
_alarm_store: AlarmStore | None = None

def get_alarm_store() -> AlarmStore:
    global _alarm_store
    if _alarm_store is None:
        _alarm_store = AlarmStore()
    return _alarm_store

__all__ = ["AlarmStore", "get_alarm_store"]
