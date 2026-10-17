from app.analytics.scoring.health import calculate_health_score


def test_critical_radio_and_capacity_values_produce_critical_score() -> None:
    score, status, issues, statuses = calculate_health_score({"rsrp": -116, "sinr": 3, "dl_throughput": 2, "prb_utilization": 97})
    assert score is not None and score < 50
    assert status == "CRITICAL"
    assert "CRITICAL_RSRP" in issues
    assert statuses["prb_utilization"] == "CRITICAL"


def test_healthy_kpis_produce_healthy_score() -> None:
    score, status, issues, statuses = calculate_health_score({
        "rsrp": -80, "sinr": 20, "dl_throughput": 50, "prb_utilization": 40, "availability": 99.9, "call_drop_rate": 0.2
    })
    assert score is not None and score >= 80
    assert status == "HEALTHY"
    assert len(issues) == 0


def test_warning_kpis_produce_warning_score() -> None:
    score, status, issues, statuses = calculate_health_score({
        "rsrp": -98, "sinr": 8, "dl_throughput": 10, "prb_utilization": 80
    })
    assert score is not None and 50 <= score < 80
    assert status == "WARNING"


def test_empty_or_none_kpis_produce_unknown_score() -> None:
    score, status, issues, statuses = calculate_health_score({"rsrp": None, "sinr": None})
    assert score is None
    assert status == "UNKNOWN"

