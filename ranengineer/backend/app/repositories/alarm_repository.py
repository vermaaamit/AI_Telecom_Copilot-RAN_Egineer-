from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.alarm import AlarmModel
from datetime import datetime, timezone
import uuid

def alarm_to_dict(alarm: AlarmModel) -> dict[str, object]:
    return {
        "id": alarm.id,
        "alarm_id": alarm.id,
        "cell_id": alarm.cell_id,
        "severity": alarm.severity,
        "alarm_type": alarm.alarm_type,
        "description": alarm.description,
        "timestamp": alarm.timestamp.isoformat() if alarm.timestamp else None,
        "created_at": alarm.timestamp.isoformat() if alarm.timestamp else None,
        "status": alarm.status,
        "metadata": alarm.details or {}
    }

class AlarmRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def save(self, payload: dict) -> dict[str, object]:
        now = datetime.now(timezone.utc)
        alarm_id = payload.get("alarm_id") or f"ALM-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        alarm = AlarmModel(
            id=alarm_id,
            cell_id=payload.get("cell_id", ""),
            severity=payload.get("severity", "WARNING").upper(),
            alarm_type=payload.get("alarm_type", "UNKNOWN"),
            description=payload.get("description", ""),
            timestamp=payload.get("timestamp", now),
            status=payload.get("status", "ACTIVE"),
            details=payload.get("metadata", {})
        )
        self.db.add(alarm)
        self.db.commit()
        self.db.refresh(alarm)
        return alarm_to_dict(alarm)

    def get(self, alarm_id: str) -> dict[str, object] | None:
        alarm = self.db.scalar(select(AlarmModel).where(AlarmModel.id == alarm_id))
        return alarm_to_dict(alarm) if alarm else None

    def list_all(self) -> list[dict[str, object]]:
        alarms = self.db.scalars(select(AlarmModel).order_by(AlarmModel.timestamp.desc())).all()
        return [alarm_to_dict(a) for a in alarms]

    def list_active(self) -> list[dict[str, object]]:
        alarms = self.db.scalars(select(AlarmModel).where(AlarmModel.status == "ACTIVE").order_by(AlarmModel.timestamp.desc())).all()
        return [alarm_to_dict(a) for a in alarms]

    def list_critical(self) -> list[dict[str, object]]:
        alarms = self.db.scalars(select(AlarmModel).where(AlarmModel.severity == "CRITICAL").order_by(AlarmModel.timestamp.desc())).all()
        return [alarm_to_dict(a) for a in alarms]

    def update_status(self, alarm_id: str, new_status: str) -> dict[str, object] | None:
        alarm = self.db.scalar(select(AlarmModel).where(AlarmModel.id == alarm_id))
        if not alarm:
            return None
        alarm.status = new_status
        self.db.commit()
        self.db.refresh(alarm)
        return alarm_to_dict(alarm)

