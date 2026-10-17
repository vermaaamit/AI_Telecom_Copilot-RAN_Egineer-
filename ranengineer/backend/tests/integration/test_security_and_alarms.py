"""Integration tests for suspicious file upload security flow and alarm API."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Content that triggers the MockScanner's malware detection
MALWARE_CSV = b"__MALWARE_TEST__,this,file,is,suspicious\ncell_id,rsrp\nCELL01,-85\n"

VALID_CSV = b"cell_id,site_id,RSRP,SINR,DL_Throughput,PRB_Utilization,Call_Drop_Rate,Availability\nCELL_SEC_01,SITE_S1,-85,18,45,42,0.1,99.8\n"


def test_suspicious_file_upload_is_blocked() -> None:
    """Suspicious file must be blocked and NOT reach CSV parsing or analytics."""
    response = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("malware_test.csv", MALWARE_CSV, "text/csv")},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "SUSPICIOUS_FILE_UPLOAD"
    assert "blocked" in body["error"]["message"].lower()


def test_suspicious_upload_raises_security_alarm() -> None:
    """After a suspicious upload, the alarms API should show a SUSPICIOUS_FILE_UPLOAD alarm."""
    # Trigger the suspicious upload
    client.post(
        "/api/v1/datasets/upload",
        files={"file": ("malware_test_alarm.csv", MALWARE_CSV, "text/csv")},
    )
    # Check alarms endpoint
    alarms_res = client.get("/api/v1/alarms")
    assert alarms_res.status_code == 200
    alarms = alarms_res.json()
    security_alarms = [a for a in alarms if a["alarm_type"] == "SUSPICIOUS_FILE_UPLOAD"]
    assert len(security_alarms) >= 1
    alarm = security_alarms[-1]
    assert alarm["severity"] == "CRITICAL"
    assert alarm["status"] == "ACTIVE"
    assert alarm["metadata"]["action"] == "BLOCKED"


def test_suspicious_upload_does_not_create_dataset() -> None:
    """Suspicious files must NOT be processed into a dataset."""
    before = client.get("/api/v1/datasets").json()
    count_before = len(before)

    client.post(
        "/api/v1/datasets/upload",
        files={"file": ("malware_nodataset.csv", MALWARE_CSV, "text/csv")},
    )

    after = client.get("/api/v1/datasets").json()
    # Dataset count must not increase
    assert len(after) == count_before


def test_alarm_api_list_active() -> None:
    """Active alarms endpoint returns only ACTIVE alarms."""
    active_res = client.get("/api/v1/alarms/active")
    assert active_res.status_code == 200
    for alarm in active_res.json():
        assert alarm["status"] == "ACTIVE"


def test_alarm_api_list_critical() -> None:
    """Critical alarms endpoint returns only CRITICAL severity alarms."""
    critical_res = client.get("/api/v1/alarms/critical")
    assert critical_res.status_code == 200
    for alarm in critical_res.json():
        assert alarm["severity"] == "CRITICAL"


def test_alarm_api_create_and_get() -> None:
    """Can create a synthetic alarm and retrieve it by ID."""
    payload = {
        "alarm_type": "HIGH_PRB_UTILIZATION",
        "severity": "CRITICAL",
        "description": "PRB utilization exceeded 90%",
        "source": "INTEGRATION_TEST",
        "site_id": "SITE_TEST",
        "cell_id": "CELL_TEST",
        "synthetic": True,
    }
    create_res = client.post("/api/v1/alarms", json=payload)
    assert create_res.status_code == 201
    alarm = create_res.json()
    alarm_id = alarm["alarm_id"]
    assert alarm_id.startswith("ALM-")

    get_res = client.get(f"/api/v1/alarms/{alarm_id}")
    assert get_res.status_code == 200
    assert get_res.json()["alarm_id"] == alarm_id


def test_alarm_api_acknowledge() -> None:
    """Can acknowledge an alarm."""
    create_res = client.post("/api/v1/alarms", json={
        "alarm_type": "LOW_THROUGHPUT",
        "severity": "MAJOR",
        "description": "Low DL throughput",
        "source": "INTEGRATION_TEST",
    })
    alarm_id = create_res.json()["alarm_id"]

    ack_res = client.patch(f"/api/v1/alarms/{alarm_id}/acknowledge")
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "ACKNOWLEDGED"


def test_alarm_api_not_found() -> None:
    """Non-existent alarm returns 404 with structured error."""
    res = client.get("/api/v1/alarms/ALM-DOES-NOT-EXIST")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "ALARM_NOT_FOUND"


def test_site_aggregation_endpoint() -> None:
    """Upload CSV and verify the /sites endpoint returns correct aggregations."""
    csv_data = (
        b"cell_id,site_id,RSRP,SINR,DL_Throughput,PRB_Utilization,Call_Drop_Rate,Availability\n"
        b"CELL_S1,SITE_AGG,-116,3,2,97,3.1,97.4\n"
        b"CELL_S2,SITE_AGG,-85,18,45,43,0.1,99.8\n"
        b"CELL_S3,SITE_OTHER,-90,12,30,60,0.5,99.0\n"
    )
    upload = client.post("/api/v1/datasets/upload", files={"file": ("site_test.csv", csv_data, "text/csv")})
    assert upload.status_code == 201
    dataset_id = upload.json()["id"]

    sites_res = client.get(f"/api/v1/datasets/{dataset_id}/sites")
    assert sites_res.status_code == 200
    sites = sites_res.json()["sites"]
    assert len(sites) == 2
    site_agg = next(s for s in sites if s["site_id"] == "SITE_AGG")
    assert site_agg["total_cells"] == 2


def test_kpi_degradation_in_cell_response() -> None:
    """Upload CSV and verify kpi_degradation is present in cell data."""
    csv_data = (
        b"cell_id,site_id,RSRP,SINR,DL_Throughput,PRB_Utilization,Call_Drop_Rate,Availability\n"
        b"CELL_DEG_01,SITE_D,-116,3,2,97,3.1,97.4\n"
    )
    upload = client.post("/api/v1/datasets/upload", files={"file": ("degradation_test.csv", csv_data, "text/csv")})
    assert upload.status_code == 201
    dataset_id = upload.json()["id"]

    cells_res = client.get(f"/api/v1/datasets/{dataset_id}/cells")
    assert cells_res.status_code == 200
    cell = cells_res.json()["items"][0]
    assert "kpi_degradation" in cell
    assert len(cell["kpi_degradation"]) > 0
    # Each degradation entry must have required fields
    entry = cell["kpi_degradation"][0]
    assert "kpi" in entry
    assert "current_value" in entry
    assert "status" in entry
    assert "degradation" in entry
    assert "severity" in entry

