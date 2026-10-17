# AI Telecom Copilot – Operational & Development Rules

## 1. Development Principles
1. **Analytics Calculates**: All KPI values, health scores, and mathematical aggregations must be computed deterministically in Python/SQL. The LLM must NEVER compute or invent values.
2. **Rules Interpret**: Anomalies, degradation states, and root causes are derived from expert telecom rules (`ran_rules.json`).
3. **AI Explains**: Generative AI tools strictly formulate readable explanations of deterministic findings.
4. **Engineer Decides**: All system outputs are presented as *probable causes* or *recommendations*, never definitive unverified facts. Engineers make the operational decisions.

## 2. API & Data Guardrails
- **Zero Hallucination Guarantee**: Any entity (cell ID, site ID, KPI metric) mentioned in a copilot response must strictly be grounded in the active dataset.
- **Definitive Claims Rule**: The copilot must never claim "the root cause is X". It must state "probable cause based on telemetry is X".
- **Security Scanners**: Every uploaded file must undergo antivirus/malware signature inspection. Malicious files must be rejected with HTTP 400 and trigger a CRITICAL security alarm.
- **Database Consistency**: All schema modifications must be implemented using Alembic migrations with version history.

## 3. Telemetry & Root Cause Rules
- **Coverage & Interference**: Triggered when `RSRP < -110 dBm` and `SINR < 0 dB`.
- **Congestion & Capacity**: Triggered when `PRB_UTILIZATION > 85%` and downlink throughput is degraded.
- **Mobility & Handover**: Triggered when `HANDOVER_SUCCESS_RATE < 95%`.
- **Cell Outage**: Triggered when `AVAILABILITY < 90%` or traffic abruptly drops to zero.
- **Alarm Correlation**:
  - `HIGH`: Direct cell ID match + active alarm matching degraded KPI domain.
  - `MEDIUM`: Site-level match + alarm matching degraded KPI domain.
  - `LOW`: Co-located site alarm without direct KPI domain match.

