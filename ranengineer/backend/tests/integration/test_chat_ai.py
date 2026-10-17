from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_CSV = b"""cell_id,site_id,technology,RSRP,SINR,DL_Throughput,PRB_Utilization,Call_Drop_Rate,Availability
CELL_A1,SITE_ALPHA,4G,-118,2,2.0,97.0,3.5,96.0
CELL_A2,SITE_ALPHA,4G,-88,20,50.0,40.0,0.2,99.8
CELL_B1,SITE_BETA,5G,-104,6,8.0,88.0,1.2,98.2
"""


def setup_test_dataset() -> str:
    res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("chat_ai_test.csv", SAMPLE_CSV, "text/csv")},
    )
    assert res.status_code == 201
    return res.json()["id"]


def test_chat_underperforming_cells_question() -> None:
    ds_id = setup_test_dataset()
    res = client.post("/api/v1/chat", json={"dataset_id": ds_id, "question": "Which cells are performing badly?"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "find_bad_cells"
    assert "CELL_A1" in data["answer"]
    assert "Probable Causes:" in data["answer"]
    assert "Recommended Checks:" in data["answer"]
    assert data["guardrail_report"]["is_grounded"] is True


def test_chat_single_cell_investigation() -> None:
    ds_id = setup_test_dataset()
    res = client.post("/api/v1/chat", json={"dataset_id": ds_id, "question": "Why is CELL_A1 performing badly?"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "cell_analysis"
    assert "CELL_A1" in data["answer"]
    assert "Limitations:" in data["answer"]


def test_chat_cell_comparison() -> None:
    ds_id = setup_test_dataset()
    res = client.post("/api/v1/chat", json={"dataset_id": ds_id, "question": "Compare CELL_A1 and CELL_A2."})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "compare_cells"
    assert "CELL_A2" in data["answer"]


def test_chat_kpi_filter_question() -> None:
    ds_id = setup_test_dataset()
    res = client.post("/api/v1/chat", json={"dataset_id": ds_id, "question": "Which cells have SINR below 5?"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "filter_cells_by_kpi"
    assert "CELL_A1" in data["answer"]


def test_chat_site_congested_question() -> None:
    ds_id = setup_test_dataset()
    res = client.post("/api/v1/chat", json={"dataset_id": ds_id, "question": "Which sites are congested?"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "compare_sites"
    assert "SITE_ALPHA" in data["answer"] or "SITE_BETA" in data["answer"]

