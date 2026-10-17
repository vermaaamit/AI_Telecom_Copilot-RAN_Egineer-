"""Unit tests for O-RAN Non-RT RIC rApp Studio and Guardrails."""
import pytest

from app.oran.generator import RAppStudio, STANDARD_A1_SCHEMAS
from app.oran.models import (
    ApprovalRequest,
    PolicyType,
    RAppGenerationRequest,
    ReviewStatus,
)
from app.oran.store import RAppStore


def test_standard_a1_schemas_exist():
    studio = RAppStudio()
    templates = studio.list_templates()
    assert len(templates) >= 3

    policy_types = [t.policy_type_id for t in templates]
    assert 20000 in policy_types  # Traffic Steering
    assert 20001 in policy_types  # Energy Saving
    assert 20002 in policy_types  # QoE Assurance


def test_traffic_steering_validation_success():
    studio = RAppStudio()
    valid_params = {
        "prb_threshold_percent": 85.0,
        "rsrp_offset_db": -4.0,
        "hysteresis_db": 2.0,
        "time_to_trigger_ms": 320,
    }
    result = studio.validate_parameters(PolicyType.TRAFFIC_STEERING, valid_params)
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_traffic_steering_bounds_violation():
    studio = RAppStudio()
    # PRB > 98% is physically unsafe
    invalid_params = {
        "prb_threshold_percent": 115.0,
        "rsrp_offset_db": -4.0,
    }
    result = studio.validate_parameters(PolicyType.TRAFFIC_STEERING, invalid_params)
    assert result.is_valid is False
    assert any("prb_threshold_percent" in e for e in result.errors)


def test_energy_saving_guardrail_requires_underlay_cell():
    studio = RAppStudio()
    # Missing coverage_underlay_cell_id is a safety violation
    unsafe_params = {
        "offpeak_prb_threshold": 15.0,
        "reactivation_prb_threshold": 55.0,
        "coverage_underlay_cell_id": "",
    }
    result = studio.validate_parameters(PolicyType.ENERGY_SAVING, unsafe_params)
    assert result.is_valid is False
    assert any("GUARDRAIL VIOLATION" in e for e in result.errors)


def test_rapp_package_synthesis():
    studio = RAppStudio()
    req = RAppGenerationRequest(
        rapp_name="Downtown Macro Load Balancer",
        policy_type=PolicyType.TRAFFIC_STEERING,
        target_cells=["CELL_101", "CELL_102"],
        target_site_id="SITE_DOWNTOWN",
        parameters={"prb_threshold_percent": 78.0, "rsrp_offset_db": -5.0},
    )
    rapp = studio.generate_rapp(req)
    assert rapp.id.startswith("rapp-")
    assert rapp.name == "Downtown Macro Load Balancer"
    assert rapp.review_status == ReviewStatus.VALIDATED
    assert "target_cells" in rapp.a1_policy_payload["scope"]
    assert len(rapp.data_requirements) >= 3
    assert "MANDATORY GUARDRAIL" in rapp.safety_notice


def test_rapp_store_lifecycle_and_approval():
    store = RAppStore()
    initial_count = len(store.list_all())
    assert initial_count >= 3

    # Create new rApp
    req = RAppGenerationRequest(
        rapp_name="Suburban Energy Saver",
        policy_type=PolicyType.ENERGY_SAVING,
        target_cells=["CELL_SUB_01"],
        parameters={
            "offpeak_prb_threshold": 10.0,
            "reactivation_prb_threshold": 50.0,
            "coverage_underlay_cell_id": "CELL_SUB_ANCHOR",
        },
    )
    rapp = store.studio.generate_rapp(req)
    store.save(rapp)

    assert len(store.list_all()) == initial_count + 1
    assert store.get_by_id(rapp.id) is not None

    # Approve
    approved = store.approve(
        rapp.id,
        "engineer@telecom.ai",
        ApprovalRequest(notes="Lab test passed with 0 dropped calls."),
    )
    assert approved is not None
    assert approved.review_status == ReviewStatus.ENGINEER_APPROVED
    assert approved.approved_by == "engineer@telecom.ai"
    assert "Lab test passed" in approved.engineer_notes

