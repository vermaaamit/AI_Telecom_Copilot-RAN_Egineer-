from app.analytics.anomaly.rules import probable_causes


def test_coverage_and_interference_rule() -> None:
    causes = probable_causes({"rsrp": "CRITICAL", "sinr": "CRITICAL"})
    assert any("Coverage degradation" in c["probable_cause"] for c in causes)
    assert any("antenna, feeder, and radio alarms" in check for c in causes for check in c["recommended_checks"])


def test_congestion_and_capacity_rule() -> None:
    causes = probable_causes({"prb_utilization": "CRITICAL", "dl_throughput": "WARNING"})
    assert any("Congestion or capacity" in c["probable_cause"] for c in causes)
    assert any("PRB utilization" in check for c in causes for check in c["recommended_checks"])


def test_mobility_and_handover_rule() -> None:
    causes = probable_causes({"call_drop_rate": "WARNING", "handover_success_rate": "CRITICAL"})
    assert any("Mobility or handover" in c["probable_cause"] for c in causes)
    assert any("neighbor relations" in check for c in causes for check in c["recommended_checks"])


def test_cell_outage_rule() -> None:
    causes = probable_causes({"availability": "CRITICAL"})
    assert any("Cell outage" in c["probable_cause"] for c in causes)


def test_transport_degradation_rule() -> None:
    causes = probable_causes({"latency": "CRITICAL", "packet_loss": "WARNING"})
    assert any("Transport or backhaul" in c["probable_cause"] for c in causes)


def test_no_rules_match_for_healthy_kpis() -> None:
    causes = probable_causes({"rsrp": "HEALTHY", "sinr": "HEALTHY", "prb_utilization": "HEALTHY"})
    assert len(causes) == 0

