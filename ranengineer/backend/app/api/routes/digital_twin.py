"""Digital Twin & 6G / IMT-2030 Simulation API Routes."""
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.digital_twin.engine import BENCHMARK_SCENARIOS, DigitalTwinEngine
from app.digital_twin.models import (
    DigitalTwinScenarioTemplate,
    ISACPerformance,
    SimulationParameter,
    SimulationRequest,
    SimulationResult,
)
from app.security.auth import User, get_current_user

router = APIRouter(prefix="/digital-twin", tags=["6G & Digital Twin Studio"])


@router.get("/scenarios", response_model=List[DigitalTwinScenarioTemplate])
async def list_digital_twin_scenarios():
    """List benchmark what-if digital twin scenarios (e.g. Downtilt, Massive MIMO, 6G Sub-THz, ISAC)."""
    engine = DigitalTwinEngine()
    return engine.list_benchmark_scenarios()


@router.post("/simulate", response_model=SimulationResult)
async def simulate_cell_optimization(
    request: SimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run deterministic mathematical what-if simulation for candidate parameter adjustments."""
    engine = DigitalTwinEngine(db)
    return engine.simulate(request.cell_id, request.parameters)


@router.get("/isac/benchmark", response_model=List[ISACPerformance])
async def benchmark_isac_tradeoff(
    cell_id: str = "CELL_102_ISAC",
    frequency_band_ghz: float = 140.0,
    carrier_bandwidth_mhz: float = 1000.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generates an ISAC trade-off curve across varying sensing resource allocations (0% to 50%)."""
    engine = DigitalTwinEngine(db)
    ratios = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50]
    results: List[ISACPerformance] = []

    for r in ratios:
        sim_res = engine.simulate(
            cell_id=cell_id,
            params=SimulationParameter(
                tilt_offset_deg=0.0,
                tx_power_offset_dbm=0.0,
                mimo_layers=16,
                frequency_band_ghz=frequency_band_ghz,
                carrier_bandwidth_mhz=carrier_bandwidth_mhz,
                isac_sensing_resource_ratio=r,
            ),
        )
        if sim_res.isac_performance:
            results.append(sim_res.isac_performance)

    return results

