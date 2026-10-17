from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    KPI_ANALYST = "KPI_ANALYST"
    ANOMALY_DETECTOR = "ANOMALY_DETECTOR"
    RCA_SPECIALIST = "RCA_SPECIALIST"
    STANDARDS_ENGINEER = "STANDARDS_ENGINEER"
    OPTIMIZATION_ENGINEER = "OPTIMIZATION_ENGINEER"
    SYNTHESIS_REPORTER = "SYNTHESIS_REPORTER"


class AgentContribution(BaseModel):
    role: AgentRole
    agent_name: str
    status: str = "COMPLETED"
    findings: list[str] = Field(default_factory=list)
    metrics_evaluated: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)


class MultiAgentInvestigationReport(BaseModel):
    investigation_id: str
    target_cell_id: str
    target_site_id: str | None = None
    health_score: int | None = None
    overall_verdict: str
    agent_contributions: list[AgentContribution] = Field(default_factory=list)
    consolidated_remediations: list[str] = Field(default_factory=list)
    standards_references: list[str] = Field(default_factory=list)
    engineer_disclaimer: str = (
        "Multi-Agent investigation coordinated across deterministic analytical agents. "
        "Engineers must review physical site conditions before executing parameter modifications."
    )

