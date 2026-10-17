"""Alarm API routes for AI Telecom Copilot – RAN Engineer.

Phase 1 API (subset of full alarm API defined in project spec section 27):

  GET  /api/v1/alarms              – list all alarms
  GET  /api/v1/alarms/active       – list active alarms
  GET  /api/v1/alarms/critical     – list critical alarms
  GET  /api/v1/alarms/{alarm_id}   – get alarm by ID
  POST /api/v1/alarms              – create alarm (internal / test)
  PATCH /api/v1/alarms/{alarm_id}/acknowledge
  PATCH /api/v1/alarms/{alarm_id}/clear

Full OSS/EMS alarm integration is deferred to future phases.
"""
from fastapi import APIRouter, HTTPException

from app.alarms import AlarmCreate, get_alarm_store

router = APIRouter(prefix="/alarms", tags=["alarms"])


@router.get("", summary="List all alarms")
def list_alarms() -> list[dict]:
    return [a.model_dump(mode="json") for a in get_alarm_store().list_all()]


@router.get("/active", summary="List active alarms")
def list_active_alarms() -> list[dict]:
    return [a.model_dump(mode="json") for a in get_alarm_store().list_active()]


@router.get("/critical", summary="List critical alarms")
def list_critical_alarms() -> list[dict]:
    return [a.model_dump(mode="json") for a in get_alarm_store().list_critical()]


@router.get("/{alarm_id}", summary="Get alarm by ID")
def get_alarm(alarm_id: str) -> dict:
    alarm = get_alarm_store().get(alarm_id)
    if not alarm:
        raise HTTPException(404, detail={"error": {"code": "ALARM_NOT_FOUND", "message": f"Alarm {alarm_id} not found.", "details": []}})
    return alarm.model_dump(mode="json")


@router.post("", status_code=201, summary="Create an alarm (internal/synthetic)")
def create_alarm(payload: AlarmCreate) -> dict:
    alarm = get_alarm_store().create(payload)
    return alarm.model_dump(mode="json")


@router.patch("/{alarm_id}/acknowledge", summary="Acknowledge an alarm")
def acknowledge_alarm(alarm_id: str) -> dict:
    alarm = get_alarm_store().acknowledge(alarm_id)
    if not alarm:
        raise HTTPException(404, detail={"error": {"code": "ALARM_NOT_FOUND", "message": f"Alarm {alarm_id} not found.", "details": []}})
    return alarm.model_dump(mode="json")


@router.patch("/{alarm_id}/clear", summary="Clear an alarm")
def clear_alarm(alarm_id: str) -> dict:
    alarm = get_alarm_store().clear(alarm_id)
    if not alarm:
        raise HTTPException(404, detail={"error": {"code": "ALARM_NOT_FOUND", "message": f"Alarm {alarm_id} not found.", "details": []}})
    return alarm.model_dump(mode="json")

