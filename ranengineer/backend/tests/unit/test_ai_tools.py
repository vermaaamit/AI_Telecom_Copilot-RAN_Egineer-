from app.ai.tools.analytics_tools import (
    compare_cells,
    compare_sites,
    execute_intent,
    filter_cells_by_kpi,
    find_bad_cells,
    get_anomalies,
    get_cell_analysis,
    get_dataset_summary,
    get_kpi_trend,
)

SAMPLE_DATASET = {
    "id": "ds-test-123",
    "name": "test_network",
    "filename": "test_network.csv",
    "technology": "4G/5G",
    "summary": {
        "total_cells": 3,
        "healthy_cells": 1,
        "warning_cells": 1,
        "critical_cells": 1,
        "average_health_score": 62.0,
    },
    "available_kpis": ["rsrp", "sinr", "dl_throughput", "prb_utilization"],
    "cells": [
        {
            "cell_id": "CELL102",
            "site_id": "SITE10",
            "technology": "4G",
            "health_score": 28,
            "status": "CRITICAL",
            "kpis": {"rsrp": -118, "sinr": 2, "dl_throughput": 2.0, "prb_utilization": 96.0},
            "kpi_statuses": {"rsrp": "CRITICAL", "sinr": "CRITICAL", "dl_throughput": "CRITICAL", "prb_utilization": "CRITICAL"},
            "issues": ["CRITICAL_RSRP", "CRITICAL_SINR"],
            "probable_causes": [{"probable_cause": "Coverage degradation or interference", "recommended_checks": ["Check radio alarms"]}],
        },
        {
            "cell_id": "CELL105",
            "site_id": "SITE10",
            "technology": "4G",
            "health_score": 92,
            "status": "HEALTHY",
            "kpis": {"rsrp": -85, "sinr": 22, "dl_throughput": 55.0, "prb_utilization": 35.0},
            "kpi_statuses": {"rsrp": "HEALTHY", "sinr": "HEALTHY", "dl_throughput": "HEALTHY", "prb_utilization": "HEALTHY"},
            "issues": [],
            "probable_causes": [],
        },
        {
            "cell_id": "CELL201",
            "site_id": "SITE20",
            "technology": "5G",
            "health_score": 66,
            "status": "WARNING",
            "kpis": {"rsrp": -98, "sinr": 9, "dl_throughput": 12.0, "prb_utilization": 75.0},
            "kpi_statuses": {"rsrp": "WARNING", "sinr": "WARNING", "dl_throughput": "WARNING", "prb_utilization": "WARNING"},
            "issues": ["WARNING_RSRP"],
            "probable_causes": [],
        },
    ],
}


def test_tool_get_dataset_summary() -> None:
    res = get_dataset_summary(SAMPLE_DATASET)
    assert res["dataset_id"] == "ds-test-123"
    assert res["summary"]["total_cells"] == 3
    assert "rsrp" in res["available_kpis"]


def test_tool_find_bad_cells() -> None:
    res = find_bad_cells(SAMPLE_DATASET, limit=2)
    assert len(res["items"]) == 2
    assert res["items"][0]["cell_id"] == "CELL102"
    assert res["items"][0]["status"] == "CRITICAL"


def test_tool_get_cell_analysis() -> None:
    res = get_cell_analysis(SAMPLE_DATASET, "CELL102")
    assert "cell" in res
    assert res["cell"]["cell_id"] == "CELL102"
    assert res["cell"]["health_score"] == 28
    assert len(res["cell"]["probable_causes"]) == 1

    missing = get_cell_analysis(SAMPLE_DATASET, "NON_EXISTENT")
    assert "error" in missing


def test_tool_filter_cells_by_kpi() -> None:
    res = filter_cells_by_kpi(SAMPLE_DATASET, kpi="sinr", threshold=5.0, direction="lower")
    assert len(res["items"]) == 1
    assert res["items"][0]["cell_id"] == "CELL102"


def test_tool_compare_cells() -> None:
    res = compare_cells(SAMPLE_DATASET, "CELL102", "CELL105")
    assert res["better_performing"] == "CELL105"
    assert "rsrp" in res["kpi_comparison"]
    assert res["kpi_comparison"]["rsrp"]["CELL102"] == -118
    assert res["kpi_comparison"]["rsrp"]["CELL105"] == -85


def test_tool_compare_sites() -> None:
    res = compare_sites(SAMPLE_DATASET)
    assert res["total_sites"] == 2
    assert len(res["worst_sites"]) == 2


def test_tool_get_anomalies() -> None:
    res = get_anomalies(SAMPLE_DATASET)
    assert res["total_anomalies"] == 1
    assert res["items"][0]["cell_id"] == "CELL102"


def test_tool_get_kpi_trend() -> None:
    res = get_kpi_trend(SAMPLE_DATASET, kpi="rsrp")
    assert "rsrp" in res["kpi_statistics"]
    assert res["kpi_statistics"]["rsrp"]["min"] == -118
    assert res["kpi_statistics"]["rsrp"]["max"] == -85


def test_execute_intent_dispatcher() -> None:
    res = execute_intent(SAMPLE_DATASET, "find_bad_cells", limit=1)
    assert res["intent"] == "find_bad_cells"
    assert len(res["items"]) == 1

