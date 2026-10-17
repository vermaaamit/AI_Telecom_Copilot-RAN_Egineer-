"""Dataset service for AI Telecom Copilot – RAN Engineer.

Orchestrates:
  CSV parsing → KPI analysis → health scoring → bad-cell detection → KPI degradation → probable RCA

ANALYTICS CALCULATES. RULES INTERPRET. AI EXPLAINS. ENGINEER DECIDES.
"""
from datetime import UTC, datetime
from uuid import uuid4

from app.analytics.anomaly.rules import probable_causes
from app.analytics.ingestion.csv_parser import ParsedCSV, parse_kpi_csv
from app.analytics.kpi.thresholds import classify_kpi
from app.analytics.scoring.health import calculate_health_score
from app.config.kpi_config import get_kpi_definitions


def _build_kpi_degradation(kpis: dict[str, float | None], kpi_statuses: dict[str, str]) -> list[dict[str, object]]:
    """Build structured KPI degradation list per cell.

    Each entry includes kpi, current_value, threshold, status, degradation direction, and severity.
    Only includes KPIs that are WARNING or CRITICAL (not HEALTHY).
    Historical trend data is not available; degradation is threshold-based only.
    """
    definitions = get_kpi_definitions()
    degradation: list[dict[str, object]] = []
    for kpi, status in kpi_statuses.items():
        if status not in ("WARNING", "CRITICAL"):
            continue
        defn = definitions.get(kpi)
        if not defn:
            continue
        value = kpis.get(kpi)
        direction = defn["direction"]
        # Determine degradation direction relative to normal
        degradation_dir = "DOWN" if direction == "higher_is_better" else "UP"
        degradation.append({
            "kpi": kpi.upper(),
            "current_value": value,
            "unit": defn.get("unit", ""),
            "threshold": defn["warning"] if status == "WARNING" else defn["good"],
            "status": status,
            "degradation": degradation_dir,
            "severity": status,
            "direction": direction,
        })
    return degradation


def analyse_dataset(content: bytes, filename: str, technology: str | None = None) -> dict[str, object]:
    """Parse CSV and compute health scores, KPI degradation, and probable RCA for each cell."""
    parsed: ParsedCSV = parse_kpi_csv(content)
    cells: list[dict[str, object]] = []

    for row in parsed.rows:
        score, status, issues, kpi_statuses = calculate_health_score(row["kpis"])
        kpi_degradation = _build_kpi_degradation(row["kpis"], kpi_statuses)
        cells.append({
            **row,
            "health_score": score,
            "status": status,
            "issues": issues,
            "kpi_statuses": kpi_statuses,
            "kpi_degradation": kpi_degradation,
            "probable_causes": probable_causes(kpi_statuses),
        })

    # Sort cells by health score ascending (lowest = worst first)
    cells.sort(key=lambda cell: cell["health_score"] if cell["health_score"] is not None else 101)

    counts = {s: sum(cell["status"] == s for cell in cells) for s in ("HEALTHY", "WARNING", "CRITICAL", "UNKNOWN")}
    known_scores = [cell["health_score"] for cell in cells if cell["health_score"] is not None]

    return {
        "id": str(uuid4()),
        "name": filename.rsplit(".", 1)[0],
        "filename": filename,
        "technology": technology,
        "created_at": datetime.now(UTC),
        "row_count": len(parsed.rows),
        "cell_count": len(cells),
        "available_kpis": list(parsed.mapped_columns),
        "unsupported_columns": parsed.unsupported_columns,
        "invalid_values": parsed.invalid_values,
        "cells": cells,
        "summary": {
            "total_cells": len(cells),
            "healthy_cells": counts["HEALTHY"],
            "warning_cells": counts["WARNING"],
            "critical_cells": counts["CRITICAL"],
            "unknown_cells": counts["UNKNOWN"],
            "average_health_score": round(sum(known_scores) / len(known_scores), 1) if known_scores else None,
        },
    }


def find_underperforming_cells(
    dataset: dict[str, object],
    limit: int = 10,
    status: str | None = None,
    kpi: str | None = None,
    site_id: str | None = None,
    technology: str | None = None,
) -> list[dict[str, object]]:
    """Return worst cells sorted by health score (ascending = worst first), with optional filters."""
    cells = list(dataset["cells"])
    # Cells are already sorted by health score from analyse_dataset.
    # Re-sort defensively in case dataset was loaded from DB without ordering.
    cells.sort(key=lambda cell: cell["health_score"] if cell.get("health_score") is not None else 101)

    if status:
        cells = [cell for cell in cells if cell["status"] == status.upper()]
    if kpi:
        cells = [cell for cell in cells if cell["kpi_statuses"].get(kpi) in {"WARNING", "CRITICAL"}]
    if site_id:
        cells = [cell for cell in cells if cell["site_id"] == site_id]
    if technology:
        cells = [cell for cell in cells if cell["technology"] == technology]

    return cells[:limit]
