# Phase 1 API

All endpoints are prefixed by `/api/v1` and documented in Swagger UI (`/docs`) in development.

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Health probe |
| `POST /datasets/upload` | Validate and analyze a KPI CSV |
| `GET /datasets` | List uploaded development datasets |
| `GET /datasets/{id}/summary` | KPI availability and score summary |
| `GET /datasets/{id}/bad-cells` | Filter/rank underperforming cells |
| `GET /cells/{cell_id}/analysis` | Cell evidence and probable causes |
| `POST /chat` | Grounded MVP intent handling |

The chat endpoint only handles deterministic, dataset-backed questions. A future LLM provider must use controlled result tools.
