import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Intent:
    name: str
    limit: int = 10
    target_id: str | None = None
    target_id_2: str | None = None
    kpi: str | None = None
    threshold: float | None = None
    direction: str | None = None


KPI_PATTERNS = {
    "rsrp": r"\brsrp\b",
    "rsrq": r"\brsrq\b",
    "sinr": r"\bsinr\b",
    "cqi": r"\bcqi\b",
    "dl_throughput": r"\b(?:dl[_\s-]?throughput|downlink|throughput)\b",
    "ul_throughput": r"\b(?:ul[_\s-]?throughput|uplink)\b",
    "prb_utilization": r"\b(?:prb[_\s-]?utilization|prb|utilization|congestion|congested)\b",
    "call_drop_rate": r"\b(?:call[_\s-]?drop[_\s-]?rate|call[_\s-]?drop|drop[_\s-]?rate|cdr)\b",
    "availability": r"\bavailability\b",
    "handover_success_rate": r"\b(?:handover|handover[_\s-]?success[_\s-]?rate|hosr)\b",
    "latency": r"\blatency\b",
    "packet_loss": r"\bpacket[_\s-]?loss\b",
}


def parse_intent(question: str) -> Intent:
    normalized = question.lower()

    # 1. Check for comparison between two cells e.g. "Compare CELL102 and CELL105"
    cell_matches = re.findall(r"\b(?!(?:cell|cells)\b)(?:cell|gnb|enb)[-_]?[a-zA-Z0-9]+\b", question, re.IGNORECASE)

    if len(cell_matches) >= 2 and any(t in normalized for t in ("compare", "vs", "versus", "between", "difference")):
        return Intent(
            name="compare_cells",
            target_id=cell_matches[0].upper(),
            target_id_2=cell_matches[1].upper(),
        )

    # 2. Extract cell ID if single cell mentioned e.g. "Why is CELL102 performing badly?"
    target_cell = cell_matches[0].upper() if cell_matches else None
    if target_cell and any(term in normalized for term in ("why", "how", "analyze", "issue", "status", "detail", "performance", "investigate", "cause")):
        return Intent(name="cell_analysis", limit=1, target_id=target_cell)

    # 3. Check for site-level questions e.g. "Which site has the worst performance?", "Which sites are congested?"
    if any(t in normalized for t in ("site", "sites")):
        site_matches = re.findall(r"\bsite[-_]?\w+\b", question, re.IGNORECASE)
        s1 = site_matches[0].upper() if site_matches else None
        s2 = site_matches[1].upper() if len(site_matches) > 1 else None
        return Intent(name="compare_sites", target_id=s1, target_id_2=s2)

    # 4. Check for KPI trends / statistics
    if any(t in normalized for t in ("trend", "distribution", "statistics", "average", "avg")):
        for kpi_name, pattern in KPI_PATTERNS.items():
            if re.search(pattern, normalized):
                return Intent(name="get_kpi_trend", kpi=kpi_name)
        return Intent(name="get_kpi_trend")

    # 5. Extract limit if specified e.g. "worst 5 cells", "top 10"
    limit = 10
    limit_match = re.search(r"\b(?:top|worst|first)?\s*(\d+)\b", normalized)
    if limit_match:
        try:
            parsed_limit = int(limit_match.group(1))
            if 1 <= parsed_limit <= 100:
                limit = parsed_limit
        except ValueError:
            pass

    # 6. Check for anomalies / outliers
    if any(term in normalized for term in ("anomal", "outlier")):
        return Intent(name="get_anomalies", limit=limit)

    # 7. Check for KPI threshold condition e.g. "SINR below 5", "RSRP < -105", "PRB above 90"
    for kpi_name, pattern in KPI_PATTERNS.items():
        if re.search(pattern, normalized):
            # Look for threshold value
            thresh_match = re.search(r"(?:below|under|less than|<|<=)\s*(-?\d+(?:\.\d+)?)", normalized)
            if thresh_match:
                return Intent(
                    name="filter_cells_by_kpi",
                    limit=limit,
                    kpi=kpi_name,
                    threshold=float(thresh_match.group(1)),
                    direction="lower",
                )
            thresh_above = re.search(r"(?:above|over|greater than|>|>=)\s*(-?\d+(?:\.\d+)?)", normalized)
            if thresh_above:
                return Intent(
                    name="filter_cells_by_kpi",
                    limit=limit,
                    kpi=kpi_name,
                    threshold=float(thresh_above.group(1)),
                    direction="higher",
                )
            if any(qual in normalized for qual in ("poor", "low", "high", "degraded", "bad")):
                return Intent(name="filter_cells_by_kpi", limit=limit, kpi=kpi_name)

    # 8. Check for bad / underperforming cells / engineering prioritization
    if any(term in normalized for term in ("bad", "worst", "critical", "underperform", "poor", "check first", "priority")):
        return Intent(name="find_bad_cells", limit=limit)

    # 9. Check for summary / overview / major issues
    if any(term in normalized for term in ("summary", "overview", "major issue", "kpi summary", "dataset", "health score", "healthy")):
        return Intent(name="dataset_summary")

    # Fallback if a cell was mentioned without explicit question keyword
    if target_cell:
        return Intent(name="cell_analysis", limit=1, target_id=target_cell)

    return Intent(name="unsupported")
