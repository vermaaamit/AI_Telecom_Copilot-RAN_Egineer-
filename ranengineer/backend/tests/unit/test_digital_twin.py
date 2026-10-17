"""Unit tests for 6G / IMT-2030 Research Lab & AI-Native Digital Twin (Section 48)."""
import pytest

from app.digital_twin.engine import DigitalTwinEngine
from app.digital_twin.models import SimulationParameter


def test_list_benchmark_scenarios():
    engine = DigitalTwinEngine()
    scenarios = engine.list_benchmark_scenarios()
    assert len(scenarios) >= 4
    techs = [s.technology for s in scenarios]
    assert "5G-NR" in techs
    assert "6G_IMT2030" in techs


def test_downtilt_simulation_improves_sinr():
    engine = DigitalTwinEngine()
    # Baseline with interference (low SINR)
    baseline = {
        "RSRP": -90.0,
        "SINR": 2.0,
        "DL_THROUGHPUT": 25.0,
        "UL_THROUGHPUT": 6.0,
        "PRB_UTILIZATION": 85.0,
        "CALL_DROP_RATE": 2.5,
        "AVAILABILITY": 99.0,
    }

    # Simulate +2.0 degrees electrical downtilt
    params = SimulationParameter(tilt_offset_deg=2.0)
    res = engine.simulate(cell_id="CELL_TEST_TILT", params=params, baseline_override=baseline)

    assert res.simulation_id.startswith("SIM-")
    assert res.target_cell_id == "CELL_TEST_TILT"
    # Positive tilt improves SINR
    assert res.projected_kpis.sinr_db > baseline["SINR"]
    # Throughput improves due to better SINR
    assert res.projected_kpis.dl_throughput_mbps > baseline["DL_THROUGHPUT"]
    assert res.is_synthetic is True
    assert res.research_tier == "6G_IMT2030_AI_NATIVE"


def test_6g_subthz_extreme_capacity():
    engine = DigitalTwinEngine()
    # 6G Sub-THz configuration: 140 GHz, 1000 MHz bandwidth, 16 MIMO layers
    params = SimulationParameter(
        tilt_offset_deg=0.0,
        tx_power_offset_dbm=4.0,
        mimo_layers=16,
        frequency_band_ghz=140.0,
        carrier_bandwidth_mhz=1000.0,
        isac_sensing_resource_ratio=0.0,
    )
    res = engine.simulate(cell_id="CELL_6G_MICRO", params=params)

    # Extreme Gbps throughput
    assert res.projected_kpis.dl_throughput_mbps > 500.0
    assert res.projected_health_score >= res.baseline_health_score


def test_6g_isac_dual_function_sensing_tradeoff():
    engine = DigitalTwinEngine()
    # 20% resource allocation to radar sensing
    params = SimulationParameter(
        frequency_band_ghz=140.0,
        carrier_bandwidth_mhz=1000.0,
        isac_sensing_resource_ratio=0.20,
    )
    res = engine.simulate(cell_id="CELL_6G_ISAC", params=params)

    assert res.isac_performance is not None
    assert res.isac_performance.isac_enabled is True
    assert res.isac_performance.sensing_resource_ratio == 0.20
    # Range resolution should be sub-meter (centimeter-level)
    assert 0.0 < res.isac_performance.sensing_range_resolution_cm < 100.0
    # Velocity accuracy in m/s
    assert res.isac_performance.sensing_velocity_accuracy_m_per_s > 0.0
    assert res.isac_performance.communication_throughput_gbps > 0.0


def test_uptilt_negative_angle_increases_interference_risk():
    engine = DigitalTwinEngine()
    # Negative tilt (uptilt) extends coverage beam too far, degrading SINR due to neighbor cell interference
    params = SimulationParameter(tilt_offset_deg=-3.0)
    res = engine.simulate(cell_id="CELL_UPTILT", params=params)
    assert res.projected_kpis.sinr_db < res.baseline_kpis["SINR"]
    assert "Not recommended" in res.recommendation or res.delta_health_score <= 0.0


def test_fallback_baseline_kpis():
    engine = DigitalTwinEngine(db=None)
    params = SimulationParameter(mimo_layers=4)
    res = engine.simulate(cell_id="CELL_UNKNOWN_FALLBACK", params=params)
    assert res.baseline_kpis["RSRP"] == -98.0
    assert res.baseline_kpis["SINR"] == 4.5
    assert res.target_cell_id == "CELL_UNKNOWN_FALLBACK"

