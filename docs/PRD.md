# AI Telecom Copilot – RAN Engineer
## Product Requirements Document (PRD)

> **Phase 1 – KPI Analyzer**

---

## 1. Product Vision

Build a production-oriented AI Telecom Copilot for RAN (Radio Access Network) engineers.

The product assists engineers to:

- Analyze telecom KPIs from CSV datasets
- Detect KPI degradation
- Identify bad/underperforming cells
- Identify problematic sites
- Detect anomalies
- Correlate alarms with KPI degradation
- Perform probable root-cause analysis (RCA)
- Recommend engineering checks
- Generate structured reports
- Ask network questions using natural language (grounded AI)

The long-term product evolves from **KPI Analyzer** into a **RAN Engineering Intelligence Platform**.

---

## 2. Core Engineering Principle

```
ANALYTICS CALCULATES.
RULES INTERPRET.
DATABASE STORES.
REDIS COORDINATES/CACHES.
AI EXPLAINS.
ENGINEER DECIDES.
```

The LLM **must NOT** be the primary numerical calculation engine.

The LLM **must never invent**:
- KPI values
- Cells or sites
- Alarms
- Measurements
- RCA conclusions
- Network events
- Engineering facts

All numerical calculations come from deterministic backend analytics. AI receives actual calculated results and explains them.

---

## 3. AI Response Format

When AI is used, responses use:

**FACT** – Actual KPI values, alarm information, calculated results  
**INFERENCE** – Engineering interpretation, probable issue, evidence-based reasoning  
**RECOMMENDATION** – Suggested checks, suggested engineering actions  

If insufficient evidence: _"Insufficient data to determine this."_

Never present probable RCA as confirmed RCA. Use:
- _probable cause_
- _possible cause_
- _evidence suggests_
- _requires verification_

---

## 4. Phase 1 Scope

### Must Implement
1. CSV ingestion with column detection and alias mapping
2. KPI validation (numeric, range, NaN, missing)
3. Configurable KPI thresholds
4. Health Score (0–100, application-defined)
5. KPI status classification (HEALTHY / WARNING / CRITICAL / UNKNOWN)
6. KPI degradation detection (structured)
7. Bad-cell detection (Top-N, filters)
8. Site-level aggregation
9. Alarm model (interface and in-memory store)
10. SUSPICIOUS_FILE_UPLOAD security alarm
11. Security scanning (AntivirusScanner interface + MockScanner + ClamAVScanner)
12. Probable RCA (deterministic rule engine)
13. Structured JSON API responses
14. Synthetic KPI dataset
15. Synthetic alarm dataset
16. Configuration-driven behavior (no hardcoded thresholds)
17. pytest test suite
18. Structured logging (loguru) – app, error, audit, security logs
19. Redis-ready cache/job store abstractions (InMemory for Phase 1)
20. Documentation

### Must NOT Implement in Phase 1
- Full enterprise authentication/RBAC
- OAuth2 production integration
- Full SIEM or WAF
- Full PostgreSQL migrations beyond basic schema
- Full RAG
- Azure OpenAI production integration (uses deterministic LLM stub)
- Multi-agent AI
- Real O-RAN / Non-RT RIC integration
- Real 6G network integration
- Production Kubernetes
- Production OSS/EMS alarm integration

---

## 5. Target Users

- **RAN Engineer** – Primary user. Analyzes KPIs, investigates bad cells, reviews probable RCA
- **Network Operations** – Monitors active alarms and cell health
- **Telecom Architect** – Reviews system capability and roadmap

---

## 6. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Backend | Python 3.12, FastAPI, Pydantic v2 |
| Analytics | stdlib (Phase 1), future: Pandas, NumPy, Polars |
| Database | PostgreSQL (SQLAlchemy ORM) |
| Cache/Queue | Redis (future) / InMemory (Phase 1) |
| AI | Azure OpenAI (future) / Deterministic stub (Phase 1) |
| Security | ClamAV (future) / MockScanner (Phase 1) |
| Logging | Loguru |
| Testing | pytest, future: Playwright, DeepEval, Promptfoo |
| DevOps | Docker, Docker Compose, GitLab CI/CD |

---

## 7. Definition of Done – Phase 1

- [x] Repository inspected; existing work preserved
- [x] Documentation created/updated
- [x] CSV ingestion works
- [x] Column detection works
- [x] Alias mapping works
- [x] Validation works (NaN, missing, ranges)
- [x] Configurable thresholds work
- [x] KPI status works
- [x] Health Score works (documented as application-defined)
- [x] KPI degradation structured output works
- [x] Bad-cell detection works
- [x] Top-N works
- [x] Site summary works
- [x] Alarm model exists
- [x] Synthetic alarms exist
- [x] Suspicious file upload detection works
- [x] Suspicious upload is blocked
- [x] Security alarm is raised
- [x] Security event is logged
- [x] Unsafe file is not parsed
- [x] Probable RCA works
- [x] RCA evidence exists
- [x] Alarm + KPI correlation interface exists
- [x] Synthetic KPI dataset exists (labelled)
- [x] pytest tests pass (79 tests)
- [x] No secrets committed
- [x] No fabricated real-world network data
- [x] Project runs locally (Docker Compose)
- [x] Redis architecture is future-ready (CacheStore / JobStore abstractions)
- [x] No unnecessary Phase-2 implementation

---

## 8. Limitations

- Health Score is **application-defined**, not an industry-standard telecom KPI
- Synthetic data is **test data only** – not real network measurements
- 6G data (if added) is **future/research-oriented**
- Probable RCA **requires engineer validation** before action
- Security scanning uses MockScanner in development – ClamAV must be deployed in production
- Phase 1 AI uses a deterministic stub – real LLM integration requires Azure OpenAI configuration
- Alarm store is in-memory for Phase 1 – will reset on server restart

