"""Unit tests for Operational Shift Handover report generator."""
from datetime import datetime, timezone
import pytest

from app.alarms.models import AlarmCreate, AlarmSeverity, AlarmStatus, AlarmType
from app.alarms.store import AlarmStore
from app.config.database import SessionLocal
from app.incidents.models import IncidentCreate, IncidentSeverity, IncidentStatus
from app.incidents.store import IncidentStore
from app.reports.generator import ShiftHandoverGenerator
from app.reports.models import NetworkOperationalStatus


def test_shift_handover_empty_db():
    with SessionLocal() as db:
        generator = ShiftHandoverGenerator(db)
        report = generator.generate()
        assert report is not None
        assert report.report_id.startswith("HND-")
        assert report.system_status == NetworkOperationalStatus.HEALTHY
        assert isinstance(report.handover_action_items, list)
        assert len(report.handover_action_items) > 0

        # Test Markdown export
        md = generator.format_markdown(report)
        assert "# NOC RAN Operational Shift Handover" in md
        assert report.report_id in md
        assert "Immediate Handover Action Checklist" in md


def test_shift_handover_with_alarms_and_incidents():
    with SessionLocal() as db:
        alarm_store = AlarmStore()
        incident_store = IncidentStore()

        # Create critical alarm
        alarm_store.create(
            AlarmCreate(
                site_id="SITE_TEST_99",
                cell_id="CELL_TEST_99A",
                technology="NR",
                alarm_type=AlarmType.CELL_UNAVAILABLE,
                severity=AlarmSeverity.CRITICAL,
                status=AlarmStatus.ACTIVE,
                description="Fiber cut on primary fronthaul link",
                source="eNB-Agent",
            )
        )

        # Create incident
        incident_store.create(
            IncidentCreate(
                title="Major Fiber Outage SITE_TEST_99",
                description="Front-haul degradation",
                severity=IncidentSeverity.CRITICAL,
                status=IncidentStatus.OPEN,
                affected_cells=["CELL_TEST_99A"],
                related_alarms=[],
            )
        )

        generator = ShiftHandoverGenerator(db)
        report = generator.generate()

        assert report.system_status == NetworkOperationalStatus.CRITICAL
        assert len(report.active_alarms) >= 1
        assert len(report.open_incidents) >= 1
        assert any("active alarm" in a.lower() for a in report.handover_action_items)

        md = generator.format_markdown(report)
        assert "Fiber cut on primary fronthaul link" in md
        assert "Major Fiber Outage SITE_TEST_99" in md
