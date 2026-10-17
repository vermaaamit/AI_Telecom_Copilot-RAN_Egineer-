# Phase 1 Self-Testing & Verification Guide

This guide provides simple, step-by-step instructions for testing and validating all features implemented in **Phase 1** of **AI Telecom Copilot – RAN Engineer**.

---

## 1. Automated Test Suite (79 Tests)

Run the full automated test suite inside Docker. All 79 tests should pass in ~3-4 seconds.

```bash
# Run from repository root
cd /home/amitverma/Desktop/project/AI_Telecom_Copilot-RAN_Egineer

docker compose -f ranengineer/docker-compose.yml run --rm backend pytest -v
```

### Running Targeted Test Groups:
- **API Integration Tests:**
  ```bash
  docker compose -f ranengineer/docker-compose.yml run --rm backend pytest tests/integration/test_api_endpoints.py -v
  ```
- **Security & Alarms Integration Tests:**
  ```bash
  docker compose -f ranengineer/docker-compose.yml run --rm backend pytest tests/integration/test_security_and_alarms.py -v
  ```
- **AI Intent & Deterministic Dispatcher Tests:**
  ```bash
  docker compose -f ranengineer/docker-compose.yml run --rm backend pytest tests/unit/test_ai_intent.py tests/unit/test_ai_tools.py -v
  ```
- **RCA Rules & Health Score Tests:**
  ```bash



  
  docker compose -f ranengineer/docker-compose.yml run --rm backend pytest tests/unit/test_rca_rules.py tests/unit/test_health_score.py -v
  ```

---

## 2. Service Status Check

Check that all containers are healthy and running:
```bash
docker compose -f ranengineer/docker-compose.yml ps
```

You should see:
- `ranengineer-backend-1` on port `8000`
- `ranengineer-frontend-1` on port `3000`
- `ranengineer-postgres-1` (healthy)
- `ranengineer-redis-1`

If any container is stopped, start the stack:
```bash
docker compose -f ranengineer/docker-compose.yml up -d
```

Stop container
```bash
docker compose -f ranengineer/docker-compose.yml stop
```

## 3. Interactive Web Testing

