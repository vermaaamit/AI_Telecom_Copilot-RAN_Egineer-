from typing import Any
from app.services.dataset_service import find_underperforming_cells


def get_dataset_summary(dataset: dict[str, Any]) -> dict[str, Any]:
    return {
        "dataset_id": dataset["id"],
        "name": dataset.get("name"),
        "filename": dataset.get("filename"),
        "technology": dataset.get("technology"),
        "summary": dataset["summary"],
        "available_kpis": dataset.get("available_kpis", []),
        "unsupported_columns": dataset.get("unsupported_columns", []),
        "invalid_values_count": len(dataset.get("invalid_values", [])),
    }


def find_bad_cells(dataset: dict[str, Any], limit: int = 10, status: str | None = None, kpi: str | None = None, site_id: str | None = None, technology: str | None = None) -> dict[str, Any]:
    cells = find_underperforming_cells(dataset, limit=limit, status=status, kpi=kpi, site_id=site_id, technology=technology)
    return {
        "dataset_id": dataset["id"],
        "total_matched": len(cells),
        "limit": limit,
        "items": [
            {
                "cell_id": cell["cell_id"],
                "site_id": cell.get("site_id"),
                "technology": cell.get("technology"),
                "health_score": cell.get("health_score"),
                "status": cell.get("status"),
                "issues": cell.get("issues", []),
                "probable_causes": cell.get("probable_causes", []),
            }
            for cell in cells
        ],
    }


def get_cell_analysis(dataset: dict[str, Any], cell_id: str) -> dict[str, Any]:
    target = next((c for c in dataset.get("cells", []) if c["cell_id"].upper() == cell_id.upper()), None)
    if not target:
        return {"dataset_id": dataset["id"], "error": f"Cell {cell_id} not found in dataset."}
    return {
        "dataset_id": dataset["id"],
        "cell": {
            "cell_id": target["cell_id"],
            "site_id": target.get("site_id"),
            "technology": target.get("technology"),
            "health_score": target.get("health_score"),
            "status": target.get("status"),
            "kpis": target.get("kpis", {}),
            "kpi_statuses": target.get("kpi_statuses", {}),
            "issues": target.get("issues", []),
            "probable_causes": target.get("probable_causes", []),
        },
    }


def filter_cells_by_kpi(dataset: dict[str, Any], kpi: str, threshold: float | None = None, direction: str | None = None, limit: int = 10) -> dict[str, Any]:
    cells = dataset.get("cells", [])
    matched = []
    for cell in cells:
        val = cell.get("kpis", {}).get(kpi)
        if val is None:
            continue
        if threshold is not None:
            if direction == "lower" and val < threshold:
                matched.append(cell)
            elif direction == "higher" and val > threshold:
                matched.append(cell)
            elif val <= threshold:
                matched.append(cell)
        else:
            if cell.get("kpi_statuses", {}).get(kpi) in {"WARNING", "CRITICAL"}:
                matched.append(cell)

    matched.sort(key=lambda c: c.get("health_score") if c.get("health_score") is not None else 101)
    items = matched[:limit]
    return {
        "dataset_id": dataset["id"],
        "kpi": kpi,
        "total_matched": len(matched),
        "items": [
            {
                "cell_id": cell["cell_id"],
                "site_id": cell.get("site_id"),
                "health_score": cell.get("health_score"),
                "kpi_value": cell.get("kpis", {}).get(kpi),
                "kpi_status": cell.get("kpi_statuses", {}).get(kpi),
                "status": cell.get("status"),
            }
            for cell in items
        ],
    }


def compare_cells(dataset: dict[str, Any], cell_id_1: str, cell_id_2: str) -> dict[str, Any]:
    c1 = next((c for c in dataset.get("cells", []) if c["cell_id"].upper() == cell_id_1.upper()), None)
    c2 = next((c for c in dataset.get("cells", []) if c["cell_id"].upper() == cell_id_2.upper()), None)
    if not c1 or not c2:
        missing = []
        if not c1:
            missing.append(cell_id_1)
        if not c2:
            missing.append(cell_id_2)
        return {"dataset_id": dataset["id"], "error": f"Cells not found: {', '.join(missing)}"}

    kpi_comparison = {}
    all_kpis = set(c1.get("kpis", {}).keys()) | set(c2.get("kpis", {}).keys())
    for k in sorted(all_kpis):
        kpi_comparison[k] = {
            cell_id_1: c1.get("kpis", {}).get(k),
            f"{cell_id_1}_status": c1.get("kpi_statuses", {}).get(k),
            cell_id_2: c2.get("kpis", {}).get(k),
            f"{cell_id_2}_status": c2.get("kpi_statuses", {}).get(k),
        }

    better = cell_id_1 if (c1.get("health_score") or 0) > (c2.get("health_score") or 0) else cell_id_2
    return {
        "dataset_id": dataset["id"],
        "cell_1": {"cell_id": c1["cell_id"], "health_score": c1.get("health_score"), "status": c1.get("status")},
        "cell_2": {"cell_id": c2["cell_id"], "health_score": c2.get("health_score"), "status": c2.get("status")},
        "kpi_comparison": kpi_comparison,
        "better_performing": better,
    }


