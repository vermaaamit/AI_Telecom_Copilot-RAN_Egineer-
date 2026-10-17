# AI Telecom Copilot – Project Memory & Context

## Key Architectural Decisions
1. **Separation of Computation and Explanations**: Analytics (health scores, aggregations, thresholds) and Rules (probable causes, alarms correlation) are strictly implemented in Python and executed deterministically. The AI layer (LLM) is strictly an intent translator and explanation synthesizer.
2. **Database Migrations**: We use Alembic with PostgreSQL. Every change to `app/models/` must be paired with an Alembic revision script executed via `alembic -c app/alembic.ini upgrade head`.
3. **Correlation Confidence Logic**:
   - `HIGH`: Direct cell ID match + matching degraded KPI domain.
   - `MEDIUM`: Site-level match + matching degraded KPI domain.
   - `LOW`: Co-located site alarm without direct KPI domain match.
4. **Alarm & Incident Lifecycles**:
   - Alarms transition: `ACTIVE` -> `ACKNOWLEDGED` -> `CLEARED`.
   - Incidents transition: `OPEN` -> `RESOLVED` (requires resolution notes).
5. **Time-Series Trends & Forecasting (Phase 3)**:
   - Evaluates telemetry trajectories across chronological datasets.
   - Calculates linear slope and percentage change against baseline.
   - Classifies trajectory into `DEGRADING`, `IMPROVING`, or `STABLE`.
6. **Predictive Degradation Velocity**:
   - Analyzes velocity ($\Delta KPI / \Delta t$) before alarms fire.
   - Proactively alerts on cells on trajectory to breach critical thresholds.
7. **RAG Knowledge Base (Phase 4)**:
   - Curated 3GPP & O-RAN engineering standards in `configs/knowledge/documents.json`.
   - Keyword & domain token relevance scoring without replacing numerical KPI telemetry.
8. **Multi-Agent Orchestration**:
   - `MultiAgentOrchestrator` runs 5 specialized analytical subagents (`KPI Analyst`, `Anomaly Specialist`, `RCA & Alarm Specialist`, `Standards Specialist`, `Optimization Specialist`).
   - Synthesizes findings into unified engineer recommendations.
9. **O-RAN Non-RT RIC rApp Guardrails (Phase 6)**:
   - A1-P declarative policy generation for Traffic Steering (Type 20000), Energy Saving (Type 20001), and QoE Assurance (Type 20002).
   - Mandatory guardrail: Energy saving requires explicit underlay coverage protection.
   - Direct automated live deployment is strictly blocked without formal engineer sign-off.
10. **RBAC Authentication & Permissions**:
   - HS256 JWT tokens with 8-hour expiry.
   - Roles: `ADMIN`, `RAN_ENGINEER`, `VIEWER`.
   - Role checking enforced on write operations (`require_role(...)`).
11. **Shift Handover Intelligence**:
   - Aggregates multi-source telemetry, active alarms, open incidents, and predictive velocity warnings into structured operational briefings.
12. **6G & Digital Twin RF Ray-Tracing Physics (Phase 7)**:
   - Deterministic ray-tracing modeling for downtilt/uptilt SINR impact, Massive MIMO spatial multiplexing, 140 GHz sub-THz bandwidth, and ISAC radar trade-offs.
   - All research outputs are explicitly tagged with `is_synthetic=True` and `research_tier="6G_IMT2030_AI_NATIVE"`.
   - Uptilt (negative tilt) is flagged as HIGH risk due to beam overshoot and inter-cell pilot pollution.
13. **Advanced Redis Security Auditing & Anti-Brute-Force**:
   - Atomic sliding window TTL counters in Redis (`failed_login`, `upload_count`, `api_requests`) with automatic memory fallback.
   - Accounts automatically locked for 15 minutes after 5 consecutive failed login attempts (HTTP 423 Locked).
   - Regex threat scanner detects instruction override, prompt leak attempts, SQL injection, and guardrail bypass attempts before dispatching prompts to LLM.
14. **CI/CD Pipeline & AI Evaluation Harness (Phase 8)**:
   - GitHub Actions 7-stage pipeline: lint → unit tests → integration tests → security tests → AI evaluations → frontend build → Docker build.
   - AI groundedness evaluations verify guardrails block hallucinated cell IDs, definitive claims are softened, RAG returns grounded 3GPP/O-RAN documents, and RCA evidence is deterministic.
   - Adversarial security evaluations test 22+ attack vectors (instruction override, prompt leak, SQL injection, guardrail bypass) with zero false negatives.
15. **Production Seed & Bootstrapper**:
   - `scripts/seed_production.py` provides single-command environment bootstrapping with baseline telemetry, alarms, incidents, and rApp policies.

## Useful Commands
- Run backend tests:
  `docker compose -f ranengineer/docker-compose.yml run --rm backend pytest -v`
- Run database migrations:
  `docker compose -f ranengineer/docker-compose.yml run --rm backend alembic -c app/alembic.ini upgrade head`
- Check running services:
  `docker compose -f ranengineer/docker-compose.yml ps`
- View live backend logs:
  `docker compose -f ranengineer/docker-compose.yml logs -f backend`

