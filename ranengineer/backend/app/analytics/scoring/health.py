from app.analytics.kpi.thresholds import classify_kpi
from app.config.kpi_config import get_kpi_definitions

STATUS_POINTS = {"HEALTHY": 100, "WARNING": 55, "CRITICAL": 10}


def calculate_health_score(kpis: dict[str, float | None]) -> tuple[int | None, str, list[str], dict[str, str]]:
    definitions = get_kpi_definitions()
    weighted_points = 0.0
    available_weight = 0.0
    issues: list[str] = []
    statuses: dict[str, str] = {}
    for kpi, value in kpis.items():
        if value is None or kpi not in definitions:
            continue
        status = classify_kpi(kpi, value)
        statuses[kpi] = status
        weight = definitions[kpi]["weight"]
        weighted_points += STATUS_POINTS[status] * weight
        available_weight += weight
        if status != "HEALTHY":
            issues.append(f"{status}_{kpi.upper()}")
    if not available_weight:
        return None, "UNKNOWN", [], statuses
    score = round(weighted_points / available_weight)
    status = "HEALTHY" if score >= 80 else "WARNING" if score >= 50 else "CRITICAL"
    return score, status, issues, statuses
