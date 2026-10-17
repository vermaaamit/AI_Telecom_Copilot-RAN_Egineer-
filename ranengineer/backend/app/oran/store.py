"""In-memory and persistent store for generated O-RAN rApp descriptors."""
from datetime import datetime, timezone
from typing import Dict, List, Optional
import threading

from app.oran.generator import RAppStudio
from app.oran.models import (
    ApprovalRequest,
    PolicyType,
    RAppDescriptor,
    RAppGenerationRequest,
    ReviewStatus,
)


class RAppStore:
    """Thread-safe store for O-RAN rApp descriptors."""

    def __init__(self):
        self._lock = threading.Lock()
        self._rapps: Dict[str, RAppDescriptor] = {}
        self.studio = RAppStudio()
        self._seed_default_rapps()

    def _seed_default_rapps(self):
        """Pre-seeds standard rApps demonstrating Traffic Steering, Energy Saving, and QoE Assurance."""
        demo_reqs = [
            RAppGenerationRequest(
                rapp_name="Macro-to-SmallCell Dynamic Traffic Steerer",
                policy_type=PolicyType.TRAFFIC_STEERING,
                target_cells=["CELL_001_A", "CELL_001_B"],
                target_site_id="SITE_001",
                objective="Offload PRB congestion from macro sector to micro cell when utilization exceeds 82%",
                parameters={
                    "prb_threshold_percent": 82.0,
                    "rsrp_offset_db": -4.0,
                    "hysteresis_db": 2.5,
                    "time_to_trigger_ms": 320,
                },
                notes="Tested on digital twin simulation.",
            ),
            RAppGenerationRequest(
                rapp_name="GreenRAN Dynamic Carrier Sleep Orchestrator",
                policy_type=PolicyType.ENERGY_SAVING,
                target_cells=["CELL_045_C"],
                target_site_id="SITE_045",
                objective="Automate off-peak mid-band carrier sleep between 01:00 and 05:00 UTC",
                parameters={
                    "offpeak_prb_threshold": 12.0,
                    "reactivation_prb_threshold": 50.0,
                    "coverage_underlay_cell_id": "CELL_045_A",
                    "sleep_depth": "carrier_shutdown",
                },
                notes="Coverage continuity verified with low-band 700MHz anchor.",
            ),
            RAppGenerationRequest(
                rapp_name="URLLC Low-Latency Slice SLA Protector",
                policy_type=PolicyType.QOE_ASSURANCE,
                target_cells=["CELL_102_A", "CELL_102_B"],
                target_site_id="SITE_102",
                objective="Guarantee 5QI-1 mission critical packet delay budget under 15ms",
                parameters={
                    "slice_id": "SST-1_SD-URLLC01",
                    "min_throughput_dl_mbps": 75.0,
                    "max_packet_delay_budget_ms": 15.0,
                    "priority_level": 1,
                },
                notes="Automated scheduler priority elevation via A1-P.",
            ),
        ]
        for req in demo_reqs:
            rapp = self.studio.generate_rapp(req)
            self._rapps[rapp.id] = rapp

    def list_all(self, policy_type: Optional[PolicyType] = None) -> List[RAppDescriptor]:
        """Lists all stored rApps, optionally filtered by policy type."""
        with self._lock:
            items = list(self._rapps.values())
        if policy_type:
            items = [r for r in items if r.policy_type == policy_type]
        return sorted(items, key=lambda x: x.created_at, reverse=True)

    def get_by_id(self, rapp_id: str) -> Optional[RAppDescriptor]:
        """Retrieves a single rApp by its unique ID."""
        with self._lock:
            return self._rapps.get(rapp_id)

    def save(self, rapp: RAppDescriptor) -> RAppDescriptor:
        """Stores or updates an rApp descriptor."""
        with self._lock:
            rapp.updated_at = datetime.now(timezone.utc).isoformat()
            self._rapps[rapp.id] = rapp
            return rapp

    def approve(self, rapp_id: str, engineer_email: str, approval_req: ApprovalRequest) -> Optional[RAppDescriptor]:
        """Records formal engineer sign-off and transitions review status."""
        with self._lock:
            rapp = self._rapps.get(rapp_id)
            if not rapp:
                return None

            rapp.review_status = ReviewStatus.ENGINEER_APPROVED
            rapp.approved_by = engineer_email
            rapp.approved_at = datetime.now(timezone.utc).isoformat()
            if approval_req.notes:
                prev = rapp.engineer_notes or ""
                rapp.engineer_notes = f"{prev}\n[Approved by {engineer_email}]: {approval_req.notes}".strip()
            rapp.updated_at = datetime.now(timezone.utc).isoformat()
            self._rapps[rapp_id] = rapp
            return rapp


# Singleton instance
_store_instance: Optional[RAppStore] = None


def get_rapp_store() -> RAppStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = RAppStore()
    return _store_instance

