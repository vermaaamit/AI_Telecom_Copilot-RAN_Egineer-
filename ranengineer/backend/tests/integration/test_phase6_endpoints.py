"""Integration tests for Phase 6 Endpoints: Auth/RBAC, O-RAN rApp Studio, Shift Handover."""
import pytest
from starlette.testclient import TestClient

from app.main import app
from app.security.auth import create_access_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def engineer_token():
    return create_access_token({"sub": "engineer@telecom.ai", "role": "RAN_ENGINEER"})


@pytest.fixture
def viewer_token():
    return create_access_token({"sub": "viewer@telecom.ai", "role": "VIEWER"})


def test_auth_login_successful(client):
    res = client.post("/api/v1/auth/login", json={"email": "engineer@telecom.ai", "password": "telecom123!"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["role"] == "RAN_ENGINEER"


def test_auth_login_failure(client):
    res = client.post("/api/v1/auth/login", json={"email": "engineer@telecom.ai", "password": "wrong"})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_auth_me_profile(client, engineer_token):
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {engineer_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "engineer@telecom.ai"
    assert data["role"] == "RAN_ENGINEER"


def test_auth_users_list(client):
    res = client.get("/api/v1/auth/users")
    assert res.status_code == 200
    users = res.json()
    assert len(users) >= 3
    roles = [u["role"] for u in users]
    assert "ADMIN" in roles
    assert "RAN_ENGINEER" in roles
    assert "VIEWER" in roles


def test_oran_list_templates(client):
    res = client.get("/api/v1/oran/templates")
    assert res.status_code == 200
    templates = res.json()
    assert len(templates) >= 3
    names = [t["policy_type_name"] for t in templates]
    assert any("Traffic_Steering" in n for n in names)


def test_oran_list_rapps(client):
    res = client.get("/api/v1/oran/rapps")
    assert res.status_code == 200
    rapps = res.json()
    assert len(rapps) >= 3
    assert all("safety_notice" in r for r in rapps)


def test_oran_validate_parameters_endpoint(client):
    payload = {
        "rapp_name": "Test TS",
        "policy_type": "traffic_steering",
        "target_cells": ["CELL_A"],
        "parameters": {"prb_threshold_percent": 80.0, "rsrp_offset_db": -5.0},
    }
    res = client.post("/api/v1/oran/rapps/validate", json=payload)
    assert res.status_code == 200
    assert res.json()["is_valid"] is True


def test_oran_generate_and_approve_rapp(client, engineer_token, viewer_token):
    # 1. Generate with RAN_ENGINEER token
    gen_payload = {
        "rapp_name": "Integration Test Load Balancer",
        "policy_type": "traffic_steering",
        "target_cells": ["CELL_INT_1"],
        "target_site_id": "SITE_INT",
        "parameters": {"prb_threshold_percent": 75.0, "rsrp_offset_db": -4.0},
    }
    res = client.post(
        "/api/v1/oran/rapps/generate",
        json=gen_payload,
        headers={"Authorization": f"Bearer {engineer_token}"},
    )
    assert res.status_code == 201
    rapp = res.json()
    rapp_id = rapp["id"]
    assert rapp["review_status"] == "VALIDATED"

    # 2. Approve with VIEWER role should fail (403 Forbidden)
    res_deny = client.post(
        f"/api/v1/oran/rapps/{rapp_id}/approve",
        json={"notes": "Viewer attempting approval"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert res_deny.status_code == 403

    # 3. Approve with RAN_ENGINEER should succeed (200 OK)
    res_approve = client.post(
        f"/api/v1/oran/rapps/{rapp_id}/approve",
        json={"notes": "Approved in lab simulation"},
        headers={"Authorization": f"Bearer {engineer_token}"},
    )
    assert res_approve.status_code == 200
    assert res_approve.json()["review_status"] == "ENGINEER_APPROVED"
    assert res_approve.json()["approved_by"] == "engineer@telecom.ai"


def test_shift_handover_report_endpoint(client, engineer_token):
    res = client.get(
        "/api/v1/reports/handover",
        headers={"Authorization": f"Bearer {engineer_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "report_id" in data
    assert "system_status" in data
    assert "handover_action_items" in data
    assert "executive_summary" in data


def test_shift_handover_export_markdown(client, engineer_token):
    res = client.get(
        "/api/v1/reports/handover/export",
        headers={"Authorization": f"Bearer {engineer_token}"},
    )
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/markdown")
    assert "attachment; filename=shift_handover_" in res.headers["content-disposition"]
    assert "# NOC RAN Operational Shift Handover" in res.text

