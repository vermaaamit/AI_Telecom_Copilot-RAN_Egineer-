"""Pydantic models for 6G / IMT-2030 Research Lab & AI-Native RAN Digital Twin."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field


class SimulationParameter(BaseModel):
    tilt_offset_deg: float = Field(0.0, ge=-8.0, le=8.0, description="Antenna downtilt adjustment (+ down, - up in degrees)")
    tx_power_offset_dbm: float = Field(0.0, ge=-10.0, le=10.0, description="Transmit power offset in dBm")
    mimo_layers: int = Field(4, ge=1, le=128, description="Number of MIMO stream layers (e.g. 4 for 4G/5G, up to 64/128 for 6G Massive MIMO)")
    frequency_band_ghz: float = Field(3.5, ge=0.7, le=300.0, description="Carrier frequency (e.g. 3.5 GHz Mid-band, 28 GHz mmWave, 140 GHz Sub-THz)")
    carrier_bandwidth_mhz: float = Field(100.0, ge=10.0, le=4000.0, description="Aggregated carrier bandwidth in MHz")
    isac_sensing_resource_ratio: float = Field(0.0, ge=0.0, le=0.5, description="Fraction of OFDM resources dedicated to radar sensing vs communications (0.0 = pure comm, 0.2 = dual ISAC)")


class SimulationRequest(BaseModel):
    cell_id: str
    parameters: SimulationParameter
    notes: Optional[str] = "Digital twin what-if optimization simulation"


class ProjectedKpis(BaseModel):
    rsrp_dbm: float
    sinr_db: float
    dl_throughput_mbps: float
    ul_throughput_mbps: float
    prb_utilization_percent: float
    call_drop_rate_percent: float
    availability_percent: float


class ISACPerformance(BaseModel):
    isac_enabled: bool = False
    sensing_range_resolution_cm: float = 0.0
    sensing_velocity_accuracy_m_per_s: float = 0.0
    sensing_detection_probability: float = 0.0
    communication_throughput_gbps: float = 0.0
    sensing_resource_ratio: float = 0.0
    research_note: str = "6G IMT-2030 Integrated Sensing & Communication waveform resource sharing."


class SimulationResult(BaseModel):
    simulation_id: str = Field(default_factory=lambda: f"SIM-{uuid.uuid4().hex[:8].upper()}")
    target_cell_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    parameters: SimulationParameter
    baseline_kpis: Dict[str, float]
    baseline_health_score: float
    projected_kpis: ProjectedKpis
    projected_health_score: float
    delta_health_score: float
    isac_performance: Optional[ISACPerformance] = None
    projected_status: str
    recommendation: str
    risk_assessment: str
    is_synthetic: bool = True
    research_tier: str = "6G_IMT2030_AI_NATIVE"
    disclaimer: str = (
        "SYNTHETIC RESEARCH MODEL: Digital twin projections are deterministic mathematical "
        "simulations conforming to 3GPP TR 38.901 and IMT-2030 framework. "
        "Certified engineer validation is required before live network implementation."
    )


class DigitalTwinScenarioTemplate(BaseModel):
    id: str
    title: str
    description: str
    technology: str
    sample_cell_id: str
    recommended_parameters: SimulationParameter
    expected_outcome: str

