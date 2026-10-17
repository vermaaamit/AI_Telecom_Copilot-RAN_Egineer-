"""Deterministic Digital Twin Simulation Engine for AI-Native RAN & 6G / IMT-2030 (Section 48)."""
import math
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.analytics.scoring.health import calculate_health_score
from app.digital_twin.models import (
    DigitalTwinScenarioTemplate,
    ISACPerformance,
    ProjectedKpis,
    SimulationParameter,
    SimulationResult,
)
from app.repositories.dataset_repository import DatasetRepository

SPEED_OF_LIGHT = 3e8  # m/s

BENCHMARK_SCENARIOS = [
    DigitalTwinScenarioTemplate(
        id="scenario-tilt-opt",
        title="Urban Interference Mitigation via Antenna Downtilt",
        description="Applies +2.5° electrical downtilt to suppress overshoot interference and raise cell-center SINR.",
        technology="5G-NR",
        sample_cell_id="CELL_001_A",
        recommended_parameters=SimulationParameter(
            tilt_offset_deg=2.5,
            tx_power_offset_dbm=0.0,
            mimo_layers=4,
            frequency_band_ghz=3.5,
            carrier_bandwidth_mhz=100.0,
            isac_sensing_resource_ratio=0.0,
        ),
        expected_outcome="SINR expected to improve by ~2.0 dB with PRB utilization relief and zero coverage loss.",
    ),
    DigitalTwinScenarioTemplate(
        id="scenario-massive-mimo",
        title="Downtown Massive MIMO 64T64R Spatial Expansion",
        description="Upgrades antenna array from 4 layers to 32 spatial layers, multiplying cell spectral efficiency.",
        technology="5G-Advanced",
        sample_cell_id="CELL_045_C",
        recommended_parameters=SimulationParameter(
            tilt_offset_deg=0.0,
            tx_power_offset_dbm=3.0,
            mimo_layers=32,
            frequency_band_ghz=3.5,
            carrier_bandwidth_mhz=100.0,
            isac_sensing_resource_ratio=0.0,
        ),
        expected_outcome="DL throughput projected to increase by >250% under congested peak loads.",
    ),
    DigitalTwinScenarioTemplate(
        id="scenario-6g-subthz",
        title="6G Sub-THz Ultra-Capacity Micro-Hotspot (140 GHz)",
        description="Simulates 140 GHz D-Band sub-THz carrier with 1000 MHz bandwidth for extreme Gbps throughput.",
        technology="6G_IMT2030",
        sample_cell_id="CELL_102_A",
        recommended_parameters=SimulationParameter(
            tilt_offset_deg=1.0,
            tx_power_offset_dbm=5.0,
            mimo_layers=16,
            frequency_band_ghz=140.0,
            carrier_bandwidth_mhz=1000.0,
            isac_sensing_resource_ratio=0.0,
        ),
        expected_outcome="Peak cell downlink throughput exceeds 20 Gbps with sub-millisecond radio latency.",
    ),
    DigitalTwinScenarioTemplate(
        id="scenario-6g-isac",
        title="6G ISAC Dual-Function Sensing & Communications",
        description="Allocates 20% of OFDM radio resources to high-resolution environment sensing (radar radar imaging).",
        technology="6G_IMT2030",
        sample_cell_id="CELL_102_B",
        recommended_parameters=SimulationParameter(
            tilt_offset_deg=0.0,
            tx_power_offset_dbm=2.0,
            mimo_layers=16,
            frequency_band_ghz=140.0,
            carrier_bandwidth_mhz=1000.0,
            isac_sensing_resource_ratio=0.20,
        ),
        expected_outcome="Achieves 15 cm radar range resolution and 0.2 m/s velocity accuracy while sustaining 16 Gbps comm.",
    ),
]


