from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
KPI_SAMPLE_CSV = FIXTURES_DIR / "kpi_sample.csv"


def test_incidents_crud_api():
    # 1. Create incident
    payload = {
        "title": "Core Transmission Packet Loss",
        "description": "Transport latency spike affecting multiple sectors",
        "severity": "CRITICAL",
        "status": "OPEN",
        "affected_cells": ["CELL_001", "CELL_002"],
        "related_alarms": []
    }
    create_res = client.post("/api/v1/incidents", json=payload)
    assert create_res.status_code == 201
    incident_data = create_res.json()
    incident_id = incident_data["id"]
    assert incident_data["title"] == payload["title"]
    assert incident_data["status"] == "OPEN"

    # 2. Get incident by id
    get_res = client.get(f"/api/v1/incidents/{incident_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == incident_id

    # 3. List incidents
    list_res = client.get("/api/v1/incidents")
    assert list_res.status_code == 200
    assert any(i["id"] == incident_id for i in list_res.json())

    # 4. Resolve incident
    resolve_res = client.patch(
        f"/api/v1/incidents/{incident_id}/resolve",
        json={"resolution": "Bypassed faulty microwave link."}
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "RESOLVED"
    assert resolve_res.json()["resolution"] == "Bypassed faulty microwave link."


def test_cell_enhanced_rca_with_correlation():
    # 1. Ingest dataset
    with open(KPI_SAMPLE_CSV, "rb") as f:
        upload_res = client.post(
            "/api/v1/datasets/upload",
            files={"file": ("sample_rca.csv", f, "text/csv")},
        )
    assert upload_res.status_code == 201
    dataset = upload_res.json()
    assert len(dataset["cells"]) > 0
    test_cell = dataset["cells"][0]
    cell_id = test_cell["cell_id"]
    site_id = test_cell.get("site_id", "SITE_001")

    # 2. Inject an alarm matching this cell
    alarm_payload = {
        "alarm_type": "POOR_RADIO_QUALITY",
        "severity": "CRITICAL",
        "description": "Excessive interference and low SINR",
        "source": "OSS_FIELD",
        "cell_id": cell_id,
        "site_id": site_id,
    }
    alarm_res = client.post("/api/v1/alarms", json=alarm_payload)
    assert alarm_res.status_code == 201
    alarm_data = alarm_res.json()

    # 3. Query enhanced RCA
    rca_res = client.get(f"/api/v1/cells/{cell_id}/rca")
    assert rca_res.status_code == 200
    rca_data = rca_res.json()

    assert rca_data["cell_id"] == cell_id
    assert "correlated_alarms" in rca_data
    assert len(rca_data["correlated_alarms"]) >= 1
    assert rca_data["correlated_alarms"][0]["alarm_id"] == alarm_data["alarm_id"]
    assert "disclaimer" in rca_data
    assert "primary_hypothesis" in rca_data
    assert len(rca_data["recommended_actions"]) >= 1

