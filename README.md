# AI Telecom Copilot — RAN Engineer

AI Telecom Copilot is a production-oriented assistant for 4G/5G/O-RAN engineering. Its first working capability is a deterministic KPI CSV analyzer: upload a KPI export, validate and normalize it, score cells, identify underperformers, and surface rule-based **probable causes**.

## Repository layout

```text
.
├── cicd-script/                 # Build, test, and deployment entrypoints
└── ranengineer/
    ├── frontend/                # Next.js + TypeScript dashboard
    ├── backend/                 # Modular FastAPI MVP
    ├── analytics-engine/        # Future shared analytics pipeline modules
    ├── knowledge-base/          # Curated 4G, 5G, RAN, and O-RAN knowledge
    ├── database/                # Migrations, schemas, and seed data
    ├── configs/                 # Versioned KPI configuration
    ├── tests/                   # Cross-service tests
    ├── deployments/             # Docker and Kubernetes assets
    └── docs/                    # Architecture and API documentation
```

## Run locally

Start the API:

```bash
cd ranengineer/backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then start the dashboard:

```bash
cd ranengineer/frontend
npm install
npm run dev
```

The API documentation is available at `http://localhost:8000/docs`. Set `NEXT_PUBLIC_API_BASE_URL` to override the browser API URL.

## Data reliability & AI Grounding

- Analytics, not an LLM, calculates KPI statuses and the application-defined health score.
- KPI aliases, thresholds, directions, and weights live in [`ranengineer/configs/kpi/definitions.json`](ranengineer/configs/kpi/definitions.json).
- Unit normalization automatically strips unit suffixes (`dBm`, `dB`, `Mbps`, `%`, `ms`) and handles null tokens (`N/A`, `NaN`, `-`).
- Rules present engineering interpretations as **probable causes**, never confirmed faults.
- Database persistence is backed by PostgreSQL with SQLAlchemy ORM and schema migrations.
- AI Copilot queries execute deterministic, controlled analytics tools (`find_bad_cells`, `get_cell_analysis`, `compare_cells`, `filter_cells_by_kpi`, `compare_sites`, `get_anomalies`, `get_kpi_trend`).
- Guardrails verify cell identifiers and enforce structured responses with limitations and confidence boundaries.

## Testing and Verification

Run backend unit and integration tests (56 automated tests covering parser, mapping, thresholds, scoring, bad cells, RCA rules, AI intent parser, controlled tools, grounding guardrails, and API endpoints):

```bash
./cicd-script/test.sh
```

## Automation

```bash
./cicd-script/build.sh
./cicd-script/test.sh
./cicd-script/deploy.sh
```

`deploy.sh` starts the local Docker Compose stack. Copy `ranengineer/.env.example` to `ranengineer/.env` before making environment-specific changes.


