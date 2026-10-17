# AI Telecom Copilot – RAN Engineer

AI Telecom Copilot is an intelligent engineering platform designed to help mobile network teams analyze radio access network (RAN) performance, detect degradation, prioritize problem cells, identify site issues, and support faster engineering decisions. The project combines deterministic KPI analytics with AI-driven explanation layers to provide a safer and more useful telecom operations assistant.

The system is built to support 4G, 5G, O-RAN, and future AI-RAN environments. The first release focuses on a reliable KPI analysis engine that ingests CSV data, validates and normalizes metrics, calculates health scores, identifies bad cells, detects degradation, correlates alarms, and produces probable root-cause analysis using transparent, rule-based logic.

---

## Project Vision

The long-term goal is to create a practical AI-powered RAN engineering platform that helps engineers:

- analyze telecom KPIs,
- detect KPI degradation,
- identify bad cells and problematic sites,
- correlate alarms with performance issues,
- detect anomalies,
- support probable root-cause analysis,
- recommend engineering checks,
- generate structured operational reports,
- answer natural-language network questions with grounded evidence,
- support future O-RAN and Non-RT RIC workflows,
- prepare for AI-native 6G / IMT-2030 research use cases.

This project evolves from a KPI analyzer into a broader RAN Engineering Intelligence Platform.

---

## What the project solves

Telecom operations teams often receive large KPI exports and alarm datasets from multiple network elements. Manual analysis is slow, inconsistent, and error-prone. Engineers need a system that can:

- validate incoming data,
- detect missing or invalid KPI values,
- normalize different metric names and units,
- identify poor-performing cells and sites,
- highlight degradation patterns quickly,
- show health scores in a clear and explainable format,
- provide evidence-based probable RCA,
- block unsafe or suspicious uploads before processing.

The project addresses these needs with a deterministic analytics-first architecture, so the AI layer explains results rather than inventing them.

---

## Core outcome of the project

The current Phase 1 implementation delivers a working telecom KPI analytics foundation with these outcomes:

1. CSV ingestion and validation
2. KPI detection and alias mapping
3. Unit and value normalization
4. Configurable threshold evaluation
5. KPI status classification
6. Health score calculation for cells
7. Bad-cell detection
8. Site-level summary reporting
9. KPI degradation detection
10. Alarm model and structure
11. Synthetic alarm dataset generation
12. Suspicious file upload detection and blocking
13. Security alarm generation
14. Probable root-cause analysis using deterministic rules
15. Structured JSON outputs for dashboards and APIs
16. Test coverage for the main analytics pipeline

This is a practical Phase 1 foundation, not a full enterprise SIEM or full AI assistant stack.

---

## Why this matters

In real telecom networks, poor KPI performance can affect:

- customer experience,
- call quality,
- data throughput,
- handover success,
- service reliability,
- network capacity planning,
- maintenance prioritization,
- NOC operations.

This project gives engineers a structured way to identify weak network areas before they become larger incidents. It reduces guesswork and supports faster validation of root causes.

---

## Benefits

### For RAN engineers
- Quickly checks whether a cell or site is degraded.
- Understands which KPIs are poor and why.
- Identifies priority cells using health score and severity.
- Uses evidence-based probable RCA rather than speculative conclusions.

### For operations teams
- Faster triage of KPI issues and alarm patterns.
- Better prioritization of engineering action.
- Cleaner reporting and structured outputs for review.
- Safer handling of suspicious files before ingestion.

### For AI-assisted workflows
- AI is grounded in actual analytics results.
- LLM responses are constrained by deterministic tools and evidence.
- Reduces hallucination risk by preventing fabricated KPI values, cells, alarms, or locations.

### For future platform evolution
- The architecture is modular and extendable.
- Supports future O-RAN, Non-RT RIC, and AI-RAN use cases.
- Provides a strong base for knowledge retrieval, incident correlation, and automation.

---

## Key capabilities

