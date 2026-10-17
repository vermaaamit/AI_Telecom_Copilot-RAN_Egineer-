from app.analytics.kpi.thresholds import classify_kpi


def test_classify_higher_is_better_kpi() -> None:
    # RSRP: good >= -90, warning >= -105, critical < -105
    assert classify_kpi("rsrp", -85.0) == "HEALTHY"
    assert classify_kpi("rsrp", -90.0) == "HEALTHY"
    assert classify_kpi("rsrp", -95.0) == "WARNING"
    assert classify_kpi("rsrp", -105.0) == "WARNING"
    assert classify_kpi("rsrp", -115.0) == "CRITICAL"


def test_classify_lower_is_better_kpi() -> None:
    # PRB Utilization: good < 70, warning < 90, critical >= 90
    assert classify_kpi("prb_utilization", 50.0) == "HEALTHY"
    assert classify_kpi("prb_utilization", 69.9) == "HEALTHY"
    assert classify_kpi("prb_utilization", 75.0) == "WARNING"
    assert classify_kpi("prb_utilization", 89.9) == "WARNING"
    assert classify_kpi("prb_utilization", 90.0) == "CRITICAL"
    assert classify_kpi("prb_utilization", 98.0) == "CRITICAL"


def test_classify_unknown_kpi() -> None:
    assert classify_kpi("non_existent_kpi", 42.0) == "UNKNOWN"