Open your browser to test interactively:
- **Interactive Swagger UI / API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Frontend Dashboard:** [http://localhost:3000](http://localhost:3000)

---

## 4. Step-by-Step Manual Testing via `curl`

You can run these commands from your terminal on your host machine.

### Step 4.1: Health Check
Verify the backend service is responding:
```bash
curl -s http://localhost:8000/api/v1/health | jq .
```
**Expected Response:**
```json
{
  "status": "ok",
  "service": "ranengineer-backend"
}
```

---

### Step 4.2: KPI Definitions
Verify that the telecom KPI registry is loaded:
```bash
curl -s http://localhost:8000/api/v1/kpis/definitions | jq .
```
**Expected Response:** A list of standard RAN KPIs (e.g., `PRB_UTILIZATION`, `THROUGHPUT_DL`, `CQI`, `BLER`, `RSRP`, `SINR`, `CALL_DROP_RATE`) with target thresholds, units, and directions.

---

### Step 4.3: Upload a Valid KPI Dataset
Upload the synthetic RAN dataset:
```bash
curl -s -X POST http://localhost:8000/api/v1/datasets/upload \
  -F "file=@ranengineer/data/synthetic/kpi_dataset_synthetic.csv" | jq .
```
**Expected Output:**
- Returns a dataset object with:
  - `"id"`: `<DATASET_UUID>`
  - `"cell_count"`: Total cells processed
  - `"summary"`: Health status breakdown (`healthy`, `warning`, `critical`, `unknown`)
  - `"cells"`: Detailed cells list with calculated `health_score` (0-100), `kpis`, and deterministic `probable_causes`.

> **Note:** Save the returned `id` (e.g. `DATASET_ID="<id>"`) to use in following commands.

---

### Step 4.4: List and Retrieve Datasets
```bash
# List all datasets
curl -s http://localhost:8000/api/v1/datasets | jq .

# Get specific dataset (replace with your dataset ID)
DATASET_ID=$(curl -s http://localhost:8000/api/v1/datasets | jq -r '.[0].id')
echo "Dataset ID: $DATASET_ID"

curl -s "http://localhost:8000/api/v1/datasets/$DATASET_ID" | jq .
```

---

### Step 4.5: Inspect Underperforming Cells (Bad Cells)
Filter cells with status `CRITICAL` or `WARNING`:
```bash
curl -s "http://localhost:8000/api/v1/datasets/$DATASET_ID/worst-cells?limit=5" | jq .
```
**Expected Output:**
- Returns the lowest health score cells first.
- Each cell contains `kpi_statuses`, `kpi_degradation`, and deterministic `probable_causes`.

---

### Step 4.6: Site-Level Aggregation
Query aggregated site statistics across all cells on a given site:
```bash
# Query site aggregation for a site (e.g. SITE_001)
curl -s "http://localhost:8000/api/v1/datasets/$DATASET_ID/sites/SITE_001" | jq .
```
**Expected Output:**
- Average health score for the site.
- Aggregated average KPIs across sectors.
- List of cells belonging to that site.

---

### Step 4.7: Security Scanning & Suspicious File Blocking
Phase 1 includes a security scanner that blocks malicious payloads and triggers critical security alarms.

**Test 1: Block Non-CSV Extension**
```bash
curl -s -X POST http://localhost:8000/api/v1/datasets/upload \
  -F "file=@ranengineer/docker-compose.yml;filename=test.yml" | jq .
```
**Expected Output:** HTTP 400 rejection: `Only .csv files are supported.`

**Test 2: Block Suspicious / Malware-containing File & Trigger Alarm**
```bash
# Attempt to upload a file with suspicious signature
curl -s -X POST http://localhost:8000/api/v1/datasets/upload \
  -F "file=@ranengineer/data/synthetic/kpi_dataset_synthetic.csv;filename=malware_sample.csv" | jq .
```
**Expected Output:**
- HTTP 400 rejection: `Malicious or suspicious file detected and blocked.`
- An active `CRITICAL` alarm is automatically created in the alarms repository.

---

### Step 4.8: Verify Alarm Lifecycle
Check that alarms are stored and can be acknowledged/cleared:

```bash
# 1. List all active alarms
curl -s http://localhost:8000/api/v1/alarms/active | jq .

# 2. List all critical alarms
curl -s http://localhost:8000/api/v1/alarms/critical | jq .

# 3. Create a synthetic test alarm
ALARM_JSON=$(curl -s -X POST http://localhost:8000/api/v1/alarms \
  -H "Content-Type: application/json" \
  -d '{
    "alarm_type": "HIGH_PRB_UTILIZATION",
    "severity": "CRITICAL",
    "description": "PRB utilization exceeded 95%",
    "source": "OSS_SYNTHETIC",
    "cell_id": "CELL_001",
    "site_id": "SITE_001"
  }')
echo "$ALARM_JSON" | jq .
ALARM_ID=$(echo "$ALARM_JSON" | jq -r '.alarm_id')

# 4. Acknowledge the alarm
curl -s -X PATCH "http://localhost:8000/api/v1/alarms/$ALARM_ID/acknowledge" | jq .

# 5. Clear the alarm
curl -s -X PATCH "http://localhost:8000/api/v1/alarms/$ALARM_ID/clear" | jq .
```

---

### Step 4.9: Deterministic AI Chat & Intent Execution
The AI Chat endpoint parses natural language queries and dispatches deterministic analytics tools without hallucinations:

```bash
DATASET_ID=$(curl -s http://localhost:8000/api/v1/datasets | jq -r '.[0].id')

# Ask for worst/underperforming cells
curl -s -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"Which cells are performing poorly in this network?\",
    \"dataset_id\": \"$DATASET_ID\"
  }" | jq .
```
**Expected Response:**
- `"intent"`: `FIND_BAD_CELLS`
- `"data"`: Deterministic list of degraded cells calculated by the backend analytics.
- `"response"`: Grounded explanation following *"Analytics calculates. Rules interpret. AI explains. Engineer decides."*

---

## 5. Verification Checklist

| Test Item | Verification Method | Result |
|---|---|:---:|
| 79 Automated Tests | `pytest -v` inside Docker | [x] Passed |
| File Type Validation | Rejects non-CSV files | [x] Passed |
| Security Scanner | Detects suspicious signatures & rejects | [x] Passed |
| Security Alarm Generation | Raises `SUSPICIOUS_FILE_UPLOAD` alarm | [x] Passed |
| CSV Normalization & Parser | Ingests telecom KPIs, handles missing data | [x] Passed |
| Cell Health Score | Computes 0-100 score deterministically | [x] Passed |
| Rule-Based RCA | Classifies Coverage, Interference, Congestion | [x] Passed |
| Site Aggregation | Groups sectors into site statistics | [x] Passed |
| Alarms Lifecycle | Create, List Active/Critical, Acknowledge, Clear | [x] Passed |
| Natural Language Chat | Classifies intent & runs deterministic analytics | [x] Passed |
| Zero Hallucination Guardrail | Rejects fabricated cell IDs / absolute claims | [x] Passed |

