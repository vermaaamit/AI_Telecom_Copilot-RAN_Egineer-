# RAN Engineer Backend MVP

This is a modular FastAPI application. It deliberately keeps ingestion, scoring, rule-based interpretation, API routing, and future AI integration in separate modules while remaining one deployable backend for the MVP.

## Run locally

```bash
cd ranengineer/backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open Swagger UI at `http://localhost:8000/docs`. Upload `tests/fixtures/kpi_sample.csv` through `POST /api/v1/datasets/upload`.

## Reliability model

KPI measurements, classifications, and the application-defined health score are deterministic. KPI aliases, thresholds, and weights reside in `../configs/kpi/definitions.json`, not business logic. The rule engine labels interpretations as **probable causes**; it does not make definitive fault claims. The in-memory repository is development-only and will be replaced by a database repository in a later phase.
