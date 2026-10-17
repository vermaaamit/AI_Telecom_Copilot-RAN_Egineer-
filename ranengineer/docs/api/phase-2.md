# Phase 2 REST API Documentation

All endpoints are versioned under `/api/v1` and documented in Swagger UI at `http://localhost:8000/docs`.

## Endpoint Matrix

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/health` | Health check probe |
| `POST` | `/api/v1/datasets/upload` | Upload & analyze KPI CSV (multipart/form-data) |
| `GET` | `/api/v1/datasets` | List all analyzed datasets |
| `GET` | `/api/v1/datasets/{dataset_id}` | Retrieve complete dataset details |
| `GET` | `/api/v1/datasets/{dataset_id}/summary` | Retrieve KPI health score & category breakdown |
| `GET` | `/api/v1/datasets/{dataset_id}/cells` | List cells within a dataset (with pagination `limit`) |
| `GET` | `/api/v1/datasets/{dataset_id}/bad-cells` | Retrieve ranked underperforming cells with filters |
| `GET` | `/api/v1/datasets/{dataset_id}/anomalies` | Retrieve critical cell anomalies for a dataset |
| `GET` | `/api/v1/cells/{cell_id}` | Retrieve single cell record and KPI values |
| `GET` | `/api/v1/cells/{cell_id}/analysis` | Deterministic cell analysis with summary and checks |
| `GET` | `/api/v1/anomalies` | Cross-dataset critical cell anomaly search |
| `GET` | `/api/v1/kpis` | Configured KPI definitions, thresholds, weights |
| `POST` | `/api/v1/chat` | Grounded telecom query interface |

## Error Responses

Errors strictly conform to Section 26:
```json
{
  "error": {
    "code": "INVALID_KPI_FILE",
    "message": "Required cell identifier column was not found.",
    "details": []
  }
}
```

