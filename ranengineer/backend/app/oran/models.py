"""O-RAN Non-RT RIC rApp Models and Schemas (O-RAN WG2 / A1-P compliant)."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field


class PolicyType(str, Enum):
    TRAFFIC_STEERING = "traffic_steering"
    ENERGY_SAVING = "energy_saving"
    QOE_ASSURANCE = "qoe_assurance"


class ReviewStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    SIMULATION_TESTED = "SIMULATION_TESTED"
    ENGINEER_APPROVED = "ENGINEER_APPROVED"
    REJECTED = "REJECTED"


class A1PolicySchema(BaseModel):
    policy_type_id: int
    policy_type_name: str
    description: str
    standard_reference: str = "O-RAN.WG2.A1AP-v03.01"
    json_schema: Dict[str, Any]
    default_parameters: Dict[str, Any]


class RAppValidationResult(BaseModel):
    is_valid: bool = True
    schema_check: bool = True
    kpi_bounds_check: bool = True
    guardrail_check: bool = True
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class RAppGenerationRequest(BaseModel):
    rapp_name: str
    policy_type: PolicyType
    target_cells: List[str] = Field(..., min_length=1)
    target_site_id: Optional[str] = None
    objective: str = "Optimize cell performance using deterministic A1 policies"
    parameters: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class RAppDescriptor(BaseModel):
    id: str = Field(default_factory=lambda: f"rapp-{uuid.uuid4().hex[:8]}")
    name: str
    version: str = "1.0.0"
    vendor: str = "AI-Telecom-Copilot-RAN-WG2"
    policy_type: PolicyType
    review_status: ReviewStatus = ReviewStatus.DRAFT
    target_cells: List[str]
    target_site_id: Optional[str] = None
    objective: str
    a1_policy_payload: Dict[str, Any]
    data_requirements: List[str]
    guardrail_validation: RAppValidationResult
    engineer_notes: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    safety_notice: str = (
        "MANDATORY GUARDRAIL: Deployment to live O-RAN Non-RT RIC / Near-RT RIC "
        "requires formal RAN Engineer sign-off and lab validation. "
        "Unreviewed automated deployment is strictly prohibited."
    )


class ApprovalRequest(BaseModel):
    notes: Optional[str] = "Approved following lab simulation and KPI boundary check."

