"""Security Auditing, Redis Counter Metrics & Prompt Inspection API Routes."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.security.auditor import (
    PromptInspectionResult,
    SecurityAuditEvent,
    SecurityAuditor,
    get_security_auditor,
)
from app.security.auth import User, UserRole, get_current_user, require_role
from app.security.counters import SecurityCounterStore, get_security_counter_store

router = APIRouter(prefix="/security", tags=["Security Auditing & Threat Monitoring"])


class InspectPromptRequest(BaseModel):
    prompt: str


@router.get("/metrics")
async def get_security_metrics(
    counters: SecurityCounterStore = Depends(get_security_counter_store),
    current_user: User = Depends(get_current_user),
):
    """Retrieve Redis-backed security counters and threat mitigation stats."""
    return counters.get_metrics()


@router.get("/audit-log", response_model=List[SecurityAuditEvent])
async def list_security_audit_events(
    limit: int = Query(50, ge=1, le=200),
    severity: Optional[str] = Query(None, description="Filter by INFO, WARNING, CRITICAL"),
    auditor: SecurityAuditor = Depends(get_security_auditor),
    current_user: User = Depends(get_current_user),
):
    """Retrieve recent structured security audit events."""
    return auditor.list_events(limit=limit, severity=severity)


@router.post("/inspect-prompt", response_model=PromptInspectionResult)
async def inspect_user_prompt(
    request: InspectPromptRequest,
    auditor: SecurityAuditor = Depends(get_security_auditor),
    current_user: User = Depends(get_current_user),
):
    """Pre-execution guardrail check to detect prompt injection, jailbreaks, and adversarial overrides."""
    return auditor.inspect_prompt(request.prompt)