### 1. KPI ingestion and validation
The system accepts KPI CSV files, detects relevant columns, validates row and value quality, and flags missing or malformed entries.

### 2. KPI alias mapping
It supports aliases such as RSRP, SINR, DL throughput, PRB utilization, and others through configuration-driven mappings instead of hard-coded assumptions.

### 3. Threshold-driven status evaluation
Each KPI uses configurable threshold definitions to classify performance as GOOD, WARNING, CRITICAL, or UNKNOWN.

### 4. Health Score
The application-defined Health Score combines critical cell KPIs into a weighted score from 0 to 100, helping identify underperforming cells.

### 5. Bad-cell detection
The platform identifies the worst cells by KPI issues, health score, severity, and filters such as technology or site.

### 6. Site-level analytics
Site summaries aggregate results from cell-level health and KPI status to provide an operational view of performance across the site.

### 7. Alarm model
The project includes an alarm model for severity, status, source, timing, and description. It supports synthetic alarm generation and future correlation with KPI degradation.

### 8. Security alarm for suspicious uploads
Files are screened for filename, extension, content, file size, and unsafe patterns. Harmful or suspicious files are blocked and recorded as a security alarm before parsing or analysis.

### 9. Probable RCA
The rule engine generates possible causes using durable engineering logic, such as:
- weak coverage + poor SINR + low throughput,
- high PRB + low throughput,
- high call drop + poor handover,
- low availability,
- alarm + KPI evidence correlation.

Each RCA includes evidence, severity, confidence, and recommended checks.

---

## Architecture summary

The system follows a modular, deterministic design:

- Input layer: CSV upload and validation
- Analytics layer: KPI mapping, normalization, scoring, degradation, site analysis
- Rules layer: probable RCA and engineering interpretation
- Alarm layer: alarm classification and correlation hooks
- Security layer: suspicious upload detection and blocking
- AI layer: grounded explanation using deterministic analytic outputs
- Data/config layer: YAML/JSON configuration and future-ready persistence

The architecture intentionally separates:

- Analytics calculates
- Rules interpret
- Database stores
- Redis coordinates/caches
- AI explains
- Engineer decides

This ensures the LLM does not act as the primary numeric engine and does not invent facts.

---

## System principles

- Deterministic calculations before AI interpretation
- Configuration-driven KPI aliases and thresholds
- Evidence-first RCA without unsupported certainty
- Structured output for dashboards and APIs
- Security-first file handling
- Phase-based implementation to reduce unnecessary scope

---

## Future use and business value

This project is not just a small KPI utility. It is a foundation for a broader intelligent telecom operations platform.

### Near-term future use
- KPI trend analysis over time
- More advanced alarm correlation
- Better site and cluster-level health views
- Scripted engineering reports
- Integration with additional network data sources

### Mid-term future use
- O-RAN / Non-RT RIC support
- AI-assisted engineering recommendations
- rApp concept validation and policy template generation
- Alert and incident context linking
- Better optimization recommendations for coverage and capacity

### Long-term future use
- AI-native RAN operations
- 6G / IMT-2030 research readiness
- Knowledge retrieval for telecom troubleshooting
- Intelligent automation with human approval guardrails
- Distributed AI workflows for network optimization

### Strategic benefit
This platform can evolve into a decision-support system for engineering teams, helping them move from reactive issue handling to proactive network optimization.

---

## Technology stack

### Backend
- Python
- FastAPI
- Pydantic
- SQLAlchemy (future and present persistence layer support)
- Pandas / NumPy / Polars-ready design

### Frontend
- Next.js
- TypeScript
- Tailwind CSS

### Data and configuration
- CSV ingestion and validation
- JSON/YAML configuration for KPIs, rules, and thresholds
- PostgreSQL-ready architecture
- Redis-ready coordination and caching layer

### AI and security
- Azure OpenAI abstraction design
- Guardrails and grounded response patterns
- Suspicious file upload detection
- Audit and security event logging

### Testing
- pytest
- Playwright-ready future UI testing
- structured quality checks for analytics and API logic

