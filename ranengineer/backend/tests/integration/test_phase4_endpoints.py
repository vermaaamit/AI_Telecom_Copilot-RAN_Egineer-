from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
KPI_SAMPLE_CSV = FIXTURES_DIR / "kpi_sample.csv"


def test_knowledge_search_api():
    # 1. Search with valid term
    res = client.get("/api/v1/knowledge/search?q=interference&limit=2")
    assert res.status_code == 200
    data = res.json()
    assert data["query"] == "interference"
    assert data["total_matched"] >= 1
    assert len(data["documents"]) <= 2
    assert "disclaimer" in data

    # 2. Search validation min length
    bad_res = client.get("/api/v1/knowledge/search?q=a")
    assert bad_res.status_code == 422


def test_multi_agent_investigate_api():
    # 1. Upload dataset
    with open(KPI_SAMPLE_CSV, "rb") as f:
        res = client.post(
            "/api/v1/datasets/upload",
            files={"file": ("dataset_agent.csv", f, "text/csv")},
        )
    assert res.status_code == 201
    d = res.json()
    cell_id = d["cells"][0]["cell_id"]

    # 2. Request multi-agent investigation
    inv_res = client.post("/api/v1/agents/investigate", json={"cell_id": cell_id})
    assert inv_res.status_code == 200
    inv_data = inv_res.json()
    assert inv_data["target_cell_id"] == cell_id
    assert inv_data["investigation_id"].startswith("INV-")
    assert len(inv_data["agent_contributions"]) >= 4
    assert "overall_verdict" in inv_data
    assert "engineer_disclaimer" in inv_data

    # 3. 404 for unknown cell
    not_found = client.post("/api/v1/agents/investigate", json={"cell_id": "UNKNOWN_999"})
    assert not_found.status_code == 404

