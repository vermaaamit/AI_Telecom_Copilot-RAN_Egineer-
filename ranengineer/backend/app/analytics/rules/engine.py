from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.analytics.rules.models import RanRule, RanRuleMatch, RuleEvaluationResult


def _find_rules_path() -> Path:
    # 1. Project-relative config path (from app/analytics/rules/engine.py -> repo root -> configs)
    candidate_1 = Path(__file__).resolve().parents[4] / "configs" / "rules" / "ran_rules.json"
    if candidate_1.exists():
        return candidate_1
    # 2. Container root mount path /configs/rules/ran_rules.json
    candidate_2 = Path("/configs/rules/ran_rules.json")
    if candidate_2.exists():
        return candidate_2
    # 3. Fallback to relative from current working directory
    candidate_3 = Path("configs/rules/ran_rules.json")
    if candidate_3.exists():
        return candidate_3
    return candidate_1


class RanRuleEngine:
    """Dedicated RAN Telecom Rule Engine for deterministic anomaly RCA."""

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or _find_rules_path()
        self._rules: list[RanRule] = self._load_rules()

    def _load_rules(self) -> list[RanRule]:
        if not self.config_path.exists():
            return []
        with self.config_path.open(encoding="utf-8") as f:
            data = json.load(f)
            rules_list = data.get("rules", [])
            return [RanRule(**r) for r in rules_list]

    @property
    def rules(self) -> list[RanRule]:
        return self._rules

    def get_rules_by_category(self, category: str) -> list[RanRule]:
        return [r for r in self._rules if r.category.lower() == category.lower()]

    def evaluate_cell(
        self,
        kpis: dict[str, float | None],
        kpi_statuses: dict[str, str],
        cell_id: str | None = None,
    ) -> RuleEvaluationResult:
        matched_rules: list[RanRuleMatch] = []

        for rule in self._rules:
            matched_kpis_for_rule: list[str] = []
            condition_results: list[bool] = []

            for cond in rule.conditions:
                kpi_status = kpi_statuses.get(cond.kpi, "UNKNOWN")
                status_matched = kpi_status in cond.threshold_status

                # Optional numeric threshold evaluation if threshold_value is provided
                val = kpis.get(cond.kpi)
                val_matched = True
                if cond.threshold_value is not None and val is not None:
                    if cond.operator == "<":
                        val_matched = val < cond.threshold_value
                    elif cond.operator == "<=":
                        val_matched = val <= cond.threshold_value
                    elif cond.operator == ">":
                        val_matched = val > cond.threshold_value
                    elif cond.operator == ">=":
                        val_matched = val >= cond.threshold_value
                    elif cond.operator == "==":
                        val_matched = val == cond.threshold_value

                cond_matched = status_matched and val_matched
                condition_results.append(cond_matched)
                if cond_matched:
                    matched_kpis_for_rule.append(cond.kpi)

            # Evaluate match mode
            rule_matched = False
            if rule.match_mode == "all" and condition_results:
                rule_matched = all(condition_results)
            elif rule.match_mode == "any" and condition_results:
                rule_matched = any(condition_results)

            if rule_matched:
                matched_rules.append(
                    RanRuleMatch(
                        rule_id=rule.rule_id,
                        name=rule.name,
                        category=rule.category,
                        severity=rule.severity,
                        matched_kpis=matched_kpis_for_rule,
                        explanation=rule.explanation,
                        recommended_checks=rule.recommended_checks,
                    )
                )

        # Build synthesized probable causes
        probable_causes_list: list[dict[str, Any]] = []
        for match in matched_rules:
            probable_causes_list.append(
                {
                    "rule_id": match.rule_id,
                    "category": match.category,
                    "severity": match.severity,
                    "probable_cause": f"Probable cause: {match.name} – {match.explanation}",
                    "recommended_checks": match.recommended_checks,
                }
            )

        # Primary issue is the most severe matched rule (CRITICAL prioritized over WARNING)
        primary_issue: str | None = None
        if matched_rules:
            critical_matches = [m for m in matched_rules if m.severity == "CRITICAL"]
            if critical_matches:
                primary_issue = critical_matches[0].name
            else:
                primary_issue = matched_rules[0].name

        return RuleEvaluationResult(
            cell_id=cell_id,
            matched_rules=matched_rules,
            probable_causes=probable_causes_list,
            primary_issue=primary_issue,
        )

    def get_probable_causes(
        self,
        kpi_statuses: dict[str, str],
        kpis: dict[str, float | None] | None = None,
    ) -> list[dict[str, Any]]:
        """Convenience method returning probable causes list adhering to Section 11 & 17."""
        res = self.evaluate_cell(kpis=kpis or {}, kpi_statuses=kpi_statuses)
        return res.probable_causes


@lru_cache
def get_rule_engine() -> RanRuleEngine:
    return RanRuleEngine()

