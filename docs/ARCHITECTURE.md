# AI Telecom Copilot – Architecture Overview

## Core System Axiom
> **ANALYTICS CALCULATES. RULES INTERPRET. AI EXPLAINS. ENGINEER DECIDES.**

The architecture is explicitly decoupled into deterministic computation, rule-based reasoning, persistent relational storage, and grounded generative AI assistance.

```
                    ┌───────────────────────────────┐
                    │      Next.js Frontend         │
                    │ (Dashboard, Cells, Alarms,    │
                    │    Incidents, Copilot Chat)   │
                    └───────────────┬───────────────┘
                                    │ HTTP / REST
                                    ▼
                    ┌───────────────────────────────┐
                    │      FastAPI API Gateway      │
                    │  (Validation, Routing, Auth)  │
                    └───────┬───────────────┬───────┘
                            │               │
            ┌───────────────┴────┐     ┌────┴────────────────┐
            ▼                    ▼     ▼                     ▼
┌─────────────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│ Ingestion & Validation  │  │ Deterministic     │  │ AI Copilot        │
│ - ClamAV / Mock Scanner │  │ Telecom Analytics │  │ - Intent Parser   │
│ - CSV Normalization     │  │ - Health Scoring  │  │ - Tool Dispatcher │
│ - Header Alias Mapping  │  │ - Rule Engine RCA │  │ - Guardrails      │
└───────────┬─────────────┘  │ - Correlation     │  └────────┬──────────┘
            │                └─────────┬─────────┘           │
            ▼                          ▼                     │
┌────────────────────────────────────────────────────────┐   │
│              PostgreSQL Relational Storage             │◄──┘
│  - Datasets & Cells (Historical & Active Telemetry)    │
│  - Alarms (OSS/EMS persistent alerts & security logs)  │
│  - Incidents (Operator tickets & resolution tracking)  │
│  - Managed via Alembic Migrations                      │
└────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. Ingestion & Security Pipeline
- **Security Scanner**: Inspects all file uploads for malware and suspicious patterns before processing. Blocks untrusted files and automatically creates critical security alarms.
- **CSV Parser**: Normalizes messy real-world telecom CSV headers via configurable KPI alias registries (`configs/kpi_definitions.json`). Rejects non-CSV files and malformed payloads.

### 2. Deterministic Analytics Engine
- **KPI Registry & Thresholds**: Evaluates RAN performance metrics (`PRB_UTILIZATION`, `THROUGHPUT_DL`, `SINR`, `CQI`, `BLER`, `CALL_DROP_RATE`) against telecom threshold bands (`GOOD`, `WARNING`, `CRITICAL`).
- **Health Scoring**: Computes a normalized 0–100 health score for every cell deterministically based on weighted KPI domain scores.
- **Rule Engine (RCA)**: Evaluates expert telecom rules from `configs/rules/ran_rules.json` to identify probable causes (Coverage & Interference, Congestion, Outage, Transport).
- **Alarm Correlation Engine**: Correlates degraded KPIs with persistent alarms using spatial (cell-level and site-level) and domain-specific telemetry mappings with confidence levels (`HIGH`, `MEDIUM`, `LOW`).

### 3. Persistent Data Layer (PostgreSQL & Alembic)
- Managed via SQLAlchemy 2.0 ORM with async migration support via Alembic.
- **Tables**:
  - `datasets`: Ingested file metadata, telemetry summary, and column mapping statuses.
  - `cells`: Cell-level telemetry records, health scores, and computed probable causes.
  - `alarms`: Network and security alarms (OSS/EMS alerts, severity, lifecycle states).
  - `incidents`: Engineering incident management, affected cell associations, and resolution audit trails.

### 4. AI Copilot & Guardrails
- **Intent Dispatcher**: Maps natural language queries to backend deterministic analytics functions.
- **Grounding Guardrails**: Strictly prevents LLM hallucination. Ensures that all cell IDs, KPI figures, and root cause descriptions exist in database telemetry. Replaces definitive claims with probabilistic phrasing.

### 5. Multi-Agent Orchestration & RAG
- **Knowledge Base**: Curated 3GPP and O-RAN specifications in `configs/knowledge/documents.json`.
- **Specialized Subagents**: Coordinates 5 analytical subagents (KPI Analyst, Anomaly Specialist, RCA & Alarm Specialist, Standards Specialist, Optimization Specialist) synthesized via `MultiAgentOrchestrator`.

### 6. O-RAN Non-RT RIC rApp Studio
- **A1-P Declarative Policies**: Conforming to O-RAN WG2 standards for Traffic Steering (#20000), Energy Saving (#20001), and QoE Assurance (#20002).
- **Safety Guardrails**: Prohibits unattended live execution without engineer sign-off and enforces underlay coverage preservation on energy-saving policies.

### 7. 6G / IMT-2030 Digital Twin Engine
- **RF Ray-Tracing Physics**: Deterministic what-if modeling for antenna downtilt/uptilt, inter-cell interference, and Massive MIMO spatial multiplexing.
- **6G Sub-THz Throughput**: Shannon capacity modeling over 140 GHz D-Band channels up to 2 GHz channel width.
- **ISAC Radar Co-Design**: Integrated Sensing and Communication trade-offs between communication spectral efficiency and radar range resolution ($\Delta R = c / (2 \cdot B_{\text{sensing}})$).
- **Synthetic Research Tagging**: Tagged strictly as `is_synthetic=True` and `research_tier="6G_IMT2030_AI_NATIVE"`.

### 8. Threat Auditing & Redis Security Counters
- **Sliding Window Counters**: Redis atomic TTL keys tracking failed logins, uploads, and API quotas with in-memory fallback.
- **Anti-Brute-Force Lockout**: 15-minute lock on accounts with >5 failed login attempts (HTTP 423).
- **Prompt Injection Defense**: Regex-based detection of instruction override, prompt leaks, SQL injections, and guardrail bypass attempts before prompt dispatch.

### 9. CI/CD Pipeline & Production Automation
- **GitHub Actions Workflow**: 7-stage pipeline (lint → unit tests → integration tests → security tests → AI evals → frontend build → Docker build) ensuring every commit to `main` passes deterministic telecom analytics, grounding, and adversarial security checks.
- **Production Seed Script**: `scripts/seed_production.py` bootstraps a fresh environment with baseline 4G/5G telemetry, correlated alarms, operational incidents, and validated O-RAN rApp policies.

### 10. AI Evaluation Harness
- **Groundedness & Faithfulness Tests**: Verify that AI copilot responses never reference non-existent cells, always use probabilistic phrasing, and that RAG retriever returns accurate 3GPP/O-RAN standards.
- **Adversarial Security Evaluations**: 22+ parametric attack vectors (instruction overrides, prompt leaks, SQL injection payloads, guardrail bypasses) tested with zero false negatives against the `SecurityAuditor` regex scanner.



