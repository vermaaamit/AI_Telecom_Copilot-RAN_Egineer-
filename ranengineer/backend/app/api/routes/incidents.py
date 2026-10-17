from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.incidents import IncidentCreate, get_incident_store

router = APIRouter(prefix="/incidents", tags=["incidents"])

@router.get("", summary="List all incidents")
def list_incidents() -> list[dict]:
    return [i.model_dump(mode="json") for i in get_incident_store().list_all()]

@router.get("/open", summary="List open incidents")
def list_open_incidents() -> list[dict]:
    return [i.model_dump(mode="json") for i in get_incident_store().list_open()]

@router.get("/{incident_id}", summary="Get incident by ID")
def get_incident(incident_id: str) -> dict:
    incident = get_incident_store().get(incident_id)
    if not incident:
        raise HTTPException(404, detail={"error": {"code": "INCIDENT_NOT_FOUND", "message": f"Incident {incident_id} not found.", "details": []}})
    return incident.model_dump(mode="json")

@router.post("", status_code=201, summary="Create an incident")
def create_incident(payload: IncidentCreate) -> dict:
    incident = get_incident_store().create(payload)
    return incident.model_dump(mode="json")

class IncidentResolution(BaseModel):
    resolution: str

@router.patch("/{incident_id}/resolve", summary="Resolve an incident")
def resolve_incident(incident_id: str, payload: IncidentResolution) -> dict:
    incident = get_incident_store().resolve(incident_id, payload.resolution)
    if not incident:
        raise HTTPException(404, detail={"error": {"code": "INCIDENT_NOT_FOUND", "message": f"Incident {incident_id} not found.", "details": []}})
    return incident.model_dump(mode="json")