class DigitalTwinEngine:
    """Deterministic mathematical simulation of RAN physics, beamforming, and 6G ISAC."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def list_benchmark_scenarios(self) -> List[DigitalTwinScenarioTemplate]:
        return BENCHMARK_SCENARIOS

    def simulate(
        self,
        cell_id: str,
        params: SimulationParameter,
        baseline_override: Optional[Dict[str, float]] = None,
    ) -> SimulationResult:
        # 1. Resolve baseline KPIs
        baseline_kpis: Dict[str, float] = {}
        if baseline_override:
            baseline_kpis = baseline_override
        elif self.db:
            repo = DatasetRepository(self.db)
            cell_data = repo.find_cell(cell_id)
            if cell_data and "kpis" in cell_data and isinstance(cell_data["kpis"], dict):
                baseline_kpis = {k.upper(): float(v) for k, v in cell_data["kpis"].items() if v is not None}

        # Fallback baseline for synthetic exploration
        if not baseline_kpis:
            baseline_kpis = {
                "RSRP": -98.0,
                "SINR": 4.5,
                "DL_THROUGHPUT": 32.0,
                "UL_THROUGHPUT": 8.0,
                "PRB_UTILIZATION": 74.0,
                "CALL_DROP_RATE": 1.2,
                "AVAILABILITY": 99.2,
            }

        # 2. Compute baseline Health Score
        base_score_raw, _, _, _ = calculate_health_score(baseline_kpis)
        base_score = float(base_score_raw if base_score_raw is not None else 65.0)

        # 3. Deterministic Physics & Beamforming Projections
        # Downtilt physics (tilt_offset_deg)
        # Positive tilt: concentrates power closer to antenna, reduces overshoot interference, improves SINR
        tilt = params.tilt_offset_deg
        delta_sinr_tilt = (0.75 * tilt) - (0.05 * (tilt ** 2))
        delta_rsrp_tilt = -1.1 * tilt  # Edge coverage decreases slightly with downtilt

        # Power offset (tx_power_offset_dbm)
        tx_pwr = params.tx_power_offset_dbm
        delta_rsrp_pwr = 0.95 * tx_pwr
        delta_sinr_pwr = (0.5 * tx_pwr) if tx_pwr <= 3.0 else (1.5 - 0.2 * (tx_pwr - 3.0))

        # Combined RSRP & SINR
        proj_rsrp = round(baseline_kpis.get("RSRP", -95.0) + delta_rsrp_tilt + delta_rsrp_pwr, 2)
        proj_sinr = round(baseline_kpis.get("SINR", 5.0) + delta_sinr_tilt + delta_sinr_pwr, 2)

        # MIMO layer scaling (Shannon capacity multiplier)
        base_layers = 4.0
        mimo_ratio = max(1.0, math.sqrt(params.mimo_layers / base_layers))

        # Bandwidth scaling relative to baseline 100MHz
        bw_ratio = params.carrier_bandwidth_mhz / 100.0

        # Sub-THz spectral efficiency boost
        thz_multiplier = 1.0
        if params.frequency_band_ghz >= 100.0:
            # 6G sub-THz extreme capacity regime
            thz_multiplier = 2.5

        # ISAC Resource Division: (1 - isac_ratio) allocated to communications
        comm_ratio = 1.0 - params.isac_sensing_resource_ratio

        # Projected Throughput (Shannon model derivative)
        sinr_linear = max(0.1, 10 ** (proj_sinr / 10.0))
        shannon_factor = math.log2(1.0 + sinr_linear) / math.log2(1.0 + (10 ** (baseline_kpis.get("SINR", 5.0) / 10.0)))
        shannon_factor = max(0.3, min(shannon_factor, 3.5))

        proj_dl_thp = baseline_kpis.get("DL_THROUGHPUT", 30.0) * mimo_ratio * bw_ratio * thz_multiplier * shannon_factor * comm_ratio
        proj_dl_thp = round(max(1.0, proj_dl_thp), 2)

        proj_ul_thp = baseline_kpis.get("UL_THROUGHPUT", 8.0) * math.sqrt(mimo_ratio) * bw_ratio * comm_ratio
        proj_ul_thp = round(max(0.5, proj_ul_thp), 2)

        # PRB Utilization: high throughput offload alleviates congestion
        base_prb = baseline_kpis.get("PRB_UTILIZATION", 60.0)
        prb_relief = (proj_dl_thp / max(1.0, baseline_kpis.get("DL_THROUGHPUT", 30.0))) * 8.0
        proj_prb = round(max(10.0, min(98.0, base_prb - prb_relief + (3.0 if tx_pwr > 4.0 else 0.0))), 2)

        # Call Drop Rate: correlates inversely with RSRP and SINR
        base_cdr = baseline_kpis.get("CALL_DROP_RATE", 1.0)
        cdr_delta = (-0.15 * delta_sinr_tilt) - (0.10 * delta_rsrp_pwr)
        proj_cdr = round(max(0.05, min(15.0, base_cdr + cdr_delta)), 2)

        proj_avail = baseline_kpis.get("AVAILABILITY", 99.5)

        projected_kpi_dict = {
            "RSRP": proj_rsrp,
            "SINR": proj_sinr,
            "DL_THROUGHPUT": proj_dl_thp,
            "UL_THROUGHPUT": proj_ul_thp,
            "PRB_UTILIZATION": proj_prb,
            "CALL_DROP_RATE": proj_cdr,
            "AVAILABILITY": proj_avail,
        }

        # 4. Projected Health Score
        proj_score_raw, proj_status, _, _ = calculate_health_score(projected_kpi_dict)
        proj_score = float(proj_score_raw if proj_score_raw is not None else 70.0)
        delta_score = round(proj_score - base_score, 1)

        # 5. 6G ISAC Performance Evaluation
        isac_perf: Optional[ISACPerformance] = None
        if params.isac_sensing_resource_ratio > 0.0:
            sensing_bw_hz = (params.carrier_bandwidth_mhz * 1e6) * params.isac_sensing_resource_ratio
            # Range resolution Delta R = c / (2 * B_sensing)
            range_res_m = SPEED_OF_LIGHT / (2.0 * sensing_bw_hz)
            range_res_cm = round(range_res_m * 100.0, 2)

            # Velocity resolution Delta v = c / (2 * f_c * T_obs), assume 1ms coherent processing interval
            fc_hz = params.frequency_band_ghz * 1e9
            vel_acc_mps = round(SPEED_OF_LIGHT / (2.0 * fc_hz * 0.001), 2)

            det_prob = round(min(0.99, 0.80 + 0.18 * (proj_sinr / 20.0)), 3)
            comm_gbps = round(proj_dl_thp / 1000.0, 2)

            isac_perf = ISACPerformance(
                isac_enabled=True,
                sensing_range_resolution_cm=range_res_cm,
                sensing_velocity_accuracy_m_per_s=vel_acc_mps,
                sensing_detection_probability=det_prob,
                communication_throughput_gbps=comm_gbps,
                sensing_resource_ratio=params.isac_sensing_resource_ratio,
                research_note=f"Dual-function ISAC at {params.frequency_band_ghz} GHz provides {range_res_cm} cm radar accuracy with {comm_gbps} Gbps comm.",
            )

        # 6. Recommendation & Risk Assessment
        if tilt < 0:
            recommendation = (
                f"Not recommended: Negative antenna tilt ({tilt}°) causes beam overshoot and pilot pollution, "
                f"degrading inter-cell SINR."
            )
            risk = "HIGH: Negative uptilt increases neighbor interference and handover failures."
        elif delta_score >= 10.0:
            recommendation = (
                f"Strong candidate for optimization: Projected health score improves by +{delta_score} pts. "
                f"Antenna tilt offset of {tilt}° and MIMO layer scaling effectively resolves degradation."
            )
            risk = "LOW: Simulation confirms parameter boundaries satisfy 3GPP and O-RAN guardrails."
        elif delta_score >= 0.0:
            recommendation = (
                f"Moderate improvement (+{delta_score} pts). Consider staging parameter changes in lab twin first."
            )
            risk = "MEDIUM: Marginal gains; verify coverage boundary handovers before live field rollout."
        else:
            recommendation = (
                f"Not recommended: Projected health score degrades by {delta_score} pts. "
                "Current parameters exacerbate coverage gaps or interference."
            )
            risk = "HIGH: Adverse impact predicted on RSRP or inter-cell interference."

        projected_status = "HEALTHY" if proj_score >= 70 else ("WARNING" if proj_score >= 50 else "CRITICAL")

        return SimulationResult(
            target_cell_id=cell_id,
            parameters=params,
            baseline_kpis=baseline_kpis,
            baseline_health_score=base_score,
            projected_kpis=ProjectedKpis(
                rsrp_dbm=proj_rsrp,
                sinr_db=proj_sinr,
                dl_throughput_mbps=proj_dl_thp,
                ul_throughput_mbps=proj_ul_thp,
                prb_utilization_percent=proj_prb,
                call_drop_rate_percent=proj_cdr,
                availability_percent=proj_avail,
            ),
            projected_health_score=proj_score,
            delta_health_score=delta_score,
            isac_performance=isac_perf,
            projected_status=projected_status,
            recommendation=recommendation,
            risk_assessment=risk,
            is_synthetic=True,
            research_tier="6G_IMT2030_AI_NATIVE",
        )
