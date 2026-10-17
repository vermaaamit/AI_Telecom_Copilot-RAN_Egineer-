import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select

from app.config.database import SessionLocal
from app.incidents.models import Incident, IncidentCreate, IncidentStatus, IncidentSeverity
from app.models.incident import IncidentModel

class IncidentStore:
    def create(self, payload: IncidentCreate) -> Incident:
        now = datetime.now(timezone.utc)
        incident_id = f"INC-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        db_incident = IncidentModel(
            id=incident_id,
            title=payload.title,
            description=payload.description,
            severity=payload.severity.value,
            status=payload.status.value,
            created_at=now,
            updated_at=now,
            affected_cells=payload.affected_cells,
            related_alarms=payload.related_alarms,
        )
        
        with SessionLocal() as db:
            db.add(db_incident)
            db.commit()
            db.refresh(db_incident)
            return self._to_pydantic(db_incident)

    def get(self, incident_id: str) -> Optional[Incident]:
        with SessionLocal() as db:
            db_incident = db.scalar(select(IncidentModel).where(IncidentModel.id == incident_id))
            return self._to_pydantic(db_incident) if db_incident else None

    def list_all(self) -> list[Incident]:
        with SessionLocal() as db:
            db_incidents = db.scalars(select(IncidentModel).order_by(IncidentModel.created_at.desc())).all()
            return [self._to_pydantic(i) for i in db_incidents]

    def list_open(self) -> list[Incident]:
        with SessionLocal() as db:
            db_incidents = db.scalars(select(IncidentModel).where(IncidentModel.status == IncidentStatus.OPEN.value).order_by(IncidentModel.created_at.desc())).all()
            return [self._to_pydantic(i) for i in db_incidents]

    def resolve(self, incident_id: str, resolution: str) -> Optional[Incident]:
        with SessionLocal() as db:
            db_incident = db.scalar(select(IncidentModel).where(IncidentModel.id == incident_id))
            if db_incident:
                db_incident.status = IncidentStatus.RESOLVED.value
                db_incident.resolution = resolution
                db_incident.updated_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(db_incident)
                return self._to_pydantic(db_incident)
        return None

    def _to_pydantic(self, model: IncidentModel) -> Incident:
        return Incident(
            id=model.id,
            title=model.title,
            description=model.description,
            severity=IncidentSeverity(model.severity),
            status=IncidentStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            resolution=model.resolution,
            affected_cells=model.affected_cells,
            related_alarms=model.related_alarms,
        )

_incident_store: IncidentStore | None = None

def get_incident_store() -> IncidentStore:
    global _incident_store
    if _incident_store is None:
        _incident_store = IncidentStore()
    return _incident_store

__all__ = ["IncidentStore", "get_incident_store"]