def compare_sites(dataset: dict[str, Any], site_id_1: str | None = None, site_id_2: str | None = None) -> dict[str, Any]:
    cells = dataset.get("cells", [])
    site_groups: dict[str, list[dict[str, Any]]] = {}
    for cell in cells:
        sid = cell.get("site_id") or "UNKNOWN_SITE"
        site_groups.setdefault(sid, []).append(cell)

    site_stats = []
    for sid, s_cells in site_groups.items():
        scores = [c["health_score"] for c in s_cells if c.get("health_score") is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else None
        critical_count = sum(1 for c in s_cells if c.get("status") == "CRITICAL")
        site_stats.append({
            "site_id": sid,
            "cell_count": len(s_cells),
            "average_health_score": avg_score,
            "critical_cells": critical_count,
        })

    site_stats.sort(key=lambda s: s["average_health_score"] if s["average_health_score"] is not None else 101)

    if site_id_1 and site_id_2:
        s1 = next((s for s in site_stats if s["site_id"].upper() == site_id_1.upper()), None)
        s2 = next((s for s in site_stats if s["site_id"].upper() == site_id_2.upper()), None)
        return {"dataset_id": dataset["id"], "sites": [s for s in (s1, s2) if s]}

    return {
        "dataset_id": dataset["id"],
        "worst_sites": site_stats[:5],
        "total_sites": len(site_stats),
    }


def get_anomalies(dataset: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    critical_cells = [c for c in dataset.get("cells", []) if c.get("status") == "CRITICAL"]
    critical_cells.sort(key=lambda c: c.get("health_score") if c.get("health_score") is not None else 101)
    items = critical_cells[:limit]
    return {
        "dataset_id": dataset["id"],
        "total_anomalies": len(critical_cells),
        "items": [
            {
                "cell_id": cell["cell_id"],
                "site_id": cell.get("site_id"),
                "health_score": cell.get("health_score"),
                "status": cell.get("status"),
                "issues": cell.get("issues", []),
                "probable_causes": cell.get("probable_causes", []),
            }
            for cell in items
        ],
    }


def get_kpi_trend(dataset: dict[str, Any], kpi: str | None = None) -> dict[str, Any]:
    cells = dataset.get("cells", [])
    target_kpis = [kpi] if kpi else dataset.get("available_kpis", [])
    stats = {}
    for k in target_kpis:
        vals = [c.get("kpis", {}).get(k) for c in cells if c.get("kpis", {}).get(k) is not None]
        if vals:
            stats[k] = {
                "count": len(vals),
                "min": min(vals),
                "max": max(vals),
                "avg": round(sum(vals) / len(vals), 2),
            }
    return {
        "dataset_id": dataset["id"],
        "kpi_statistics": stats,
    }


def execute_intent(dataset: dict[str, Any], intent_name: str, limit: int = 10, target_id: str | None = None, target_id_2: str | None = None, kpi: str | None = None, threshold: float | None = None, direction: str | None = None) -> dict[str, Any]:
    if intent_name == "find_bad_cells":
        res = find_bad_cells(dataset, limit=limit, kpi=kpi)
        res["intent"] = intent_name
        return res
    if intent_name == "dataset_summary":
        res = get_dataset_summary(dataset)
        res["intent"] = intent_name
        return res
    if intent_name == "cell_analysis":
        tid = target_id or (dataset.get("cells", [{}])[0].get("cell_id", "") if dataset.get("cells") else "")
        res = get_cell_analysis(dataset, tid)
        res["intent"] = intent_name
        return res
    if intent_name == "filter_cells_by_kpi":
        res = filter_cells_by_kpi(dataset, kpi=kpi or "rsrp", threshold=threshold, direction=direction, limit=limit)
        res["intent"] = intent_name
        return res
    if intent_name == "compare_cells":
        res = compare_cells(dataset, target_id or "", target_id_2 or "")
        res["intent"] = intent_name
        return res
    if intent_name == "compare_sites":
        res = compare_sites(dataset, site_id_1=target_id, site_id_2=target_id_2)
        res["intent"] = intent_name
        return res
    if intent_name == "get_anomalies":
        res = get_anomalies(dataset, limit=limit)
        res["intent"] = intent_name
        return res
    if intent_name == "get_kpi_trend":
        res = get_kpi_trend(dataset, kpi=kpi)
        res["intent"] = intent_name
        return res
    return {"intent": "unsupported", "dataset_id": dataset["id"], "items": []}
