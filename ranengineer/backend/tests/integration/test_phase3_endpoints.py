from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
KPI_SAMPLE_CSV = FIXTURES_DIR / "kpi_sample.csv"


def test_phase3_trends_and_predictive_api():
    # 1. Upload first dataset
    with open(KPI_SAMPLE_CSV, "rb") as f:
        res1 = client.post(
            "/api/v1/datasets/upload",
            files={"file": ("dataset_t1.csv", f, "text/csv")},
        )
    assert res1.status_code == 201
    d1 = res1.json()
    assert len(d1["cells"]) > 0
    test_cell_id = d1["cells"][0]["cell_id"]

    # 2. Upload second dataset for temporal continuity
    with open(KPI_SAMPLE_CSV, "rb") as f:
        res2 = client.post(
            "/api/v1/datasets/upload",
            files={"file": ("dataset_t2.csv", f, "text/csv")},
        )
    assert res2.status_code == 201

    # 3. Query historical trends endpoint
    trends_res = client.get(f"/api/v1/cells/{test_cell_id}/trends")
    assert trends_res.status_code == 200
    trends_data = trends_res.json()
    assert trends_data["cell_id"] == test_cell_id
    assert trends_data["data_points_count"] >= 2
    assert "trends" in trends_data
    assert "overall_health_trend" in trends_data

    # 4. Query predictive anomalies endpoint
    pred_res = client.get("/api/v1/anomalies/predictive")
    assert pred_res.status_code == 200
    pred_data = pred_res.json()
    assert "total_evaluated_cells" in pred_data
    assert "at_risk_cells_count" in pred_data
    assert "items" in pred_data
    assert "methodology" in pred_data

