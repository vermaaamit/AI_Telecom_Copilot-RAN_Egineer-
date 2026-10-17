import io
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_CSV = b"""cell_id,site_id,technology,RSRP,SINR,DL_Throughput,PRB_Utilization,Call_Drop_Rate,Availability
CELL_T101,SITE_T1,4G,-118 dBm,2 dB,1.5 Mbps,95 %,3.5 %,96.0 %
CELL_T102,SITE_T1,4G,-85 dBm,22 dB,55 Mbps,35 %,0.1 %,99.9 %
CELL_T103,SITE_T2,5G,-102 dBm,6 dB,8 Mbps,85 %,0.8 %,98.5 %
"""


def test_health_check() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_kpi_definitions_endpoint() -> None:
    response = client.get("/api/v1/kpis")
    assert response.status_code == 200
    assert "rsrp" in response.json()["items"]


def test_upload_invalid_file_extension() -> None:
    response = client.post("/api/v1/datasets/upload", files={"file": ("test.txt", b"hello", "text/plain")})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_KPI_FILE"


def test_upload_empty_csv() -> None:
    response = client.post("/api/v1/datasets/upload", files={"file": ("empty.csv", b"", "text/csv")})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_KPI_FILE"


def test_full_dataset_workflow() -> None:
    # 1. Upload valid CSV
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("integration_test.csv", SAMPLE_CSV, "text/csv")},
        data={"technology": "4G/5G"}
    )
    assert upload_res.status_code == 201
    dataset = upload_res.json()
    dataset_id = dataset["id"]
    assert dataset["cell_count"] == 3
    assert "rsrp" in dataset["available_kpis"]

    # 2. List datasets
    list_res = client.get("/api/v1/datasets")
    assert list_res.status_code == 200
    assert any(d["id"] == dataset_id for d in list_res.json())

    # 3. Get dataset detail
    get_res = client.get(f"/api/v1/datasets/{dataset_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == dataset_id

    # 4. Get dataset summary
    summary_res = client.get(f"/api/v1/datasets/{dataset_id}/summary")
    assert summary_res.status_code == 200
    assert summary_res.json()["summary"]["total_cells"] == 3

    # 5. List cells
    cells_res = client.get(f"/api/v1/datasets/{dataset_id}/cells?limit=10")
    assert cells_res.status_code == 200
    assert len(cells_res.json()["items"]) == 3

    # 6. Bad cells
    bad_res = client.get(f"/api/v1/datasets/{dataset_id}/bad-cells?limit=2")
    assert bad_res.status_code == 200
    items = bad_res.json()["items"]
    assert len(items) == 2
    assert items[0]["cell_id"] == "CELL_T101"
    assert items[0]["status"] == "CRITICAL"

    # 7. Dataset anomalies
    anomalies_res = client.get(f"/api/v1/datasets/{dataset_id}/anomalies")
    assert anomalies_res.status_code == 200
    assert len(anomalies_res.json()["items"]) >= 1

    # 8. Global anomalies
    global_anom_res = client.get(f"/api/v1/anomalies?dataset_id={dataset_id}")
    assert global_anom_res.status_code == 200
    assert len(global_anom_res.json()["items"]) >= 1

    # 9. Cell detail
    cell_res = client.get("/api/v1/cells/CELL_T101")
    assert cell_res.status_code == 200
    assert cell_res.json()["cell_id"] == "CELL_T101"

    # 10. Cell analysis
    analysis_res = client.get("/api/v1/cells/CELL_T101/analysis")
    assert analysis_res.status_code == 200
    analysis = analysis_res.json()
    assert analysis["cell_id"] == "CELL_T101"
    assert "summary" in analysis
    assert len(analysis["recommended_checks"]) > 0

    # 11. Chat queries
    chat_worst = client.post("/api/v1/chat", json={"dataset_id": dataset_id, "question": "Which cells are performing badly?"})
    assert chat_worst.status_code == 200
    assert "CELL_T101" in chat_worst.json()["answer"]

    chat_summary = client.post("/api/v1/chat", json={"dataset_id": dataset_id, "question": "Give me a KPI summary."})
    assert chat_summary.status_code == 200
    assert "3 cells" in chat_summary.json()["answer"]


    chat_cell = client.post("/api/v1/chat", json={"dataset_id": dataset_id, "question": "Why is CELL_T101 performing badly?"})
    assert chat_cell.status_code == 200
    assert "CELL_T101" in chat_cell.json()["answer"]

    # 12. 404 error responses
    not_found_ds = client.get("/api/v1/datasets/non-existent-uuid")
    assert not_found_ds.status_code == 404
    assert not_found_ds.json()["error"]["code"] == "DATASET_NOT_FOUND"

    not_found_cell = client.get("/api/v1/cells/NON_EXISTENT_CELL")
    assert not_found_cell.status_code == 404
    assert not_found_cell.json()["error"]["code"] == "CELL_NOT_FOUND"

