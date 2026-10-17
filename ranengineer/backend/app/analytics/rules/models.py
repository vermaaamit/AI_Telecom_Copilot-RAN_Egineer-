from typing import Any, Literal
from pydantic import BaseModel, Field


class RuleCondition(BaseModel):
    kpi: str
    operator: str = Field(default="<", description="Comparison operator or threshold evaluation")
    threshold_status: list[str] = Field(default_factory=lambda: ["WARNING", "CRITICAL"])
    threshold_value: float | None = None


class RanRule(BaseModel):
    rule_id: str
    name: str
    category: str
    conditions: list[RuleCondition]
    match_mode: Literal["all", "any"] = "all"
    severity: Literal["CRITICAL", "WARNING", "INFO"] = "WARNING"
    explanation: str
    recommended_checks: list[str]


class RanRuleMatch(BaseModel):
    rule_id: str
    name: str
    category: str
    severity: str
    matched_kpis: list[str]
    explanation: str
    recommended_checks: list[str]


class RuleEvaluationResult(BaseModel):
    cell_id: str | None = None
    matched_rules: list[RanRuleMatch]
    probable_causes: list[dict[str, Any]]
    primary_issue: str | None = None

