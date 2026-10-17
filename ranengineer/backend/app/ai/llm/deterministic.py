from typing import Any
from app.ai.llm.provider import LLMProvider


class DeterministicLLMProvider(LLMProvider):
    """Deterministic RAN engineering explanation generator that strictly respects Section 35 response schema."""

    def explain(self, question: str, evidence: dict[str, Any]) -> str:
        intent = evidence.get("intent", "unsupported")

        if intent == "find_bad_cells":
            items = evidence.get("items", [])
            if not items:
                return (
                    "Summary:\nNo cells matched the underperformance criteria in this dataset.\n\n"
                    "Affected Cells:\nNone.\n\n"
                    "Limitations:\nAnalysis is based strictly on the uploaded KPI measurements."
                )

            crit_count = sum(1 for c in items if c.get("status") == "CRITICAL")
            warn_count = sum(1 for c in items if c.get("status") == "WARNING")
            summary = f"{len(items)} cells identified with degraded performance ({crit_count} Critical, {warn_count} Warning)."

            affected = "\n".join(f"- {c['cell_id']} (Site: {c.get('site_id') or 'N/A'}, Health Score: {c.get('health_score')}/100, Status: {c.get('status')})" for c in items)

            kpi_evidence = []
            for c in items[:5]:
                issues_str = ", ".join(c.get("issues", [])) or "Degraded health score"
                kpi_evidence.append(f"{c['cell_id']}: {issues_str}")
            evidence_str = "\n".join(kpi_evidence)

            causes_set = set()
            checks_set = set()
            for c in items:
                for cause in c.get("probable_causes", []):
                    causes_set.add(cause.get("probable_cause", ""))
                    for check in cause.get("recommended_checks", []):
                        checks_set.add(check)

            causes_str = "\n".join(f"- {cause}" for cause in sorted(causes_set)) or "- Insufficient threshold combinations to determine specific probable causes."
            checks_str = "\n".join(f"{i+1}. {check}" for i, check in enumerate(sorted(checks_set)[:6])) or "1. Monitor busy-hour KPIs.\n2. Review radio alarms."

            return (
                f"Summary:\n{summary}\n\n"
                f"Affected Cells:\n{affected}\n\n"
                f"KPI Evidence:\n{evidence_str}\n\n"
                f"Probable Causes:\n{causes_str}\n\n"
                f"Recommended Checks:\n{checks_str}\n\n"
                f"Limitations:\nEvaluated deterministically from the uploaded dataset. Probable causes are rule-based engineering interpretations, not confirmed physical faults."
            )

        if intent == "cell_analysis":
            cell = evidence.get("cell")
            if not cell:
                return (
                    f"Summary:\nThe requested cell was not found in the dataset.\n\n"
                    f"Limitations:\nAnalysis is restricted to cells available in the uploaded dataset."
                )

            cid = cell.get("cell_id", "Unknown")
            status = cell.get("status", "UNKNOWN")
            score = cell.get("health_score", "N/A")
            site = cell.get("site_id", "N/A")
            tech = cell.get("technology", "N/A")

            summary = f"Cell {cid} (Site {site}, {tech}) is operating with health score {score}/100 and classified as {status}."
            affected = f"- {cid}"

            kpis = cell.get("kpis", {})
            kpi_lines = [f"- {k.upper()}: {v} ({cell.get('kpi_statuses', {}).get(k, 'UNKNOWN')})" for k, v in kpis.items() if v is not None]
            evidence_str = "\n".join(kpi_lines) if kpi_lines else "- No measured KPI values recorded."

            causes = cell.get("probable_causes", [])
            causes_str = "\n".join(f"- {c['probable_cause']}" for c in causes) if causes else "- No rule-based probable cause identified for current KPI combination."

            checks = [check for c in causes for check in c.get("recommended_checks", [])]
            checks_str = "\n".join(f"{i+1}. {chk}" for i, chk in enumerate(checks)) if checks else "1. Inspect transmission status.\n2. Verify neighbor cell handovers."

            return (
                f"Summary:\n{summary}\n\n"
                f"Affected Cells:\n{affected}\n\n"
                f"KPI Evidence:\n{evidence_str}\n\n"
                f"Probable Causes:\n{causes_str}\n\n"
                f"Recommended Checks:\n{checks_str}\n\n"
                f"Limitations:\nInferences are derived from configured threshold rules. Additional field or alarm confirmation is recommended."
            )

        if intent == "dataset_summary":
            sum_data = evidence.get("summary", {})
            total = sum_data.get("total_cells", 0)
            healthy = sum_data.get("healthy_cells", 0)
            warning = sum_data.get("warning_cells", 0)
            critical = sum_data.get("critical_cells", 0)
            avg_score = sum_data.get("average_health_score", "N/A")
            avail = ", ".join(evidence.get("available_kpis", [])) or "None"

            return (
                f"Summary:\nAnalysis of dataset containing {total} cells: {healthy} healthy, {warning} warning, and {critical} critical. Average network health score is {avg_score}/100.\n\n"
                f"KPI Evidence:\nAvailable KPIs: {avail}.\n\n"
                f"Probable Causes:\n- Network health is driven by available radio, capacity, and mobility KPIs.\n\n"
                f"Recommended Checks:\n1. Investigate the {critical} critical cells first.\n2. Check PRB utilization and RSRP degradation across warning cells.\n\n"
                f"Limitations:\nSummary aggregates only available columns; missing KPIs were not factored into scoring."
            )

        if intent == "filter_cells_by_kpi":
            kpi = evidence.get("kpi", "KPI")
            items = evidence.get("items", [])
            total = evidence.get("total_matched", len(items))
            if not items:
                return (
                    f"Summary:\nNo cells with degraded {kpi} were detected.\n\n"
                    f"Limitations:\nBased strictly on configured thresholds."
                )

            summary = f"{total} cells exhibit degraded {kpi} (showing top {len(items)} lowest scoring cells)."
            affected = "\n".join(f"- {c['cell_id']} ({kpi}: {c.get('kpi_value')}, Health Score: {c.get('health_score')})" for c in items)

            return (
                f"Summary:\n{summary}\n\n"
                f"Affected Cells:\n{affected}\n\n"
                f"KPI Evidence:\nCells breached {kpi} warning or critical thresholds.\n\n"
                f"Probable Causes:\n- {kpi.upper()} degradation directly impacts radio link quality or throughput performance.\n\n"
                f"Recommended Checks:\n1. Check interference levels and antenna tilt.\n2. Verify neighbor cell handovers.\n\n"
                f"Limitations:\nThreshold boundaries are defined in KPI configuration."
            )

        if intent == "compare_cells":
            c1 = evidence.get("cell_1", {})
            c2 = evidence.get("cell_2", {})
            better = evidence.get("better_performing")
            comp = evidence.get("kpi_comparison", {})

            lines = []
            for k, val in list(comp.items())[:6]:
                lines.append(f"- {k.upper()}: {c1.get('cell_id')}={val.get(c1.get('cell_id'))} vs {c2.get('cell_id')}={val.get(c2.get('cell_id'))}")
            evidence_str = "\n".join(lines) if lines else "- Insufficient KPI overlap."

            return (
                f"Summary:\nComparison between {c1.get('cell_id')} (Score: {c1.get('health_score')}) and {c2.get('cell_id')} (Score: {c2.get('health_score')}). Cell {better} is performing better overall.\n\n"
                f"Affected Cells:\n- {c1.get('cell_id')} ({c1.get('status')})\n- {c2.get('cell_id')} ({c2.get('status')})\n\n"
                f"KPI Evidence:\n{evidence_str}\n\n"
                f"Probable Causes:\n- Performance variance between cells often relates to coverage geometry, antenna tilt, or traffic loading.\n\n"
                f"Recommended Checks:\n1. Align carrier parameters between the two cells.\n2. Inspect site interference profiles.\n\n"
                f"Limitations:\nDirect comparison is based on the single snapshot of KPI data."
            )

        if intent == "compare_sites":
            worst = evidence.get("worst_sites", [])
            total = evidence.get("total_sites", len(worst))
            summary = f"Evaluated {total} sites across the network."
            affected = "\n".join(f"- Site {s['site_id']}: Avg Health Score {s.get('average_health_score')}/100, {s.get('critical_cells')} critical cells" for s in worst)

            return (
                f"Summary:\n{summary}\n\n"
                f"Affected Cells:\n{affected}\n\n"
                f"KPI Evidence:\nSites ranked by aggregated health score.\n\n"
                f"Probable Causes:\n- Sites with low average health scores typically suffer from backhaul constraints or localized RF interference.\n\n"
                f"Recommended Checks:\n1. Check transmission utilization at top underperforming sites.\n2. Inspect sector power amplifiers and feeder lines.\n\n"
                f"Limitations:\nSite metrics represent average cell metrics from the dataset."
            )

        if intent == "get_anomalies":
            items = evidence.get("items", [])
            total = evidence.get("total_anomalies", len(items))
            summary = f"{total} severe cell anomalies identified with critical KPI threshold violations."
            affected = "\n".join(f"- {c['cell_id']} (Health Score: {c.get('health_score')}/100, Status: {c.get('status')})" for c in items)

            return (
                f"Summary:\n{summary}\n\n"
                f"Affected Cells:\n{affected}\n\n"
                f"KPI Evidence:\nSevere threshold degradation in one or more radio/capacity KPIs.\n\n"
                f"Probable Causes:\n- Radio equipment failure, severe inter-cell interference, or capacity saturation.\n\n"
                f"Recommended Checks:\n1. Dispatch field technician if hardware alarms coincide.\n2. Review sector antenna orientation and VSWR.\n\n"
                f"Limitations:\nAnomalies are detected via deterministic threshold rules."
            )

        return (
            "Summary:\nUnable to process question directly with existing analytics tools.\n\n"
            "Recommended Checks:\nAsk about underperforming cells ('Which cells are performing badly?'), request a cell analysis ('Why is CELL102 performing badly?'), compare cells, or request a KPI summary.\n\n"
            "Limitations:\nOnly controlled telecom analytics queries are supported."
        )

