"""O-RAN Non-RT RIC A1 Policy Generator and Guardrail Validator (O-RAN WG2 compliant)."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from app.oran.models import (
    A1PolicySchema,
    PolicyType,
    RAppDescriptor,
    RAppGenerationRequest,
    RAppValidationResult,
    ReviewStatus,
)

# Standard A1 Policy Type schemas based on O-RAN WG2 A1AP specification
STANDARD_A1_SCHEMAS: Dict[PolicyType, A1PolicySchema] = {
    PolicyType.TRAFFIC_STEERING: A1PolicySchema(
        policy_type_id=20000,
        policy_type_name="Traffic_Steering_Preference",
        description="A1-P declarative policy to steer UE traffic between macro/small cells or 4G/5G layers under high PRB utilization.",
        standard_reference="O-RAN.WG2.A1AP-v03.01 / WG2.TS-01",
        json_schema={
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "TrafficSteeringPolicy",
            "type": "object",
            "properties": {
                "prb_threshold_percent": {
                    "type": "number",
                    "minimum": 50.0,
                    "maximum": 98.0,
                    "description": "PRB utilization trigger for traffic offload",
                },
                "rsrp_offset_db": {
                    "type": "number",
                    "minimum": -12.0,
                    "maximum": 12.0,
                    "description": "Offset applied to candidate cell RSRP for A3/A4 event steering",
                },
                "hysteresis_db": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 10.0,
                    "description": "Hysteresis margin to prevent ping-pong handovers",
                },
                "time_to_trigger_ms": {
                    "type": "integer",
                    "minimum": 40,
                    "maximum": 1280,
                    "description": "Evaluation interval before triggering mobility",
                },
            },
            "required": ["prb_threshold_percent", "rsrp_offset_db"],
        },
        default_parameters={
            "prb_threshold_percent": 80.0,
            "rsrp_offset_db": -6.0,
            "hysteresis_db": 2.0,
            "time_to_trigger_ms": 320,
        },
    ),
    PolicyType.ENERGY_SAVING: A1PolicySchema(
        policy_type_id=20001,
        policy_type_name="RAN_Energy_Saving_Orchestration",
        description="A1-P declarative policy for dynamic carrier sleep during off-peak hours with underlay coverage protection.",
        standard_reference="O-RAN.WG2.A1AP-v03.01 / WG2.ES-01",
        json_schema={
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "EnergySavingPolicy",
            "type": "object",
            "properties": {
                "offpeak_prb_threshold": {
                    "type": "number",
                    "minimum": 5.0,
                    "maximum": 35.0,
                    "description": "PRB utilization threshold below which cell sleep can activate",
                },
                "reactivation_prb_threshold": {
                    "type": "number",
                    "minimum": 40.0,
                    "maximum": 85.0,
                    "description": "Surrounding layer PRB threshold to trigger rapid wake-up",
                },
                "coverage_underlay_cell_id": {
                    "type": "string",
                    "description": "Mandatory co-located underlay cell ID ensuring coverage continuity",
                },
                "sleep_depth": {
                    "type": "string",
                    "enum": ["micro_sleep", "carrier_shutdown", "deep_mimo_sleep"],
                    "description": "Hardware sleep profile depth",
                },
            },
            "required": ["offpeak_prb_threshold", "reactivation_prb_threshold", "coverage_underlay_cell_id"],
        },
        default_parameters={
            "offpeak_prb_threshold": 15.0,
            "reactivation_prb_threshold": 55.0,
            "coverage_underlay_cell_id": "CELL_UNDERLAY_DEFAULT",
            "sleep_depth": "carrier_shutdown",
        },
    ),
    PolicyType.QOE_ASSURANCE: A1PolicySchema(
        policy_type_id=20002,
        policy_type_name="QoE_Assurance_Slice_SLA",
        description="A1-P declarative policy enforcing latency and throughput SLAs across prioritized network slices.",
        standard_reference="O-RAN.WG2.A1AP-v03.01 / 3GPP TS 23.501",
        json_schema={
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "QoEAssurancePolicy",
            "type": "object",
            "properties": {
                "slice_id": {
                    "type": "string",
                    "description": "S-NSSAI slice identifier (e.g. SST-1_SD-000001)",
                },
                "min_throughput_dl_mbps": {
                    "type": "number",
                    "minimum": 1.0,
                    "maximum": 1000.0,
                    "description": "Guaranteed minimum downlink throughput",
                },
                "max_packet_delay_budget_ms": {
                    "type": "number",
                    "minimum": 5.0,
                    "maximum": 300.0,
                    "description": "Maximum tolerated packet delay budget",
                },
                "priority_level": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 8,
                    "description": "Scheduling priority weight",
                },
            },
            "required": ["slice_id", "min_throughput_dl_mbps", "max_packet_delay_budget_ms"],
        },
        default_parameters={
            "slice_id": "SST-1_SD-URLLC01",
            "min_throughput_dl_mbps": 50.0,
            "max_packet_delay_budget_ms": 20.0,
            "priority_level": 1,
        },
    ),
}


class RAppStudio:
    """O-RAN Non-RT RIC rApp design studio, policy synthesizer, and validator."""

    def __init__(self):
        self.schemas = STANDARD_A1_SCHEMAS

    def list_templates(self) -> List[A1PolicySchema]:
        """Returns standard O-RAN WG2 A1-P policy schemas."""
        return list(self.schemas.values())

    def get_template(self, policy_type: PolicyType) -> A1PolicySchema:
        """Retrieves template by policy type."""
        return self.schemas[policy_type]

    def validate_parameters(
        self, policy_type: PolicyType, params: Dict[str, Any]
    ) -> RAppValidationResult:
        """Enforces schema boundaries and telecom safety guardrails."""
        schema = self.schemas.get(policy_type)
        if not schema:
            return RAppValidationResult(
                is_valid=False,
                schema_check=False,
                kpi_bounds_check=False,
                guardrail_check=False,
                errors=[f"Unsupported policy type: {policy_type}"],
            )

        errors: List[str] = []
        warnings: List[str] = []

        if policy_type == PolicyType.TRAFFIC_STEERING:
            prb_thresh = params.get("prb_threshold_percent")
            if prb_thresh is None:
                errors.append("Missing required parameter: 'prb_threshold_percent'")
            elif not (50.0 <= float(prb_thresh) <= 98.0):
                errors.append(f"prb_threshold_percent ({prb_thresh}) out of bounds [50.0, 98.0]")

            rsrp_offset = params.get("rsrp_offset_db")
            if rsrp_offset is None:
                errors.append("Missing required parameter: 'rsrp_offset_db'")
            elif not (-12.0 <= float(rsrp_offset) <= 12.0):
                errors.append(f"rsrp_offset_db ({rsrp_offset}) out of bounds [-12.0, +12.0] dB")

            hyst = params.get("hysteresis_db", 2.0)
            if float(hyst) < 1.0:
                warnings.append("Hysteresis < 1.0 dB risks rapid ping-pong handover cycles.")

        elif policy_type == PolicyType.ENERGY_SAVING:
            offpeak_prb = params.get("offpeak_prb_threshold")
            react_prb = params.get("reactivation_prb_threshold")
            underlay_cell = params.get("coverage_underlay_cell_id")

            if offpeak_prb is None:
                errors.append("Missing required parameter: 'offpeak_prb_threshold'")
            elif not (5.0 <= float(offpeak_prb) <= 35.0):
                errors.append(f"offpeak_prb_threshold ({offpeak_prb}) out of bounds [5.0, 35.0]")

            if react_prb is None:
                errors.append("Missing required parameter: 'reactivation_prb_threshold'")
            elif not (40.0 <= float(react_prb) <= 85.0):
                errors.append(f"reactivation_prb_threshold ({react_prb}) out of bounds [40.0, 85.0]")

            if offpeak_prb is not None and react_prb is not None:
                if float(react_prb) <= float(offpeak_prb) + 15.0:
                    warnings.append(
                        f"Reactivation threshold ({react_prb}%) should be at least 15% above offpeak threshold ({offpeak_prb}%) to avoid oscillation."
                    )

            if not underlay_cell or not str(underlay_cell).strip():
                errors.append(
                    "GUARDRAIL VIOLATION: 'coverage_underlay_cell_id' is mandatory. Sleeping a cell without underlay coverage creates immediate network outages."
                )

        elif policy_type == PolicyType.QOE_ASSURANCE:
            slice_id = params.get("slice_id")
            min_dl = params.get("min_throughput_dl_mbps")
            max_delay = params.get("max_packet_delay_budget_ms")

            if not slice_id or not str(slice_id).strip():
                errors.append("Missing required parameter: 'slice_id'")
            if min_dl is None or float(min_dl) <= 0.0:
                errors.append("min_throughput_dl_mbps must be greater than 0 Mbps")
            if max_delay is None or not (5.0 <= float(max_delay) <= 300.0):
                errors.append("max_packet_delay_budget_ms out of bounds [5.0, 300.0] ms")

        is_valid = len(errors) == 0
        return RAppValidationResult(
            is_valid=is_valid,
            schema_check=is_valid,
            kpi_bounds_check=is_valid,
            guardrail_check=is_valid,
            warnings=warnings,
            errors=errors,
        )

    def generate_rapp(self, req: RAppGenerationRequest) -> RAppDescriptor:
        """Synthesizes a declarative O-RAN rApp package with strict validation."""
        schema = self.get_template(req.policy_type)
        merged_params = schema.default_parameters.copy()
        merged_params.update(req.parameters)

        validation = self.validate_parameters(req.policy_type, merged_params)

        # Assemble A1-P Policy Payload matching O-RAN WG2 Non-RT RIC specifications
        a1_policy_payload = {
            "policy_type_id": schema.policy_type_id,
            "policy_type_name": schema.policy_type_name,
            "standard_specification": schema.standard_reference,
            "scope": {
                "target_cells": req.target_cells,
                "target_site_id": req.target_site_id,
            },
            "statements": merged_params,
            "enforcement_mode": "MONITORED_CLOSED_LOOP",
        }

        # Determine data telemetry requirements for Non-RT RIC analytics
        data_requirements = [
            "3GPP TS 28.552 Cell-level Performance Measurements (PRB, DL/UL Throughput)",
            "O-RAN E2PM KPM Service Model telemetry (Reporting Period: 1000ms)",
            "O-RAN A1-P Policy Feedback Stream (A1-Status, A1-Enforcement-Report)",
        ]
        if req.policy_type == PolicyType.ENERGY_SAVING:
            data_requirements.append("Cell Power Consumption & Active PA State Telemetry")
        elif req.policy_type == PolicyType.QOE_ASSURANCE:
            data_requirements.append("5QI / S-NSSAI Packet Delay Budget & Loss Rate Counters")

        review_status = ReviewStatus.VALIDATED if validation.is_valid else ReviewStatus.DRAFT

        now_iso = datetime.now(timezone.utc).isoformat()
        return RAppDescriptor(
            id=f"rapp-{uuid.uuid4().hex[:8]}",
            name=req.rapp_name,
            version="1.0.0",
            vendor="AI-Telecom-Copilot-RAN-WG2",
            policy_type=req.policy_type,
            review_status=review_status,
            target_cells=req.target_cells,
            target_site_id=req.target_site_id,
            objective=req.objective,
            a1_policy_payload=a1_policy_payload,
            data_requirements=data_requirements,
            guardrail_validation=validation,
            engineer_notes=req.notes,
            approved_by=None,
            approved_at=None,
            created_at=now_iso,
            updated_at=now_iso,
        )

