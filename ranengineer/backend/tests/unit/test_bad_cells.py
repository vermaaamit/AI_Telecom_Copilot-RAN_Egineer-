from app.services.dataset_service import find_underperforming_cells

SAMPLE_DATASET = {
    "cells": [
        {"cell_id": "CELL_01", "site_id": "SITE_A", "technology": "4G", "health_score": 25, "status": "CRITICAL", "kpi_statuses": {"rsrp": "CRITICAL", "sinr": "CRITICAL"}},
        {"cell_id": "CELL_02", "site_id": "SITE_A", "technology": "5G", "health_score": 40, "status": "CRITICAL", "kpi_statuses": {"prb_utilization": "CRITICAL"}},
        {"cell_id": "CELL_03", "site_id": "SITE_B", "technology": "4G", "health_score": 60, "status": "WARNING", "kpi_statuses": {"rsrp": "WARNING"}},
        {"cell_id": "CELL_04", "site_id": "SITE_B", "technology": "5G", "health_score": 85, "status": "HEALTHY", "kpi_statuses": {}},
    ]
}


def test_find_underperforming_cells_limit() -> None:
    cells = find_underperforming_cells(SAMPLE_DATASET, limit=2)
    assert len(cells) == 2
    assert cells[0]["cell_id"] == "CELL_01"
    assert cells[1]["cell_id"] == "CELL_02"


def test_filter_by_status() -> None:
    critical = find_underperforming_cells(SAMPLE_DATASET, status="CRITICAL")
    assert len(critical) == 2
    assert all(c["status"] == "CRITICAL" for c in critical)

    warning = find_underperforming_cells(SAMPLE_DATASET, status="WARNING")
    assert len(warning) == 1
    assert warning[0]["cell_id"] == "CELL_03"


def test_filter_by_kpi() -> None:
    prb_cells = find_underperforming_cells(SAMPLE_DATASET, kpi="prb_utilization")
    assert len(prb_cells) == 1
    assert prb_cells[0]["cell_id"] == "CELL_02"

    rsrp_cells = find_underperforming_cells(SAMPLE_DATASET, kpi="rsrp")
    assert len(rsrp_cells) == 2


def test_filter_by_site_and_technology() -> None:
    site_a = find_underperforming_cells(SAMPLE_DATASET, site_id="SITE_A")
    assert len(site_a) == 2

    tech_5g = find_underperforming_cells(SAMPLE_DATASET, technology="5G")
    assert len(tech_5g) == 2

