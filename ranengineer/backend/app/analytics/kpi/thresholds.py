from dataclasses import dataclass
from enum import Enum
from app.config.kpi_config import get_kpi_definitions


class KpiDirection(str, Enum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


@dataclass
class KpiThresholds:
    good: float
    warning: float
    critical: float
    direction: KpiDirection


def _find_kpi_def(kpi: str) -> dict | None:
    definitions = get_kpi_definitions()
    norm = kpi.strip().lower()
    if norm in definitions:
        return definitions[norm]
    # Check aliases
    for name, d in definitions.items():
        if norm == name or norm in [a.lower() for a in d.get("aliases", [])]:
            return d
    # Match through common aliases
    alias_map = {
        "prb_utilization": "prb_utilization",
        "throughput_dl": "dl_throughput",
        "throughput_ul": "ul_throughput",
        "cqi": "cqi",
        "sinr": "sinr",
        "rsrp": "rsrp",
        "rsrq": "rsrq",
        "call_drop_rate": "call_drop_rate",
        "handover_success_rate": "handover_success_rate",
        "availability": "availability",
        "latency": "latency",
        "packet_loss": "packet_loss",
    }
    mapped_name = alias_map.get(norm)
    if mapped_name and mapped_name in definitions:
        return definitions[mapped_name]
    return None


def get_kpi_direction(kpi: str) -> KpiDirection:
    kpi_def = _find_kpi_def(kpi)
    if kpi_def and kpi_def.get("direction") == "lower_is_better":
        return KpiDirection.LOWER_IS_BETTER
    return KpiDirection.HIGHER_IS_BETTER


def get_kpi_thresholds(kpi: str) -> KpiThresholds | None:
    kpi_def = _find_kpi_def(kpi)
    if not kpi_def:
        return None
    direction = (
        KpiDirection.LOWER_IS_BETTER
        if kpi_def.get("direction") == "lower_is_better"
        else KpiDirection.HIGHER_IS_BETTER
    )
    good = float(kpi_def.get("good", 0.0))
    warning = float(kpi_def.get("warning", 0.0))
    # In classify_kpi, exceeding or falling below 'warning' is classified as CRITICAL
    critical = warning
    return KpiThresholds(good=good, warning=good, critical=critical, direction=direction)


def classify_kpi(kpi: str, value: float) -> str:
    kpi_def = _find_kpi_def(kpi)
    if not kpi_def:
        return "UNKNOWN"
    if kpi_def["direction"] == "higher_is_better":
        if value >= kpi_def["good"]:
            return "HEALTHY"
        if value >= kpi_def["warning"]:
            return "WARNING"
    else:
        if value < kpi_def["good"]:
            return "HEALTHY"
        if value < kpi_def["warning"]:
            return "WARNING"
    return "CRITICAL"