---

## Repository structure

```text
AI_Telecom_Copilot-RAN_Egineer/
├── README.md
├── docs/
├── cicd-script/
├── ranengineer/
│   ├── backend/
│   ├── frontend/
│   └── config/
├── configs/
├── data/
├── tests/
├── scripts/
└── project.txt
```

---

## Local setup

### 1. Backend

```bash
cd ranengineer/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 2. Frontend

```bash
cd ranengineer/frontend
npm install
npm run dev
```

### 3. API docs

Open:

```text
http://localhost:8000/docs
```

The frontend can usually be checked at:

```text
http://localhost:3000
```

---

## Testing

Run the project tests:

```bash
./cicd-script/test.sh
```

This validates the main Phase 1 behaviors including:

- CSV parsing
- KPI mapping
- validation logic
- normalization
- thresholds
- health score
- degradation detection
- bad-cell detection
- site aggregation
- RCA rules
- suspicious upload blocking
- API and schema behavior

---

## Security and reliability

The project includes security considerations aligned with the current Phase 1 scope:

- filename validation
- extension and content validation
- file size limits
- temporary file safety
- suspicious upload detection
- block-and-audit flow for unsafe files
- logging of security events without exposing internal scanner details
- explicit refusal to process suspicious datasets

This is intentionally limited to suspicious file upload protection, not a complete SIEM or full enterprise security platform.

---

## Data standards and engineering rules

The system follows these important design rules:

- LLMs do not calculate KPIs
- LLMs do not invent network facts
- all numeric values must come from deterministic analysis
- rules provide probable interpretation, not certainty
- synthetic data is clearly labeled as test data
- health score is application-defined and not a standard telecom KPI
- future 6G data is framed as research-oriented only

---

## Example of analysis output

```json
{
  "dataset": {
    "dataset_id": "dataset_001",
    "data_type": "SYNTHETIC_TEST_DATA"
  },
  "summary": {
    "total_cells": 100,
    "good": 62,
    "warning": 23,
    "critical": 15
  },
  "bad_cells": [
    {
      "cell_id": "CELL102",
      "site_id": "SITE10",
      "technology": "5G_NR",
      "health_score": 31,
      "severity": "CRITICAL",
      "issues": ["POOR_RSRP", "POOR_SINR", "HIGH_PRB", "LOW_THROUGHPUT"]
    }
  ],
  "kpi_degradation": [],
  "alarms": [],
  "rca": []
}
```

---

## Current phase and scope

This project is intentionally scoped to Phase 1 only. Phase 1 focuses on the foundations needed to support broader future capabilities without prematurely building an enterprise system.

Current phase intentionally does not include:
- full production authentication and RBAC,
- broad SIEM implementation,
- full RAG deployment,
- Kubernetes production setup,
- live O-RAN / Non-RT RIC integration,
- final enterprise PostgreSQL architecture,
- automatic rApp deployment,
- full AI multi-agent orchestration.

---

## Roadmap

### Phase 1
- KPI ingestion and validation
- health scoring and degradation detection
- synthetic alarm and KPI data
- suspicious upload security blocking
- deterministic RCA rules
- tests and documentation

### Phase 2
- richer alarm correlation
- more site and cluster analytics
- trend analysis and historical comparison
- better UI dashboards and operational reporting
- Redis-backed background job processing

### Phase 3
- expanded AI grounding and controlled tools
- more advanced knowledge retrieval
- wider incident correlation workflows
- improved API and system integrations

### Phase 4+
- O-RAN and Non-RT RIC readiness
- AI-RAN optimization workflows
- future 6G and IMT-2030 research interfaces

---

## Final note

AI Telecom Copilot – RAN Engineer is designed to help engineering teams move faster, work with more evidence, and reduce operational risk in RAN performance management. It is built around a principle that matters most in telecom operations: analytics should calculate, rules should interpret, and AI should explain supported findings—not invent them.

This makes the project both practical today and valuable as a foundation for future AI-driven network intelligence.


