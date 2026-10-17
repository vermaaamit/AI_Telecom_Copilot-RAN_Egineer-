from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SCENARIOS_DIR = Path(__file__).resolve().parents[3] / "data" / "scenarios"
if not SCENARIOS_DIR.exists():
    SCENARIOS_DIR = Path("/app/../data/scenarios")


def test_diagnostics_endpoint():
    res = client.get("/api/v1/diagnostics")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("OPERATIONAL", "DEGRADED")
    assert data["database"]["status"] == "HEALTHY"
    assert data["cache"]["status"] == "HEALTHY"
    assert data["security"]["scanner"] is not None
    assert data["analytics"]["ran_rules_loaded"] > 0
    assert data["analytics"]["rag_standards_loaded"] > 0


def test_scenario_1_interference():
    csv_file = SCENARIOS_DIR / "scenario_1_interference.csv"
    if not csv_file.exists():
        return
    with open(csv_file, "rb") as f:
        res = client.post("/api/v1/datasets/upload", files={"file": ("scenario_1.csv", f, "text/csv")})
    assert res.status_code == 201
    dataset = res.json()
    interf_cell = next((c for c in dataset["cells"] if c["cell_id"] == "CELL_INTERFERENCE_01"), None)
    assert interf_cell is not None
    assert interf_cell["status"] == "CRITICAL"
    assert any("coverage" in pc["category"].lower() or "interference" in pc["category"].lower() for pc in interf_cell["probable_causes"])


def test_scenario_2_congestion():
    csv_file = SCENARIOS_DIR / "scenario_2_congestion.csv"
    if not csv_file.exists():
        return
    with open(csv_file, "rb") as f:
        res = client.post("/api/v1/datasets/upload", files={"file": ("scenario_2.csv", f, "text/csv")})
    assert res.status_code == 201
    dataset = res.json()
    cong_cell = next((c for c in dataset["cells"] if c["cell_id"] == "CELL_CONGESTION_02"), None)
    assert cong_cell is not None
    assert cong_cell["status"] == "CRITICAL"
    assert any("congestion" in pc["category"].lower() for pc in cong_cell["probable_causes"])


def test_scenario_3_handover():
    csv_file = SCENARIOS_DIR / "scenario_3_handover.csv"
    if not csv_file.exists():
        return
    with open(csv_file, "rb") as f:
        res = client.post("/api/v1/datasets/upload", files={"file": ("scenario_3.csv", f, "text/csv")})
    assert res.status_code == 201
    dataset = res.json()
    ho_cell = next((c for c in dataset["cells"] if c["cell_id"] == "CELL_HANDOVER_03"), None)
    assert ho_cell is not None
    assert ho_cell["status"] == "CRITICAL"
    assert any("mobility" in pc["category"].lower() or "handover" in pc["category"].lower() for pc in ho_cell["probable_causes"])


def test_scenario_4_outage():
    csv_file = SCENARIOS_DIR / "scenario_4_outage.csv"
    if not csv_file.exists():
        return
    with open(csv_file, "rb") as f:
        res = client.post("/api/v1/datasets/upload", files={"file": ("scenario_4.csv", f, "text/csv")})
    assert res.status_code == 201
    dataset = res.json()
    outage_cell = next((c for c in dataset["cells"] if c["cell_id"] == "CELL_OUTAGE_04"), None)
    assert outage_cell is not None
    assert outage_cell["status"] == "CRITICAL"
    assert any("outage" in pc["category"].lower() for pc in outage_cell["probable_causes"])

