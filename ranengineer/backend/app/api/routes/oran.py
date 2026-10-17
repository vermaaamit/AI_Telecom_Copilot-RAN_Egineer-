"""O-RAN Non-RT RIC rApp Studio API routes."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.oran.generator import RAppStudio
from app.oran.models import (
    A1PolicySchema,
    ApprovalRequest,
    PolicyType,
    RAppDescriptor,
    RAppGenerationRequest,
    RAppValidationResult,
)
from app.oran.store import RAppStore, get_rapp_store
from app.security.auth import User, UserRole, get_current_user, require_role

router = APIRouter(prefix="/oran", tags=["O-RAN Non-RT RIC rApp Studio"])


@router.get("/templates", response_model=List[A1PolicySchema])
async def list_a1_policy_templates():
    """List standard O-RAN WG2 A1-P policy schemas (Traffic Steering, Energy Saving, QoE Assurance)."""
    studio = RAppStudio()
    return studio.list_templates()


@router.get("/rapps", response_model=List[RAppDescriptor])
async def list_rapps(
    policy_type: Optional[PolicyType] = Query(None, description="Filter by policy type"),
    store: RAppStore = Depends(get_rapp_store),
):
    """List all synthesized O-RAN rApp packages."""
    return store.list_all(policy_type=policy_type)


@router.get("/rapps/{rapp_id}", response_model=RAppDescriptor)
async def get_rapp(
    rapp_id: str,
    store: RAppStore = Depends(get_rapp_store),
):
    """Retrieve an O-RAN rApp package descriptor by ID."""
    rapp = store.get_by_id(rapp_id)
    if not rapp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "RAPP_NOT_FOUND", "message": f"rApp with ID '{rapp_id}' not found.", "details": []}},
        )
    return rapp


@router.post("/rapps/generate", response_model=RAppDescriptor, status_code=status.HTTP_201_CREATED)
async def generate_rapp_package(
    request: RAppGenerationRequest,
    current_user: User = Depends(require_role(UserRole.RAN_ENGINEER, UserRole.ADMIN)),
    store: RAppStore = Depends(get_rapp_store),
):
    """Generate and validate an O-RAN Non-RT RIC declarative rApp package.

    Enforces mandatory guardrails:
    - Physical and telecom KPI parameter boundaries
    - Underlay coverage guarantees for energy saving
    - No direct production deployment without engineer review
    """
    studio = RAppStudio()
    rapp = studio.generate_rapp(request)
    store.save(rapp)
    return rapp


@router.post("/rapps/{rapp_id}/approve", response_model=RAppDescriptor)
async def approve_rapp_package(
    rapp_id: str,
    approval_data: ApprovalRequest,
    current_user: User = Depends(require_role(UserRole.RAN_ENGINEER, UserRole.ADMIN)),
    store: RAppStore = Depends(get_rapp_store),
):
    """Record formal RAN Engineer approval and sign-off for an rApp package."""
    updated = store.approve(rapp_id, current_user.email, approval_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "RAPP_NOT_FOUND", "message": f"rApp with ID '{rapp_id}' not found.", "details": []}},
        )
    return updated


@router.post("/rapps/validate", response_model=RAppValidationResult)
async def validate_rapp_parameters(
    request: RAppGenerationRequest,
):
    """Validate candidate rApp parameters against O-RAN WG2 schemas and guardrails."""
    studio = RAppStudio()
    schema = studio.get_template(request.policy_type)
    merged_params = schema.default_parameters.copy()
    merged_params.update(request.parameters)
    return studio.validate_parameters(request.policy_type, merged_params)

